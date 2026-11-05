import pytest
import logging
import time
from faker import Faker

from pages.login_page import LoginPage
from pages.company_page import CompanyPage
from pages.lead_page import LeadPOCPage

logger = logging.getLogger(__name__)
fake = Faker("en_US")


@pytest.fixture
def company_page(logged_in_page):
    """Fixture initializing CompanyPage after UI login."""
    logger.info("Initializing CompanyPage POM fixture...")
    cp = CompanyPage(logged_in_page)
    return cp


@pytest.fixture
def lead_poc_page(logged_in_page):
    """Fixture initializing LeadPOCPage after UI login."""
    logger.info("Initializing LeadPOCPage POM fixture...")
    lp = LeadPOCPage(logged_in_page)
    return lp


@pytest.mark.login_as("PreSales2@mailinator.com")
def test_presales_create_company_and_poc_verify_in_lead_poc(company_page, lead_poc_page):
    """
    Test Name: Presales - Create Company and POC and Verify in Lead POC
    Automation Type: DOM

    Steps:
      1. Login to application with a user having Presales access.
      2. Open Company module from navigation.
      3. Wait for Company table to load and click Add New Company button.
      4. Open dropdown and select 'Add New Company & POC'.
      5. Fill required fields in Company form.
      6. Click Next button after completing Company form.
      7. Verify POC form is visible and fill all required POC details.
      8. Click Save and verify successful creation.
      9. Switch to Lead module.
      10. Open POC sub-module under Lead.
      11. Search for created Company/POC record.
      12. Verify newly created POC/company record is displayed in search results.
    """
    logger.info("==========================================================================")
    logger.info("STARTING TEST: Presales - Create Company and POC and Verify in Lead POC")
    logger.info("==========================================================================")

    # Generate unique test data
    timestamp = str(int(time.time()))
    unique_company = f"PresalesCo_{timestamp}"
    company_email = f"company_{timestamp}@mailinator.com"
    phone_number = f"98{timestamp[-8:]}"
    website_url = f"https://{unique_company.lower()}.com"
    poc_name = f"POC_{unique_company}"
    poc_email = f"poc_{timestamp}@mailinator.com"

    # Step 1: Login is performed by @pytest.mark.login_as("PreSales2@mailinator.com") / logged_in_page fixture
    logger.info("Step 1: Authenticated with Presales user.")

    # Step 2: Open Company Module
    logger.info("Step 2: Navigating to Company module...")
    company_page.go_to_company()
    assert "/company" in company_page.page.url, "Failed to navigate to Company module"

    # Step 3: Open Add New Company
    logger.info("Step 3: Clicking 'Add New Company' button...")
    company_page.click_add_new_company_menu()

    # Step 4: Select Add New Company and POC
    logger.info("Step 4: Selecting 'Add New Company & POC' option...")
    company_page.page.get_by_text("Add New Company & POC", exact=True).wait_for(state="visible", timeout=10000)
    company_page.page.get_by_text("Add New Company & POC", exact=True).click()

    # Step 5: Fill Company Form
    logger.info(f"Step 5: Filling Company Form for '{unique_company}'...")
    company_page.fill_company_form(
        name=unique_company,
        email=company_email,
        phone=phone_number,
        website=website_url
    )
    company_page.select_country_code("+1")
    company_page.select_service("UI/UX Design")
    company_page.select_lead_source("website")
    company_page.fill_note("Presales test company note")

    # Step 6: Click Next
    logger.info("Step 6: Clicking Next button...")
    company_page.click_next()

    # Step 7: Fill POC Form
    logger.info(f"Step 7: Verifying POC Form visibility and filling POC details for '{poc_name}'...")
    poc_name_input = company_page.page.locator("input[name='pocs.0.name']")
    if not poc_name_input.is_visible():
        poc_name_input = company_page.page.get_by_placeholder("Enter POC Name")
    if not poc_name_input.is_visible():
        poc_name_input = company_page.page.get_by_role("textbox", name="POC Name")
    poc_name_input.wait_for(state="visible", timeout=15000)
    assert poc_name_input.is_visible(), "POC Form is not visible"

    company_page.fill_poc_form(
        name=poc_name,
        email=poc_email,
        designation="Manager",
        phone=phone_number
    )

    # Step 8: Save POC
    logger.info("Step 8: Saving Company & POC record...")
    company_page.click_save()
    logger.info(f"Successfully saved Company & POC record: '{unique_company}'")

    # Step 9: Open Lead Module
    logger.info("Step 9: Switching to Lead module...")
    lead_poc_page.go_to_lead_module()

    # Step 10: Open POC Sub-module
    logger.info("Step 10: Opening POC sub-module under Lead...")
    lead_poc_page.open_poc_submodule()

    # Step 11: Search Created Record
    logger.info(f"Step 11: Searching for created record '{unique_company}'...")
    lead_poc_page.search_record(unique_company)

    # Step 12: Verify Record
    logger.info(f"Step 12: Verifying record '{unique_company}' in search results...")
    is_found = lead_poc_page.is_record_visible_in_table(unique_company, poc_name)
    assert is_found, f"Record for Company '{unique_company}' / POC '{poc_name}' was not found in Lead POC table search results."

    logger.info("==========================================================================")
    logger.info("FINISHED TEST: Presales - Create Company and POC and Verify in Lead POC [PASSED]")
    logger.info("==========================================================================")
