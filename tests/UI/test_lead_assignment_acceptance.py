import os
import time
import pytest
import logging
from pathlib import Path
from dotenv import load_dotenv

from pages.login_page import LoginPage
from pages.company_page import CompanyPage
from pages.lead_page import LeadPoolPage, MyLeadsPage, DynamicTable
from utilities import QALogger

logger = logging.getLogger(__name__)
load_dotenv(dotenv_path=Path(".env"), override=True)

def generate_realistic_lead_data():
    import random
    from faker import Faker
    fk = Faker("en_US")
    raw_company = fk.company()
    for ch in ("(", ")", "[", "]", "'", ",", ".", "-"):
        raw_company = raw_company.replace(ch, "")
    
    suffix = random.randint(1000, 9999)
    company_name = f"{raw_company} {suffix}"
    
    first_name = fk.first_name()
    last_name = fk.last_name()
    
    clean_domain = raw_company.replace(" ", "").lower()[:15]
    email = f"{first_name.lower()}.{last_name.lower()}@{clean_domain}.com"
    phone = fk.numerify("9#########")
    
    return {
        "company_name": company_name,
        "email": email,
        "phone": phone
    }

def map_assigned_to_credentials(assigned_to_name: str):
    name_clean = assigned_to_name.strip().lower()
    for i in range(1, 30):
        for fmt in (f"{i:02d}", str(i)):
            env_name = os.getenv(f"USER_{fmt}_FULL_NAME", "")
            if env_name and env_name.strip().lower() == name_clean:
                email = os.getenv(f"USER_{fmt}_EMAIL", "")
                password = os.getenv(f"USER_{fmt}_PASSWORD", "123456") or "123456"
                if email:
                    return email, password

    email_fallback = name_clean.replace(" ", "") + "@mailinator.com"
    logger.warning("No .env mapping found for '%s'; using fallback '%s'", assigned_to_name, email_fallback)
    return email_fallback, "123456"

def login_with_retry(login_page, email, password):
    login_page.login(email, password)
    try:
        login_page.wait_for_dashboard()
        return True
    except Exception:
        pass

    fallbacks = ["123456", "1234567", "123456789"]
    for fb_pass in fallbacks:
        if fb_pass == password:
            continue
        login_page.load()
        login_page.login(email, fb_pass)
        try:
            login_page.wait_for_dashboard()
            return True
        except Exception:
            pass

    return False

def _logout(page) -> None:
    try:
        page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        page.context.clear_cookies()
    except Exception:
        pass

    from urllib.parse import urlparse
    parsed = urlparse(page.url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    page.goto(f"{base_url}/login", wait_until="domcontentloaded")
    page.wait_for_url("**/login", timeout=15_000)
    page.reload()
    page.wait_for_url("**/login", timeout=15_000)
    page.get_by_role("textbox", name="Email").wait_for(state="visible", timeout=10_000)

@pytest.mark.ui
def test_lead_assignment_and_acceptance(page):
    """
    Scenario 1: Accept Lead Workflow
    Workflow:
      1. Login as PreSales2 (USER_11).
      2. Create a completely unique Quick Lead.
      3. Open Lead -> My Leads (/my-leads), reload, and search the unique lead.
      4. Logout PreSales.
      5. Login as Assigned BDM.
      6. Open Lead -> My Leads (/my-leads), reload, and search the unique lead.
      7. Validate Assigned User & Open Lead Details page (/lead-details).
      8. Accept Lead confirmation modal validation and execution.
    """
    start_time = time.time()
    qa_logger = QALogger()
    qa_logger.print_test_header("Lead Assignment and Acceptance Flow")

    presales_email = os.getenv("USER_11_EMAIL", "PreSales2@mailinator.com")
    presales_pass = os.getenv("USER_11_PASSWORD", "123456")

    login_page = LoginPage(page)
    company_page = CompanyPage(page)
    my_leads_page = MyLeadsPage(page)

    # Generate realistic lead data
    lead_data = generate_realistic_lead_data()
    company_name = lead_data["company_name"]
    email = lead_data["email"]
    phone = lead_data["phone"]

    # ── Step 1: PreSales Login ──────────────────────────────────────────
    current_step = 1
    action_name = "Login as PreSales"
    try:
        login_page.load()
        success = login_with_retry(login_page, presales_email, presales_pass)
        if not success:
            raise Exception(f"Failed to log in as PreSales '{presales_email}'")
        qa_logger.log_step_pass(current_step, 8, action_name)
    except Exception as e:
        qa_logger.report_failure(page, current_step, action_name, str(e), e, time.time() - start_time)
        raise

    # ── Step 2: Create Unique Quick Lead ──────────────────────────────────
    current_step = 2
    action_name = "Navigate & Add Quick Lead"
    try:
        company_page.go_to_company()
        company_page.click_add_quick_lead()
        company_page.fill_quick_lead_form(
            name=company_name,
            email=email,
            phone=phone,
            country="United States",
            country_code="+1"
        )
        page.get_by_role("button", name="Save").click()
        page.wait_for_timeout(2500)
        qa_logger.log_step_pass(current_step, 8, action_name)
    except Exception as e:
        qa_logger.report_failure(page, current_step, action_name, str(e), e, time.time() - start_time)
        raise

    # ── Step 3: Navigate to My Leads Sub-module & Search Created Lead ────
    current_step = 3
    action_name = "Navigate to My Leads & Search Created Lead"
    try:
        my_leads_page.go_to_my_leads()
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        page.locator("tbody tr").first.wait_for(state="visible", timeout=30000)

        search_box = page.get_by_placeholder("Search", exact=False).first
        search_box.fill(company_name)
        search_box.press("Enter")
        page.wait_for_timeout(2000)

        table = DynamicTable(page)
        row = table.find_row(column="COMPANY", value=company_name, match_partial=True)
        expected_assigned_user = row.get_value("ASSIGNED TO")

        logger.info(f"Company: {company_name}, Expected Assigned User: {expected_assigned_user}")
        qa_logger.log_step_pass(current_step, 8, action_name)
    except Exception as e:
        qa_logger.report_failure(page, current_step, action_name, str(e), e, time.time() - start_time)
        raise

    # ── Step 4: Logout PreSales ───────────────────────────────────────────
    current_step = 4
    action_name = "Logout PreSales"
    try:
        _logout(page)
        qa_logger.log_step_pass(current_step, 8, action_name)
    except Exception as e:
        qa_logger.report_failure(page, current_step, action_name, str(e), e, time.time() - start_time)
        raise

    # ── Step 5: Login as Assigned BDM ─────────────────────────────────────
    current_step = 5
    bdm_email, bdm_pass = map_assigned_to_credentials(expected_assigned_user)
    action_name = f"Login as Assigned BDM ({bdm_email})"
    try:
        success = login_with_retry(login_page, bdm_email, bdm_pass)
        if not success:
            raise Exception(f"Failed to log in as BDM '{bdm_email}'")
        qa_logger.log_step_pass(current_step, 8, action_name)
    except Exception as e:
        qa_logger.report_failure(page, current_step, action_name, str(e), e, time.time() - start_time)
        raise

    # ── Step 6: Search Lead in My Leads ───────────────────────────────────
    current_step = 6
    action_name = "Search Lead in My Leads"
    try:
        my_leads_page.go_to_my_leads()
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        page.locator("tbody tr").first.wait_for(state="visible", timeout=30000)

        search_box = page.get_by_placeholder("Search", exact=False).first
        search_box.fill(company_name)
        search_box.press("Enter")
        page.wait_for_timeout(2000)
        qa_logger.log_step_pass(current_step, 8, action_name)
    except Exception as e:
        qa_logger.report_failure(page, current_step, action_name, str(e), e, time.time() - start_time)
        raise

    # ── Step 7: Validate Assigned User & Open Lead Details Page ───────────
    current_step = 7
    action_name = "Validate Assigned User & Open Lead Details"
    try:
        page.wait_for_selector("table, tbody tr", timeout=15000)

        table = DynamicTable(page)
        row = table.find_row(column="COMPANY", value=company_name, match_partial=True)

        displayed_assigned = row.get_value("ASSIGNED TO")
        logger.info(f"Displayed Assigned User: '{displayed_assigned}' | Expected: '{expected_assigned_user}'")
        assert displayed_assigned.strip().lower() == expected_assigned_user.strip().lower(), (
            f"Assigned User mismatch: Expected '{expected_assigned_user}', got '{displayed_assigned}'"

        )

        company_cell = row.get_cell("COMPANY")
        link = company_cell.locator("a, button, [role='button']").first
        if link.count() > 0:
            link.click()
        else:
            company_cell.click()

        page.wait_for_timeout(2000)
        qa_logger.log_step_pass(current_step, 8, action_name)
    except Exception as e:
        qa_logger.report_failure(page, current_step, action_name, str(e), e, time.time() - start_time)
        raise

    # ── Step 8: Accept Lead Modal Validation & Execution ──────────────────
    current_step = 8
    action_name = "Accept Lead Modal & Execution"
    try:
        accept_btn = page.locator("//button[normalize-space()='Accept']").first
        accept_btn.wait_for(state="visible", timeout=10000)
        accept_btn.click()

        modal = page.locator("section[aria-modal='true'], [role='dialog'], .chakra-modal__content").first
        modal.wait_for(state="visible", timeout=10000)

        conf_msg = page.locator("//p[contains(normalize-space(),'Are you sure you want to accept this lead?')]")
        conf_msg.wait_for(state="visible", timeout=5000)

        reason_textarea = page.locator("//textarea[@placeholder='Reason for accepting the lead (Optional)']")
        reason_textarea.wait_for(state="visible", timeout=5000)

        confirm_btn = modal.locator("//button[normalize-space()='Accept']").first
        confirm_btn.click()

        page.wait_for_timeout(2000)
        qa_logger.log_step_pass(current_step, 8, action_name)
    except Exception as e:
        qa_logger.report_failure(page, current_step, action_name, str(e), e, time.time() - start_time)
        raise

    qa_logger.print_test_summary(time.time() - start_time)


@pytest.mark.ui
def test_lead_rejection_flow(page):
    """
    Scenario 2: Reject Lead Workflow
    Workflow:
      1. Login as PreSales2 (USER_11).
      2. Create a second unique Quick Lead.
      3. Open Lead -> My Leads (/my-leads), reload, and search the unique lead.
      4. Logout PreSales.
      5. Login as Assigned BDM.
      6. Open Lead -> My Leads (/my-leads), reload, and search the unique lead.
      7. Open Lead Details page (/lead-details).
      8. Reject Lead validation (empty textarea check, <20 chars validation check, 20+ chars valid rejection).
    """
    start_time = time.time()
    qa_logger = QALogger()
    qa_logger.print_test_header("Lead Rejection Flow")

    presales_email = os.getenv("USER_11_EMAIL", "PreSales2@mailinator.com")
    presales_pass = os.getenv("USER_11_PASSWORD", "123456")

    login_page = LoginPage(page)
    company_page = CompanyPage(page)
    my_leads_page = MyLeadsPage(page)

    # Generate realistic lead data
    lead_data = generate_realistic_lead_data()
    company_name = lead_data["company_name"]
    email = lead_data["email"]
    phone = lead_data["phone"]

    # Step 1: Login PreSales
    login_page.load()
    login_with_retry(login_page, presales_email, presales_pass)

    # Step 2: Create Quick Lead
    company_page.go_to_company()
    company_page.click_add_quick_lead()
    company_page.fill_quick_lead_form(
        name=company_name,
        email=email,
        phone=phone,
        country="United States",
        country_code="+1"
    )
    page.get_by_role("button", name="Save").click()
    page.wait_for_timeout(2500)

    # Step 3: Search in My Leads to capture assigned BDM
    my_leads_page.go_to_my_leads()
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    page.locator("tbody tr").first.wait_for(state="visible", timeout=30000)
    search_box = page.get_by_placeholder("Search", exact=False).first
    search_box.fill(company_name)
    search_box.press("Enter")
    page.wait_for_timeout(2000)

    table = DynamicTable(page)
    row = table.find_row(column="COMPANY", value=company_name, match_partial=True)
    expected_assigned_user = row.get_value("ASSIGNED TO")

    # Step 4: Logout PreSales
    _logout(page)

    # Step 5: Login as Assigned BDM
    bdm_email, bdm_pass = map_assigned_to_credentials(expected_assigned_user)
    login_with_retry(login_page, bdm_email, bdm_pass)

    # Step 6: Search Lead in My Leads
    my_leads_page.go_to_my_leads()
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    page.locator("tbody tr").first.wait_for(state="visible", timeout=30000)
    search_box = page.get_by_placeholder("Search", exact=False).first
    search_box.fill(company_name)
    search_box.press("Enter")
    page.wait_for_timeout(2000)

    # Step 7: Open Lead Details Page
    table = DynamicTable(page)
    row = table.find_row(column="COMPANY", value=company_name, match_partial=True)
    company_cell = row.get_cell("COMPANY")
    link = company_cell.locator("a, button, [role='button']").first
    if link.count() > 0:
        link.click()
    else:
        company_cell.click()
    page.wait_for_timeout(2000)

    # Step 8: Reject Lead Workflow Validation & Execution
    current_step = 8
    action_name = "Reject Lead Modal & Validations"
    try:
        from playwright.sync_api import expect

        reject_btn = page.locator("//button[normalize-space()='Reject']").first
        reject_btn.wait_for(state="visible", timeout=10000)
        reject_btn.click()

        modal = page.locator("section[aria-modal='true'], [role='dialog'], .chakra-modal__content").first
        modal.wait_for(state="visible", timeout=10000)

        inst_msg = page.locator("//p[contains(normalize-space(),'Please enter a reason for rejecting this lead.')]")
        inst_msg.wait_for(state="visible", timeout=5000)

        reason_textarea = page.locator("//textarea[@placeholder='Reason for rejecting the lead']")
        reason_textarea.wait_for(state="visible", timeout=5000)

        confirm_btn = modal.locator("//button[normalize-space()='Reject']").first

        # Validation 1: Blank textarea (Reject button is disabled)
        expect(confirm_btn).to_be_disabled()

        # Validation 2: < 20 characters (Reject button remains disabled)
        reason_textarea.fill("Too short reason")
        page.wait_for_timeout(500)
        expect(confirm_btn).to_be_disabled()

        # Validation 3: Valid 20+ characters rejection (Reject button becomes enabled)
        valid_reason = "This lead does not meet our minimum qualification requirements and budget criteria."
        reason_textarea.fill(valid_reason)
        page.wait_for_timeout(500)
        expect(confirm_btn).to_be_enabled()

        confirm_btn.click()
        page.wait_for_timeout(2000)

        modal.wait_for(state="hidden", timeout=10000)
        logger.info("Reject Lead modal closed successfully after valid 20+ character reason submission.")

        qa_logger.log_step_pass(current_step, 8, action_name)
    except Exception as e:
        qa_logger.report_failure(page, current_step, action_name, str(e), e, time.time() - start_time)
        raise

    qa_logger.print_test_summary(time.time() - start_time)


