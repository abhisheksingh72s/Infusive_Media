import pytest
import logging
import re
import os
from faker import Faker
from pages.login_page import LoginPage
from pages.company_page import CompanyPage
from pages.lead_page import LeadPoolPage, MyLeadsPage, RequirementGatheringPage

logger = logging.getLogger(__name__)

def get_localized_data():
    fk = Faker("en_US")
    company_name = f"RG Corp {fk.unique.company()}"
    company_name = company_name.replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("'", "").replace(",", "")
    phone = fk.numerify("##########")
    return {
        "company_name": company_name,
        "email": f"{company_name.replace(' ', '').lower()}@mailinator.com",
        "phone": phone
    }

def map_assigned_to_email(assigned_to_name):
    name_clean = assigned_to_name.strip()
    # Search all USER_XX_FULL_NAME environment variables
    for i in range(1, 30):
        idx = f"{i:02d}"
        env_name = os.getenv(f"USER_{idx}_FULL_NAME") or os.getenv(f"USER_{i}_FULL_NAME")
        if env_name and env_name.strip().lower() == name_clean.lower():
            email = os.getenv(f"USER_{idx}_EMAIL") or os.getenv(f"USER_{i}_EMAIL")
            password = os.getenv(f"USER_{idx}_PASSWORD") or os.getenv(f"USER_{i}_PASSWORD") or "123456"
            return email, password
            
    # Fallback structure (e.g. "BDM 3" -> bdm3@mailinator.com)
    email_fallback = name_clean.lower().replace(" ", "") + "@mailinator.com"
    return email_fallback, "123456"

def logout_user(page):
    logger.info("Logging out current user and clearing session storage...")
    # Clear all storage and cookies BEFORE navigating
    try:
        page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        page.context.clear_cookies()
    except Exception as e:
        logger.warning(f"Error clearing storage on current page: {e}")
        
    from urllib.parse import urlparse
    parsed = urlparse(page.url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    page.goto(f"{base_url}/login", wait_until="domcontentloaded")
    page.wait_for_url("**/login", timeout=15000)
    
    # Reload page to ensure clean state
    page.reload()
    page.wait_for_url("**/login", timeout=15000)
    
    # Verify we are on a clean login page
    page.get_by_role("textbox", name="Email").wait_for(state="visible", timeout=10000)
    logger.info("Successfully logged out and cleared session.")

def login_with_retry(login_page, email, password):
    logger.info(f"Attempting login as {email} with password: {password}")
    login_page.login(email, password)
    try:
        login_page.wait_for_dashboard()
        logger.info("Login successful!")
        return
    except Exception:
        logger.warning(f"Login failed for {email} with password {password}.")
        
    fallbacks = ["123456", "1234567", "123456789"]
    for fb_pass in fallbacks:
        if fb_pass == password:
            continue
        logger.info(f"Retrying login for {email} with fallback password: {fb_pass}")
        login_page.load()
        login_page.login(email, fb_pass)
        try:
            login_page.wait_for_dashboard()
            logger.info(f"Login successful with fallback password: {fb_pass}!")
            return
        except Exception:
            logger.warning(f"Login failed with fallback password: {fb_pass}.")
            
    raise Exception(f"Failed to log in as BDM '{email}' with any standard credentials.")

def test_presales_to_bdm_requirement_gathering(page):
    logger.info("--- STARTING: PRESALES TO BDM REQUIREMENT GATHERING FLOW ---")
    
    # Initialize Page Objects
    login_page = LoginPage(page)
    company_page = CompanyPage(page)
    lead_pool_page = LeadPoolPage(page)
    my_leads_page = MyLeadsPage(page)
    req_gathering_page = RequirementGatheringPage(page)
    
    # Step 1: Login as PreSales
    logger.info("Step 1: Logging in as PreSales user...")
    login_page.load()
    login_page.login("PreSales2@mailinator.com", "123456")
    login_page.wait_for_dashboard()
    
    # Generate unique lead details
    data = get_localized_data()
    company_name = data["company_name"]
    email = data["email"]
    phone = data["phone"]
    logger.info(f"Generated Lead details: Company='{company_name}', Phone='{phone}', Email='{email}'")
    
    # Step 2: Create Quick Lead
    logger.info("Step 2: Creating Quick Lead...")
    company_page.go_to_company()
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
    logger.info(f"Quick lead creation toast: '{toast_text}'")
    company_page.page.wait_for_url("**/company**", timeout=15000)
    company_page.page.locator("tbody tr").first.wait_for(timeout=30000)
    
    # Step 3: Find created lead in LeadPool matching phone number or company name
    logger.info("Step 3: Finding created lead in Lead Pool...")
    lead_pool_page.go_to_lead_pool()
    lead_id, assigned_to = lead_pool_page.find_lead_by_phone(phone, company_name=company_name)
    logger.info(f"Lead ID: {lead_id}, Assigned BDM: {assigned_to}")
    
    # Step 4: Logout
    logger.info("Step 4: Logging out PreSales user...")
    logout_user(page)
    
    # Step 5: Map assigned BDM to credentials
    bdm_email, bdm_password = map_assigned_to_email(assigned_to)
    logger.info(f"Step 5: Mapped BDM credentials: Email='{bdm_email}', Password='{bdm_password}'")
    
    # Step 6: Log in as BDM
    logger.info(f"Step 6: Logging in as BDM ({bdm_email})...")
    login_with_retry(login_page, bdm_email, bdm_password)
    
    # Step 7: Go to My Leads and update status to "Requirement Gathering"
    logger.info("Step 7: Navigating to My Leads...")
    my_leads_page.go_to_my_leads()
    
    logger.info("Step 8: Updating Lead Status to 'Requirement Gathering'...")
    my_leads_page.update_lead_status(lead_id, "Requirement Gathering")
    
    # Step 9: Open Requirement Gathering form from Action menu
    logger.info("Step 9: Opening Requirement Gathering form...")
    my_leads_page.open_requirement_gathering_form(lead_id)
    
    # Step 10 & 11: Fill Steps 1 and 2
    logger.info("Step 10: Filling Step 1 of Requirement Gathering form...")
    req_gathering_page.fill_step_1(
        industry_type="Retail & E-Commerce",
        lead_source="website",
        designation="HR",
    )

    logger.info("Step 11: Filling Step 2 of Requirement Gathering form...")
    req_gathering_page.fill_step_2_and_submit(
        business_type="B2C",
        years_in_business="4",
        search_source="Google Ads",
        budget="50000",
        competitor="competior1",
        business_challenges="Business challenge",
    )
    # Step 12: Verify submit success (no error toast, redirect to /my-leads)
    logger.info("Step 12: Verifying successful submission...")
    page.wait_for_url("**/my-leads", timeout=20000)
    logger.info("PRESALES TO BDM REQUIREMENT GATHERING FLOW PASSED!")
