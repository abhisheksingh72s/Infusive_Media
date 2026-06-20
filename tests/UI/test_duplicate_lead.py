import pytest
import logging
from faker import Faker
from pages.company_page import CompanyPage
from pages.duplicate_lead_page import DuplicateLeadPage

logger = logging.getLogger(__name__)

def get_localized_data():
    fk = Faker("en_US")
    company_name = f"{fk.unique.company()}"
    company_name = company_name.replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("'", "").replace(",", "")
    phone = fk.numerify("##########")
    return {
        "company_name": company_name,
        "email": f"{company_name.replace(' ', '').lower()}@mailinator.com",
        "phone": phone
    }

@pytest.fixture
def company_page(logged_in_page):
    cp = CompanyPage(logged_in_page)
    cp.go_to_company()
    return cp

@pytest.fixture
def duplicate_lead_page(logged_in_page):
    dlp = DuplicateLeadPage(logged_in_page)
    return dlp

@pytest.mark.login_as("PreSales2@mailinator.com")
def test_duplicate_lead_verification_flow(company_page, duplicate_lead_page):
    logger.info("--- STARTING: DUPLICATE LEAD VERIFICATION FLOW ---")
    
    # Step 1: Generate unique lead details
    data = get_localized_data()
    company_name = data["company_name"]
    email = data["email"]
    phone = data["phone"]
    logger.info(f"Generated Lead Details: Company='{company_name}', Email='{email}', Phone='{phone}'")
    
    # Step 2: Create Quick Lead first time
    logger.info("Step 2: Creating Quick Lead (initial attempt)...")
    company_page.click_add_quick_lead()
    company_page.fill_quick_lead_form(
        name=company_name,
        email=email,
        phone=phone,
        country="United States",
        country_code="+1"
    )
    company_page.page.get_by_role("button", name="Save").click()
    
    toast_text = company_page.capture_toast()
    logger.info(f"First quick lead creation toast: '{toast_text}'")
    company_page.page.wait_for_url("**/company**", timeout=15000)
    company_page.page.locator("tbody tr").first.wait_for(timeout=30000)
    
    # Step 3: Attempt duplicate Quick Lead second time
    logger.info("Step 3: Creating Quick Lead with duplicate details...")
    company_page.click_add_quick_lead()
    company_page.fill_quick_lead_form(
        name=company_name,
        email=email,
        phone=phone,
        country="United States",
        country_code="+1"
    )
    company_page.page.get_by_role("button", name="Save").click()
    
    toast_text_dup = company_page.capture_toast()
    logger.info(f"Duplicate creation toast: '{toast_text_dup}'")
    
    # Clean up the modal/navigate back to company list
    company_page.navigate_to_company_list_if_needed()
    
    # Step 4: Navigate to Duplicate Lead sub-module
    logger.info("Step 4: Navigating to Duplicate Lead page...")
    duplicate_lead_page.go_to_duplicate_lead()
    
    # Step 5: Search for the duplicate lead in the table
    logger.info(f"Step 5: Searching for duplicate lead matching company '{company_name}'...")
    duplicate_lead_page.search_duplicate_lead(company_name)
    
    # Step 6: Verify the created duplicate lead is displayed
    logger.info("Step 6: Checking if duplicate lead is displayed in the table...")
    is_found = duplicate_lead_page.is_lead_visible_in_table(company_name, email=email)
    
    assert is_found, f"Duplicate lead for company '{company_name}' was not found in the Duplicate Lead table."
    logger.info("DUPLICATE LEAD VERIFICATION FLOW PASSED!")


@pytest.mark.login_as("PreSales2@mailinator.com")
def test_duplicate_company_poc_verification_flow(company_page, duplicate_lead_page):
    logger.info("--- STARTING: DUPLICATE COMPANY & POC VERIFICATION FLOW (NEGATIVE TEST) ---")
    
    # Step 1: Generate unique details
    data = get_localized_data()
    company_name = data["company_name"]
    email = data["email"]
    phone = data["phone"]
    website = f"https://{company_name.replace(' ', '').lower()}.com"
    poc_name = f"{company_name} POC"
    poc_email = f"{company_name.replace(' ', '').lower()}.poc@mailinator.com"
    logger.info(f"Generated Details: Company='{company_name}', Email='{email}', Phone='{phone}'")
    
    # Step 2: Create Company and POC first time
    logger.info("Step 2: Creating Company & POC (initial attempt)...")
    company_page.click_add_new_company_and_poc()
    company_page.fill_company_form(
        name=company_name,
        email=email,
        phone=phone,
        website=website
    )
    company_page.select_country_code("+1")
    company_page.select_service("UI/UX Design")
    company_page.click_stepper_next()
    
    company_page.fill_stepper_poc_form(
        index=0,
        name=poc_name,
        email=poc_email,
        designation="HR",
        phone=phone,
        country_code="+1",
        same_as_phone=True
    )
    company_page.page.get_by_text("Save", exact=True).click()
    
    toast_text = company_page.capture_toast()
    logger.info(f"First Company & POC creation toast: '{toast_text}'")
    company_page.page.wait_for_url("**/company**", timeout=15000)
    company_page.page.locator("tbody tr").first.wait_for(timeout=30000)
    
    # Step 3: Attempt duplicate Company & POC second time (Stepper 1 - Add Company)
    logger.info("Step 3: Creating Company & POC with duplicate details...")
    company_page.click_add_new_company_and_poc()
    company_page.fill_company_form(
        name=company_name,
        email=email,
        phone=phone,
        website=website
    )
    company_page.select_country_code("+1")
    company_page.select_service("UI/UX Design")
    
    # Click Next (on the stepper, this triggers the save attempt on the backend)
    company_page.page.get_by_role("button", name="Next").click()
    
    # Step 4: Verify toast message is displayed (Company Already Exists / Company name already exists)
    toast_text_dup = company_page.capture_toast()
    logger.info(f"Duplicate creation toast: '{toast_text_dup}'")
    assert "already exists" in toast_text_dup.lower(), f"Expected duplicate warning toast. Got: '{toast_text_dup}'"
    
    # Verify we did not progress/redirect, we are still on the form page
    assert "add-new-company-poc" in company_page.page.url, "Expected duplicate company creation to block and remain on form page."
    
    # Clean up the stepper wizard / navigate back to company list
    company_page.navigate_to_company_list_if_needed()
    
    # Step 5: Navigate to Duplicate Lead sub-module
    logger.info("Step 5: Navigating to Duplicate Lead page...")
    duplicate_lead_page.go_to_duplicate_lead()
    
    # Step 6: Search for the duplicate lead in the table
    logger.info(f"Step 6: Searching for duplicate lead matching company '{company_name}'...")
    duplicate_lead_page.search_duplicate_lead(company_name)
    
    # Verify that no duplicate lead record is created in the table (Expected Result)
    logger.info("Step 7: Verifying duplicate lead is NOT displayed in the table...")
    is_found = duplicate_lead_page.is_lead_visible_in_table(company_name, email=email)
    
    assert not is_found, f"Duplicate lead for company '{company_name}' was unexpectedly found in the Duplicate Lead table."
    logger.info("DUPLICATE COMPANY & POC VERIFICATION FLOW (NEGATIVE TEST) PASSED!")


