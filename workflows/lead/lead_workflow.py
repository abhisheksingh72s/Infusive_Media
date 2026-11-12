"""
Lead Workflow Module
====================
Encapsulates Pre-Sales lead creation and BDM qualification (conversion to 'Won').
Implements the CRM Lead Assignment Engine:
  1. Country-based Mapping: checks /api/Country/{id}/assigned-members for active status.
  2. Source-based Mapping Fallback: checks /api/Source/{id}/assigned-members for active status.
  3. Lead Pool Self-Assign Fallback: if no active member is mapped, designated BDM self-assigns from /lead-pool.
Resolves credentials dynamically via /api/User.
"""

import os
import time
import urllib.parse
import logging
from faker import Faker
from playwright.sync_api import Page, expect

from pages.login_page import LoginPage
from pages.company_page import CompanyPage
from pages.lead_page import LeadPoolPage, CreatedLeadPage, MyLeadsPage, DynamicTable

logger = logging.getLogger(__name__)


class LeadWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.login_page = LoginPage(page)
        self.company_page = CompanyPage(page)
        self.lead_pool_page = LeadPoolPage(page)
        self.created_lead_page = CreatedLeadPage(page)
        self.my_leads_page = MyLeadsPage(page)

    def resolve_lead_allocation(self, country: str = "United States", source: str = None) -> dict:
        """
        Evaluate backend lead allocation engine rules:
          Rule 1: Map Country -> check /api/Country/{id}/assigned-members (status == True)
          Rule 2: Fallback to Source -> check /api/Source/{id}/assigned-members (status == True)
          Rule 3: If neither has active member, routes to Lead Pool (/lead-pool)
        """
        logger.info(f"Resolving lead allocation engine rules for country='{country}', source='{source}'...")
        # 1. Country mapping check
        try:
            country_url = f"https://infusive-back.jobvritta.com/api/Country?skip=0&limit=10&text={urllib.parse.quote(country)}"
            res = self.page.request.get(country_url)
            if res.status == 200:
                data = res.json()
                countries = data.get("countries", [])
                if countries:
                    cid = countries[0].get("id")
                    mem_res = self.page.request.get(f"https://infusive-back.jobvritta.com/api/Country/{cid}/assigned-members")
                    if mem_res.status == 200:
                        mem_data = mem_res.json()
                        active = [m for m in mem_data.get("assignedMembers", []) if m.get("status") is True]
                        if active:
                            chosen = active[0]
                            logger.info(f"Allocation Engine: Matched Country rule -> {chosen.get('name')} ({chosen.get('email')})")
                            return {"name": chosen.get("name"), "email": chosen.get("email"), "rule": "country"}
        except Exception as e:
            logger.warning(f"Allocation Engine Country check warning: {e}")

        # 2. Source mapping check
        if source:
            try:
                src_url = f"https://infusive-back.jobvritta.com/api/Source?skip=0&limit=10&search={urllib.parse.quote(source)}"
                res = self.page.request.get(src_url)
                if res.status == 200:
                    data = res.json()
                    sources = data.get("source", [])
                    if sources:
                        sid = sources[0].get("id")
                        mem_res = self.page.request.get(f"https://infusive-back.jobvritta.com/api/Source/{sid}/assigned-members")
                        if mem_res.status == 200:
                            mem_data = mem_res.json()
                            active = [m for m in mem_data.get("assignedMembers", []) if m.get("status") is True]
                            if active:
                                chosen = active[0]
                                logger.info(f"Allocation Engine: Matched Source rule -> {chosen.get('name')} ({chosen.get('email')})")
                                return {"name": chosen.get("name"), "email": chosen.get("email"), "rule": "source"}
            except Exception as e:
                logger.warning(f"Allocation Engine Source check warning: {e}")

        logger.info("Allocation Engine: No active member mapped in Country or Source. Lead routes to Lead Pool (/lead-pool).")
        return {"name": None, "email": None, "rule": "lead_pool"}

    def get_user_credentials(self, search_query: str = None) -> tuple[str, str]:
        """Fetch user email and password dynamically from environment variables or /api/User."""
        search_clean = (search_query or "").strip()
        logger.info(f"Querying credentials for '{search_clean}'...")

        # 1. Search .env USER_* configuration
        for i in range(1, 35):
            for fmt in (f"{i:02d}", str(i)):
                env_name = os.getenv(f"USER_{fmt}_FULL_NAME", "")
                env_email = os.getenv(f"USER_{fmt}_EMAIL", "")
                env_role = os.getenv(f"USER_{fmt}_ROLE", "")
                matches = (search_clean.lower() in env_name.lower() or search_clean.lower() in env_email.lower()) if search_clean else ("bdm" in env_role.lower())
                if matches and env_email:
                    password = os.getenv(f"USER_{fmt}_PASSWORD")
                    if password:
                        return env_email, password

        # 2. Query /api/User dynamically
        try:
            url = f"https://infusive-back.jobvritta.com/api/User?skip=0&limit=50&search={urllib.parse.quote(search_clean)}"
            res = self.page.request.get(url)
            if res.status == 200:
                body = res.json()
                users = body.get("users", [])
                if users:
                    for u in users:
                        name = u.get("name", "")
                        email = u.get("email", "")
                        pwd = u.get("password")
                        if (search_clean.lower() in name.lower() or search_clean.lower() in email.lower()) and pwd:
                            return email, pwd
                    for u in users:
                        roles = [r.get("name") for r in u.get("roles", [])]
                        if "BDM" in roles and u.get("password"):
                            return u.get("email"), u.get("password")
        except Exception as e:
            logger.warning(f"Error querying /api/User: {e}")

        # Fallback to configured Admin credentials from environment
        admin_email = os.getenv("EMAIL")
        admin_pass = os.getenv("PASSWORD")
        if admin_email and admin_pass:
            return admin_email, admin_pass

        raise ValueError(f"No credentials configured in environment or /api/User for '{search_clean}'.")

    def create_quick_lead(
        self,
        company_name: str = None,
        country: str = "United States",
        country_code: str = "+1",
    ) -> dict:
        """Log in as Pre-Sales, add a Quick Lead, and resolve assigned BDM via allocation engine."""
        fk = Faker("en_US")
        first_name = fk.first_name()
        last_name = fk.last_name()
        if not company_name:
            company_base = fk.company().replace("'", "").replace(",", "").replace("-", " ")
            suffix = fk.company_suffix()
            company_name = f"{company_base} {suffix}"

        domain = "".join(filter(str.isalnum, company_name.split()[0])).lower() or "enterprise"
        email = f"{first_name.lower()}.{last_name.lower()}@{domain}.com"
        phone = fk.numerify("98########")

        presales_email = os.getenv("USER_11_EMAIL") or os.getenv("EMAIL")
        presales_pass = os.getenv("USER_11_PASSWORD") or os.getenv("PASSWORD")
        if not presales_email or not presales_pass:
            raise ValueError("Pre-Sales credentials (USER_11_EMAIL / USER_11_PASSWORD or EMAIL / PASSWORD) not set in environment.")

        logger.info(f"Creating Quick Lead for '{company_name}' as Pre-Sales ({presales_email})...")
        self.login_page.load()
        self.login_page.login(presales_email, presales_pass)
        self.login_page.wait_for_dashboard()

        self.company_page.go_to_company()
        self.company_page.click_add_quick_lead()

        self.company_page.fill_quick_lead_form(
            name=company_name,
            email=email,
            phone=phone,
            country=country,
            country_code=country_code,
        )
        self.company_page.click_save_quick_lead()
        self.page.wait_for_timeout(2000)

        # Check Created Lead table to see if allocation assigned anyone
        assigned_to = None
        lead_id = None
        try:
            self.created_lead_page.go_to_created_lead()
            self.page.reload()
            self.page.wait_for_timeout(1000)
            lead_id, assigned_to = self.created_lead_page.find_lead_and_capture_assigned_bdm(phone, company_name=company_name)
        except Exception as e:
            logger.warning(f"Created Lead capture warning: {e}")

        if not assigned_to:
            # Query backend allocation rule engine to verify assignment status
            alloc = self.resolve_lead_allocation(country=country)
            assigned_to = alloc.get("name")

        logger.info(f"Lead Created: company='{company_name}', assigned_to='{assigned_to or 'Unassigned (Lead Pool)'}'")
        return {
            "company_name": company_name,
            "email": email,
            "phone": phone,
            "assigned_to": assigned_to,
            "lead_id": lead_id,
        }

    def mark_lead_won(self, company_name: str, assigned_to: str = None) -> str:
        """
        Convert lead status to 'Won'.
        If unassigned:
          1. Admin logs in and reassigns lead via Action Icon #4 (👤⇋👤) in Lead Pool (/lead-pool) to BDM 1.
          2. Assigned BDM (BDM 1) logs in, navigates to /my-leads, accepts the lead, and updates status to 'Won'.
        If assigned:
          1. Assigned BDM logs in directly, accepts lead in /my-leads, and updates status to 'Won'.
        """
        if not assigned_to:
            # Step A: Admin reassigns via Lead Pool Action Icon #4 (👤⇋👤)
            admin_email = os.getenv("EMAIL")
            admin_pass = os.getenv("PASSWORD")
            if not admin_email or not admin_pass:
                raise ValueError("Admin credentials (EMAIL and PASSWORD) must be defined in environment.")
            logger.info(f"Lead is unassigned. Logging in as Admin ({admin_email}) to reassign via Lead Pool...")
            self.login_page.logout()
            self.login_page.login(admin_email, admin_pass)
            self.login_page.wait_for_dashboard()

            target_bdm = "BDM 1"
            self.lead_pool_page.reassign_lead(company_name, bdm_name=target_bdm)
            assigned_to = target_bdm

        # Step B: Log in as the assigned BDM
        bdm_email, bdm_pass = self.get_user_credentials(assigned_to)
        logger.info(f"Logging in as assigned BDM '{assigned_to}' ({bdm_email})...")
        self.login_page.logout()
        self.login_page.login(bdm_email, bdm_pass)
        self.login_page.wait_for_dashboard()

        # Step C: Navigate to My Leads and accept/convert to Won
        logger.info(f"Navigating to My Leads to convert '{company_name}' to Won...")
        self.my_leads_page.go_to_my_leads()
        table = DynamicTable(self.page)
        row = table.find_row(column="COMPANY", value=company_name, match_partial=True)
        self.my_leads_page.accept_lead_if_assigned(row)
        self.page.wait_for_timeout(1000)

        # Update status to Won
        row = table.find_row(column="COMPANY", value=company_name, match_partial=True)
        status_cell = row.get_cell("LEAD STATUS")
        status_cell.scroll_into_view_if_needed()
        try:
            status_cell.click(timeout=5000)
        except Exception:
            status_cell.click(force=True)

        status_modal = self.page.locator("section[aria-modal='true'], [role='dialog'], .chakra-modal__content").filter(
            has_text="Update Status"
        ).first
        if not status_modal.is_visible():
            status_modal = self.page.locator("section[aria-modal='true'], [role='dialog'], .chakra-modal__content").first
        status_modal.wait_for(state="visible", timeout=10000)
        status_modal.locator("select").first.select_option(label="Won")

        desc_field = status_modal.locator("textarea")
        if desc_field.is_visible():
            desc_field.fill("Lead converted to Won via LeadWorkflow.")

        update_btn = status_modal.locator("button:has-text('Update')").first
        update_btn.click()
        logger.info("Clicked 'Update' button in Update Status modal.")

        # 1. Wait for spinner to complete
        logger.info("Waiting for status conversion spinner to finish...")
        try:
            spinner = self.page.locator(".chakra-spinner, [data-loading], .spinner, button[data-loading]").first
            if spinner.is_visible(timeout=2000):
                spinner.wait_for(state="hidden", timeout=25000)
                logger.info("Spinner finished.")
        except Exception:
            pass

        # 2. Wait for toast notification
        logger.info("Waiting for status update toast...")
        try:
            toast = self.page.locator(".chakra-toast, [role='status'], [role='alert']").first
            if toast.is_visible(timeout=5000):
                toast_msg = toast.inner_text().strip()
                logger.info(f"Captured status update toast: '{toast_msg}'")
                try:
                    toast.wait_for(state="hidden", timeout=8000)
                except Exception:
                    pass
        except Exception:
            pass

        # 3. Wait for modal to close
        try:
            status_modal.wait_for(state="hidden", timeout=15000)
            logger.info("Update Status modal closed successfully.")
        except Exception:
            close_btn = status_modal.locator("button[aria-label*='Close'], button.chakra-modal__close-btn").first
            if close_btn.count() > 0 and close_btn.is_visible():
                close_btn.click()
                status_modal.wait_for(state="hidden", timeout=5000)

        self.page.wait_for_timeout(1000)

        # 4. Search and verify current status from the table
        logger.info(f"Searching and verifying current status in table for '{company_name}'...")
        search_box = self.page.locator("input[placeholder*='Search'], input[type='search']").first
        if search_box.count() > 0 and search_box.is_visible():
            search_box.fill(company_name)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(1500)

        table = DynamicTable(self.page)
        row = table.find_row(column="COMPANY", value=company_name, match_partial=True)
        current_status = row.get_value("LEAD STATUS").strip()
        logger.info(f"Verified Lead Status in My Leads table: '{current_status}'")
        assert "won" in current_status.lower(), f"Expected Lead Status 'Won' in table, got '{current_status}'"
        return "Won"
