"""
Lead Management — Lost Status Flow
====================================
Module  : Lead Management
Test ID : test_lead_lost_status_flow

Flow (17 steps):
  1.  Navigate to login page
  2.  Login as Admin
  3.  Open Company Person page
  4.  Click Add New Company
  5.  Select Add Quick Lead from dropdown
  6.  Create Lead (company name, contact person, mobile, email) and Save
  7.  Open Lead module
  8.  Open Lead Pool
  9.  Search the created lead and capture the Assigned-To BDM name
  10. Logout Admin
  11. Login as the assigned BDM
  12. Open My Lead
  13. Click the Lead Status cell of the lead record
  14. Open Status dropdown
  15. Select "Lost"
  16. Enter description and click Update
  17. Verify the status column now shows "Lost"
"""

import os
import logging
from faker import Faker

from playwright.sync_api import expect

from pages.login_page import LoginPage
from pages.company_page import CompanyPage
from pages.lead_page import LeadPoolPage, MyLeadsPage, DynamicTable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _generate_lead_data() -> dict:
    """Return a fresh dict of lead fields using Faker (US locale)."""
    fk = Faker("en_US")
    company_name = f"LostCo {fk.unique.company()}"
    for ch in ("(", ")", "[", "]", "'", ","):
        company_name = company_name.replace(ch, "")
    phone = fk.numerify("##########")
    contact_person = fk.name().replace("'", "").replace(",", "")
    email = f"{company_name.replace(' ', '').lower()}@mailinator.com"
    return {
        "company_name": company_name,
        "contact_person": contact_person,
        "phone": phone,
        "email": email,
    }


def _map_assigned_to_credentials(assigned_to_name: str):
    """
    Resolve the full-name displayed in the Assigned-To column to (email, password)
    from .env USER_XX_* variables.  Falls back to a mailinator address if no
    mapping is found.
    """
    name_clean = assigned_to_name.strip().lower()
    for i in range(1, 30):
        for fmt in (f"{i:02d}", str(i)):
            env_name = os.getenv(f"USER_{fmt}_FULL_NAME", "")
            if env_name.strip().lower() == name_clean:
                email    = os.getenv(f"USER_{fmt}_EMAIL", "")
                password = os.getenv(f"USER_{fmt}_PASSWORD", "123456") or "123456"
                if email:
                    return email, password

    email_fallback = name_clean.replace(" ", "") + "@mailinator.com"
    logger.warning(
        "No .env mapping found for '%s'; using fallback '%s'",
        assigned_to_name,
        email_fallback,
    )
    return email_fallback, "123456"


def _logout(page) -> None:
    """Clear all client-side state and navigate to /login."""
    logger.info("Logging out — clearing storage and navigating to /login")
    try:
        page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        page.context.clear_cookies()
    except Exception as exc:
        logger.warning("Storage clear warning: %s", exc)

    from urllib.parse import urlparse
    parsed = urlparse(page.url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    page.goto(f"{base_url}/login", wait_until="domcontentloaded")
    page.wait_for_url("**/login", timeout=15_000)
    page.reload()
    page.wait_for_url("**/login", timeout=15_000)
    page.get_by_role("textbox", name="Email").wait_for(state="visible", timeout=10_000)
    logger.info("Logout complete — on clean login page")


def _login_with_retry(login_page: LoginPage, email: str, password: str) -> None:
    """
    Try the primary password; on failure try common fallback passwords before
    raising AssertionError.
    """
    logger.info("Attempting login as '%s'", email)
    login_page.login(email, password)
    try:
        login_page.wait_for_dashboard()
        logger.info("Login succeeded for '%s'", email)
        return
    except Exception:
        logger.warning("Primary password failed for '%s'", email)

    for fallback in ("123456", "1234567", "123456789"):
        if fallback == password:
            continue
        logger.info("Retrying '%s' with fallback password '%s'", email, fallback)
        login_page.load()
        login_page.login(email, fallback)
        try:
            login_page.wait_for_dashboard()
            logger.info("Login succeeded with fallback '%s'", fallback)
            return
        except Exception:
            logger.warning("Fallback '%s' also failed", fallback)

    raise AssertionError(
        f"Unable to log in as '{email}' with any known credential."
    )


# ---------------------------------------------------------------------------
# Step helpers
# ---------------------------------------------------------------------------

def _update_lead_status_to_lost(page, lead_id: str) -> None:
    """
    Steps 13-16:
      13. Find the row by LEAD ID and click the LEAD STATUS cell to open the modal
      14. Select 'Lost' from the status <select> inside the modal
      15. Fill the description textarea
      16. Click Update and wait for the modal to close
    """
    # Step 13 — open Update Status modal
    logger.info("Step 13: Opening Update Status modal for Lead ID '%s'", lead_id)
    table = DynamicTable(page)
    row = table.find_row(column="LEAD ID", value=str(lead_id))
    logger.info("Row found: %s", row.get_all_values())

    status_cell = row.get_cell("LEAD STATUS")
    try:
        status_cell.click(timeout=5_000)
    except Exception:
        status_cell.locator("div").first.click(timeout=5_000)

    update_status_modal = page.locator("section[aria-modal='true']")
    update_status_modal.wait_for(state="visible", timeout=10_000)
    logger.info("Update Status modal is open")

    # Step 14 — select 'Lost'
    logger.info("Step 14: Selecting 'Lost'")
    status_select = page.locator("section[aria-modal='true'] select")
    status_select.select_option(label="Lost")
    logger.info("'Lost' selected")

    # Step 15 — enter description
    logger.info("Step 15: Entering description")
    description_text = "Lead marked as Lost during automated test run."
    description_field = update_status_modal.locator("textarea")
    description_field.wait_for(state="visible", timeout=5_000)
    description_field.fill(description_text)
    logger.info("Description filled")

    # Step 16 — click Update
    logger.info("Step 16: Clicking Update")
    update_btn = update_status_modal.get_by_role("button", name="Update")
    expect(update_btn).to_be_enabled(timeout=5_000)
    update_btn.click()

    update_status_modal.wait_for(state="hidden", timeout=10_000)
    logger.info("Modal closed — status update submitted")
    page.wait_for_timeout(1_500)


def _verify_lead_status(page, lead_id: str, expected_status: str) -> None:
    """
    Step 17: Re-query the My Leads table and assert LEAD STATUS == expected_status.
    """
    table = DynamicTable(page)
    row = table.find_row(column="LEAD ID", value=str(lead_id))
    actual_status = row.get_value("LEAD STATUS")

    logger.info(
        "Verification — Lead ID: '%s' | Expected: '%s' | Actual: '%s'",
        lead_id,
        expected_status,
        actual_status,
    )
    assert actual_status == expected_status, (
        f"Lead status mismatch for Lead ID '{lead_id}': "
        f"expected '{expected_status}', got '{actual_status}'"
    )
    logger.info("STATUS VERIFIED — Lead '%s' is '%s' ✓", lead_id, expected_status)


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

def test_lead_lost_status_flow(page):
    """
    End-to-end: Admin creates a Quick Lead via Company Person →
    Lead Pool lookup to find assigned BDM → BDM logs in →
    updates status to 'Lost' → verifies the change.
    """
    logger.info("=" * 70)
    logger.info("START: test_lead_lost_status_flow")
    logger.info("=" * 70)

    # Initialise page objects
    login_page     = LoginPage(page)
    company_page   = CompanyPage(page)
    lead_pool_page = LeadPoolPage(page)
    my_leads_page  = MyLeadsPage(page)

    # ── Steps 1-2: Navigate + Admin login ────────────────────────────────────
    logger.info("Steps 1-2: Navigate and login as Admin")
    login_page.load()
    admin_email    = os.getenv("EMAIL", "Admin@infusive.com")
    admin_password = os.getenv("PASSWORD", "123456")
    login_page.login(admin_email, admin_password)
    login_page.wait_for_dashboard()
    logger.info("Admin login successful")

    # Generate unique lead data
    data           = _generate_lead_data()
    company_name   = data["company_name"]
    contact_person = data["contact_person"]
    phone          = data["phone"]
    email          = data["email"]
    logger.info(
        "Lead data — Company: '%s' | Contact: '%s' | Phone: '%s' | Email: '%s'",
        company_name, contact_person, phone, email,
    )

    # ── Steps 3-6: Company Person → Add New Company → Quick Lead → Save ──────
    logger.info("Step 3: Opening Company Person page")
    company_page.go_to_company()

    logger.info("Steps 4-5: Add New Company → Add Quick Lead")
    company_page.click_add_quick_lead()

    logger.info("Step 6: Filling Quick Lead form and saving")
    company_page.fill_quick_lead_form(
        name=company_name,
        email=email,
        phone=phone,
        country="United States",
        country_code="+1",
    )
    page.get_by_role("button", name="Save").click()

    toast = company_page.capture_toast(timeout=6_000)
    logger.info("Save toast: '%s'", toast)

    page.wait_for_url("**/company**", timeout=20_000)
    page.locator("tbody tr").first.wait_for(timeout=30_000)
    logger.info("Quick Lead created — back on Company list")

    # ── Steps 7-9: Lead module → Lead Pool → find lead ───────────────────────
    logger.info("Steps 7-8: Navigating to Lead Pool")
    lead_pool_page.go_to_lead_pool()

    logger.info("Step 9: Searching for lead by phone '%s'", phone)
    lead_id, assigned_to = lead_pool_page.find_lead_by_phone(
        phone, company_name=company_name
    )
    logger.info(
        "Lead found — ID: '%s' | Assigned To: '%s'", lead_id, assigned_to
    )

    # ── Step 10: Logout Admin ─────────────────────────────────────────────────
    logger.info("Step 10: Logging out Admin")
    _logout(page)

    # Resolve BDM credentials
    bdm_email, bdm_password = _map_assigned_to_credentials(assigned_to)
    logger.info("BDM email resolved: '%s'", bdm_email)

    # ── Step 11: Login as assigned BDM ───────────────────────────────────────
    logger.info("Step 11: Logging in as BDM '%s'", bdm_email)
    _login_with_retry(login_page, bdm_email, bdm_password)

    # ── Step 12: Open My Lead ─────────────────────────────────────────────────
    logger.info("Step 12: Navigating to My Lead")
    my_leads_page.go_to_my_leads()

    # ── Steps 13-16: Update lead status to 'Lost' ────────────────────────────
    _update_lead_status_to_lost(page, lead_id)

    # ── Step 17: Verify status is 'Lost' ─────────────────────────────────────
    logger.info("Step 17: Verifying Lead '%s' status is 'Lost'", lead_id)
    _verify_lead_status(page, lead_id, expected_status="Lost")

    logger.info("=" * 70)
    logger.info("PASSED: test_lead_lost_status_flow")
    logger.info("=" * 70)
