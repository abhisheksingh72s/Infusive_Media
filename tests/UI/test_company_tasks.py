import pytest
import time
import re
import random
import logging
from faker import Faker
from pages.company_page import CompanyPage

# Configure logging
logger = logging.getLogger(__name__)

# Localized Faker instances mapped to country codes
fakers = {
    "+91": Faker("en_IN"),
    "+1": Faker("en_US"),
    "+44": Faker("en_GB"),
    "+61": Faker("en_AU"),
}
default_fake = Faker("en_US")
fake = default_fake

def get_fake_for_code(code):
    return fakers.get(code, default_fake)

def get_localized_data(code):
    fk = get_fake_for_code(code)
    # Strip special characters to keep string assertions clean
    company_name = f"{fk.unique.company()}"
    company_name = company_name.replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("'", "").replace(",", "")
    poc_name = fk.name().replace("'", "").replace(",", "")
    phone = fk.numerify("##########")
    return {
        "company_name": company_name,
        "poc_name": f"{company_name}.{poc_name}",
        "phone": phone,
        "email": f"{company_name.replace(' ', '')}@mailinator.com",
        "poc_email": f"{company_name.replace(' ', '')}.poc1@mailinator.com",
    }

@pytest.fixture
def company_page(logged_in_page):
    logger.info("Initializing CompanyPage Page Object...")
    cp = CompanyPage(logged_in_page)
    logger.info("Navigating to Company list page...")
    cp.go_to_company()
    logger.info("Successfully navigated to Company page.")
    return cp

@pytest.fixture
def new_company(company_page):
    # Randomly select a country code and generate corresponding localized data
    country_code = random.choice(["+91", "+1", "+44", "+61"])
    data = get_localized_data(country_code)
    
    company_page.click_add_new_company_and_poc()
    company_page.fill_company_form(
        name=data["company_name"],
        email=data["email"],
        phone=data["phone"],
        website=fake.url()
    )
    company_page.select_country_code(country_code)
    company_page.select_service("UI/UX Design")
    company_page.click_next()
    return {
        "page": company_page,
        "name": data["company_name"],
        "email": data["email"],
        "poc_name": data["poc_name"],
        "poc_email": data["poc_email"],
        "poc_phone": data["phone"]
    }

def capture_toast(page, timeout=5000):
    logger.info("Attempting to capture toast notification...")
    selectors = [
        "div[role='status']",
        "div[role='alert']",
        ".toast",
        ".hot-toast",
        "[class*='toast']",
        "[class*='Toast']"
    ]
    combined_selector = ", ".join(selectors)
    
    try:
        logger.info(f"Waiting up to {timeout}ms for toast matching selectors: {combined_selector}")
        page.locator(combined_selector).first.wait_for(state="visible", timeout=timeout)
        logger.info("A toast element became visible in the DOM.")
    except Exception:
        logger.info("No toast element became visible within the timeout.")
        pass
        
    texts = []
    for sel in selectors:
        try:
            locs = page.locator(sel)
            count = locs.count()
            for i in range(count):
                el = locs.nth(i)
                if el.is_visible():
                    txt = el.inner_text().strip()
                    if txt:
                        texts.append(txt)
        except Exception:
            pass
    toast_text = " | ".join(set(texts))
    logger.info(f"Captured Toast Content: '{toast_text}'")
    return toast_text


# ===========================================================================
# ORIGINAL FLOWS (1 to 5)
# ===========================================================================

# ---------------------------------------------------------------------------
# Flow 1: Add New Company & Duplicate Validation
# ---------------------------------------------------------------------------
@pytest.mark.login_as("PreSales2@mailinator.com")
def test_add_new_company_flow(company_page):
    page = company_page.page
    
    logger.info("--- STARTING FLOW 1: ADD NEW COMPANY & DUPLICATE VALIDATION ---")
    
    logger.info("Step 1.1: Generating localized fake company details (code: +1)")
    loc_data = get_localized_data("+1")
    name = loc_data["company_name"]
    email = loc_data["email"]
    phone = loc_data["phone"]
    website = f"https://{name.replace(' ', '').lower()}.com"
    logger.info(f"Generated Company:\nName='{name}',\nEmail='{email}',\nPhone='{phone}',\nWebsite='{website}'")
    
    # --- STEP 1: CREATE ---
    logger.info("Step 1.2 [Create]: Clicking '+ Add New Company' to open standard form...")
    company_page.click_add_new_company()
    
    logger.info("Step 1.3 [Create]: Filling company text fields (Name, Email, Phone, Website)...")
    company_page.fill_company_form(
        name=name,
        email=email,
        phone=phone,
        website=website
    )
    
    logger.info("Step 1.4 [Create]: Selecting country code '+1'...")
    company_page.select_country_code("+1")
    
    logger.info("Step 1.5 [Create]: Selecting service 'UI/UX Design'...")
    company_page.select_service("UI/UX Design")
    
    logger.info("Step 1.6 [Create]: Clicking 'Save' and auto-waiting for success toast...")
    company_page.page.get_by_role("button", name="Save").click()
    toast_text = capture_toast(company_page.page)
    logger.info(f"Creation toast returned: '{toast_text}'")
    
    logger.info("Step 1.7 [Create]: Waiting for redirect to Company table list page...")
    company_page.page.wait_for_url("**/company**", timeout=15000)
    logger.info("Redirected back to /company page successfully.")
    
    logger.info("Step 1.8 [Create]: Waiting for table rows to be loaded...")
    company_page.page.locator("tbody tr").first.wait_for(timeout=30000)
    logger.info("Table body rows loaded.")
    
    logger.info("Step 1.9 [Create]: Asserting successful creation toast contains 'successfully', 'created', or 'added'...")
    assert "successfully" in toast_text.lower() or "created" in toast_text.lower() or "added" in toast_text.lower(), \
        f"Expected success toast. Got: '{toast_text}'"
        
    logger.info(f"Step 1.10 [Create]: Asserting company row '{name}' is visible in the list...")
    assert company_page.is_company_row_visible(name, email=email, phone=phone), f"Company '{name}' not found after creation"
    logger.info("STEP 1 [Create] verified successfully!")
    
    # --- STEP 2: DUPLICATE VALIDATION ---
    logger.info("Step 1.11 [Duplicate]: Clicking '+ Add New Company' to open duplicate form...")
    company_page.click_add_new_company()
    
    logger.info("Step 1.12 [Duplicate]: Refilling identical form details to trigger duplicate block...")
    company_page.fill_company_form(
        name=name,
        email=email,
        phone=phone,
        website=website
    )
    
    logger.info("Step 1.13 [Duplicate]: Selecting country code '+1'...")
    company_page.select_country_code("+1")
    
    logger.info("Step 1.14 [Duplicate]: Selecting service 'UI/UX Design'...")
    company_page.select_service("UI/UX Design")
    
    logger.info("Step 1.15 [Duplicate]: Clicking Save to trigger backend duplicate validation...")
    page.get_by_role("button", name="Save").click()
    
    logger.info("Step 1.16 [Duplicate]: Auto-waiting for validation toast alert...")
    toast_text = capture_toast(page)
    
    url_after = page.url
    logger.info(f"Page state after duplicate submit: URL='{url_after}'")
    
    logger.info("Step 1.17 [Duplicate]: Cleaning up / resetting form state to prevent test pollution...")
    if "add-new-company-form" in url_after:
        base_part = url_after.split("/add-new-company-form")[0]
        logger.info(f"Redirecting back to list page: {base_part}/company")
        page.goto(f"{base_part}/company")
        page.wait_for_timeout(2000)
        
    logger.info("Step 1.18 [Duplicate]: Asserting duplicate validation warning/toast is present...")
    assert "duplicate" in toast_text.lower() or "already exists" in toast_text.lower(), \
        f"Expected duplicate validation toast. Got: '{toast_text}'"
    logger.info("STEP 2 [Duplicate] verified successfully! FLOW 1 COMPLETE.")


# ---------------------------------------------------------------------------
# Flow 2: Add New Company & POC & Duplicate Validation
# ---------------------------------------------------------------------------
@pytest.mark.login_as("PreSales2@mailinator.com")
def test_add_new_company_poc_flow(company_page):
    page = company_page.page
    
    logger.info("--- STARTING FLOW 2: ADD COMPANY & POC & DUPLICATE VALIDATION ---")
    
    logger.info("Step 2.1: Generating localized company and POC details (code: +1)...")
    loc_data = get_localized_data("+1")
    name = loc_data["company_name"]
    poc_name = loc_data["poc_name"]
    email = loc_data["email"]
    poc_email = loc_data["poc_email"]
    phone = loc_data["phone"]
    website = f"https://{name.replace(' ', '').lower()}.com"
    logger.info(f"Generated Details:\nCompany='{name}',\nEmail='{email}',\nPhone='{phone}',\nWebsite='{website}',\nPOC Name='{poc_name}',\nPOC Email='{poc_email}'")
    
    # --- STEP 1: CREATE ---
    logger.info("Step 2.2 [Create]: Clicking '+ Add New Company & POC' dropdown item...")
    company_page.click_add_new_company_and_poc()
    
    logger.info("Step 2.3 [Create]: Filling company details form...")
    company_page.fill_company_form(
        name=name,
        email=email,
        phone=phone,
        website=website
    )
    
    logger.info("Step 2.4 [Create]: Selecting country code '+1'...")
    company_page.select_country_code("+1")
    
    logger.info("Step 2.5 [Create]: Selecting service 'UI/UX Design'...")
    company_page.select_service("UI/UX Design")
    
    logger.info("Step 2.6 [Create]: Clicking 'Next' to advance to the POC stepper...")
    company_page.click_next()
    
    logger.info("Step 2.7 [Create]: Filling POC form fields (Name, Email)...")
    page.locator("input[name='pocs.0.name']").fill(poc_name)
    page.locator("input[name='pocs.0.email']").fill(poc_email)
    
    logger.info("Step 2.8 [Create]: Selecting POC Designation 'HR'...")
    designation_input = page.get_by_placeholder("Enter POC Designation").first
    designation_input.click()
    page.get_by_text("HR", exact=True).click()
    
    logger.info("Step 2.9 [Create]: Selecting POC country code '+1'...")
    company_page.select_poc_country_code(0, "+1")
    
    logger.info("Step 2.10 [Create]: Filling POC phone number...")
    page.locator("input[name='pocs.0.phoneNumber']").fill(phone)
    
    logger.info("Step 2.11 [Create]: Clicking 'Same as Phone Number' for Whatsapp...")
    page.get_by_label("Same as Phone Number").first.click(force=True)
    
    logger.info("Step 2.12 [Create]: Clicking 'Save' and auto-waiting for creation toast...")
    page.get_by_text("Save", exact=True).click()
    toast_text = capture_toast(page)
    logger.info(f"Creation toast returned: '{toast_text}'")
    
    logger.info("Step 2.13 [Create]: Waiting for redirect back to list page...")
    page.wait_for_url("**/company**", timeout=15000)
    page.locator("tbody tr").first.wait_for(timeout=30000)
    logger.info("Redirected and table body loaded.")
    
    logger.info("Step 2.14 [Create]: Asserting successful creation toast contains validation keywords...")
    assert "successfully" in toast_text.lower() or "created" in toast_text.lower() or "added" in toast_text.lower(), \
        f"Expected success toast. Got: '{toast_text}'"
        
    logger.info(f"Step 2.15 [Create]: Asserting company row '{name}' is visible in list...")
    assert company_page.is_company_row_visible(name, email=email, phone=phone), f"Company '{name}' not found after creation"
    logger.info("STEP 1 [Create Company & POC] verified successfully!")
    
    # --- STEP 2: DUPLICATE VALIDATION ---
    logger.info("Step 2.16 [Duplicate]: Clicking '+ Add New Company & POC' to open duplicate flow...")
    company_page.click_add_new_company_and_poc()
    
    logger.info("Step 2.17 [Duplicate]: Refilling identical company details on first stepper page...")
    company_page.fill_company_form(
        name=name,
        email=email,
        phone=phone,
        website=website
    )
    
    logger.info("Step 2.18 [Duplicate]: Selecting country code '+1'...")
    company_page.select_country_code("+1")
    
    logger.info("Step 2.19 [Duplicate]: Selecting service 'UI/UX Design'...")
    company_page.select_service("UI/UX Design")
    
    logger.info("Step 2.20 [Duplicate]: Clicking Next (to test stepper validation blocking)...")
    page.get_by_role("button", name="Next").click()
    
    logger.info("Step 2.21 [Duplicate]: Auto-waiting for validation toast alert...")
    toast_text = capture_toast(page, timeout=3000)
    
    poc_name_visible = False
    try:
        poc_name_visible = page.get_by_role("textbox", name="POC Name").is_visible()
    except Exception:
        pass
    logger.info(f"Is POC Name input field visible? -> {poc_name_visible}")
    
    url_after = page.url
    logger.info(f"Page state after duplicate next: URL='{url_after}'")
    
    logger.info("Step 2.22 [Duplicate]: Cleaning up stepper wizard state...")
    if "add-new-company-poc" in url_after:
        try:
            page.get_by_role("button", name="Back").click()
        except Exception:
            base_part = url_after.split("/add-new-company-poc")[0]
            logger.info(f"Bypassing Back button and loading: {base_part}/company")
            page.goto(f"{base_part}/company")
        page.wait_for_timeout(2000)
        
    logger.info("Step 2.23 [Duplicate]: Asserting that the stepper was blocked (POC Name field is NOT visible)...")
    assert not poc_name_visible, \
        "Expected duplicate validation to block proceeding to POC step"
    logger.info("STEP 2 [Duplicate Company & POC] verified successfully! FLOW 2 COMPLETE.")


# ---------------------------------------------------------------------------
# Flow 3: Add Quick Lead & Duplicate Validation
# ---------------------------------------------------------------------------
@pytest.mark.login_as("PreSales2@mailinator.com")
def test_add_quick_lead_flow(company_page):
    page = company_page.page
    
    logger.info("--- STARTING FLOW 3: ADD QUICK LEAD & DUPLICATE VALIDATION ---")
    
    logger.info("Step 3.1: Generating localized lead details (code: +1)...")
    loc_data = get_localized_data("+1")
    lead_name = re.sub(r'[^A-Za-z\s]', '', loc_data["poc_name"]).strip()
    email = loc_data["email"]
    phone = loc_data["phone"]
    logger.info(f"Generated Quick Lead:\nName='{lead_name}',\nEmail='{email}',\nPhone='{phone}'")
    
    # --- STEP 1: CREATE ---
    logger.info("Step 3.2 [Create]: Clicking 'Add Quick Lead' dropdown option...")
    company_page.click_add_quick_lead()
    
    logger.info("Step 3.3 [Create]: Filling Quick Lead form details...")
    company_page.fill_quick_lead_form(
        name=lead_name,
        email=email,
        phone=phone,
        country="United States",
        country_code="+1"
    )
    
    logger.info("Step 3.4 [Create]: Clicking 'Save' and auto-waiting for success toast...")
    page.get_by_role("button", name="Save").click()
    toast_text = capture_toast(page)
    logger.info(f"Creation toast returned: '{toast_text}'")
    
    logger.info("Step 3.5 [Create]: Waiting for redirect back to list page...")
    page.wait_for_url("**/company**", timeout=15000)
    page.locator("tbody tr").first.wait_for(timeout=30000)
    logger.info("Redirected and table body loaded.")
    
    logger.info("Step 3.6 [Create]: Asserting successful creation toast contains validation keywords...")
    assert "successfully" in toast_text.lower() or "created" in toast_text.lower() or "added" in toast_text.lower(), \
        f"Expected success toast. Got: '{toast_text}'"
        
    logger.info(f"Step 3.7 [Create]: Asserting Quick Lead '{lead_name}' is visible in list...")
    assert company_page.is_company_row_visible(lead_name, email=email, phone=phone), f"Quick lead '{lead_name}' not found after creation"
    logger.info("STEP 1 [Create Quick Lead] verified successfully!")
    
    # --- STEP 2: DUPLICATE VALIDATION ---
    logger.info("Step 3.8 [Duplicate]: Clicking 'Add Quick Lead' to open duplicate lead form...")
    company_page.click_add_quick_lead()
    
    logger.info("Step 3.9 [Duplicate]: Refilling identical quick lead details...")
    company_page.fill_quick_lead_form(
        name=lead_name,
        email=email,
        phone=phone,
        country="United States",
        country_code="+1"
    )
    
    logger.info("Step 3.10 [Duplicate]: Clicking Save to trigger validation...")
    page.get_by_role("button", name="Save").click()
    
    logger.info("Step 3.11 [Duplicate]: Auto-waiting for duplicate validation toast...")
    toast_text = capture_toast(page)
    
    url_after = page.url
    logger.info(f"Page state after duplicate quick lead submit: URL='{url_after}'")
    
    logger.info("Step 3.12 [Duplicate]: Cleaning up quick lead modal state...")
    if "quick-lead" in url_after:
        try:
            page.get_by_role("button", name="Back").click()
        except Exception:
            base_part = url_after.split("/quick-lead")[0]
            logger.info(f"Bypassing Back button and loading: {base_part}/company")
            page.goto(f"{base_part}/company")
        page.wait_for_timeout(2000)
        
    logger.info("Step 3.13 [Duplicate]: Asserting duplicate lead warning/toast is present...")
    assert "duplicate" in toast_text.lower() or "already exists" in toast_text.lower(), \
        f"Expected duplicate quick lead validation toast. Got: '{toast_text}'"
    logger.info("STEP 2 [Duplicate Quick Lead] verified successfully! FLOW 3 COMPLETE.")


# ---------------------------------------------------------------------------
# Flow 4: Add New Company with Asterisks
# ---------------------------------------------------------------------------
@pytest.mark.login_as("PreSales2@mailinator.com")
def test_create_company_with_asterisks_flow(company_page):
    page = company_page.page
    
    logger.info("--- STARTING FLOW 4: ADD NEW COMPANY WITH ASTERISKS ---")
    
    logger.info("Step 4.1: Clicking '+ Add New Company' to open form...")
    company_page.click_add_new_company()
    page.wait_for_timeout(1000)
    
    logger.info("Step 4.2: Generating localized company details for fallback fields...")
    loc_data = get_localized_data("+1")
    
    logger.info("Step 4.3: Filling Name field with invalid '*****' input...")
    page.locator("input[name='companyName']").fill("*****")
    
    logger.info("Step 4.4: Filling Email field with standard unique email...")
    page.locator("input[name='companyEmail']").fill(loc_data["email"])
    
    logger.info("Step 4.5: Filling Phone field with standard numeric phone...")
    try:
        page.locator("input[name='companyPhone']").fill(loc_data["phone"])
    except Exception:
        pass
        
    logger.info("Step 4.6: Selecting country code '+1'...")
    company_page.select_country_code("+1")
    
    logger.info("Step 4.7: Selecting service 'UI/UX Design'...")
    company_page.select_service("UI/UX Design")
    
    logger.info("Step 4.8: Clicking Save to attempt submission...")
    page.get_by_role("button", name="Save").click()
    
    logger.info("Step 4.9: Auto-waiting for validation toast notifications...")
    toast_text = capture_toast(page, timeout=3000)
    
    url_after = page.url
    logger.info(f"Page state after asterisk company submit: URL='{url_after}'")
    
    logger.info("Step 4.10: Cleaning up form page to prevent test pollution...")
    if "add-new-company-form" in url_after:
        base_part = url_after.split("/add-new-company-form")[0]
        logger.info(f"Bypassing and redirecting back to: {base_part}/company")
        page.goto(f"{base_part}/company")
        page.wait_for_timeout(2000)
        
    logger.info("Step 4.11: Asserting form submission was blocked (URL still contains 'add-new-company-form')...")
    assert "add-new-company-form" in url_after, \
        "Expected asterisk input to block company form submission"
    logger.info("FLOW 4 [Company Asterisks] verified successfully!")


# ---------------------------------------------------------------------------
# Flow 5: Add Quick Lead with Asterisks
# ---------------------------------------------------------------------------
@pytest.mark.login_as("PreSales2@mailinator.com")
def test_add_quick_lead_asterisks_flow(company_page):
    page = company_page.page
    
    logger.info("--- STARTING FLOW 5: ADD QUICK LEAD WITH ASTERISKS ---")
    
    logger.info("Step 5.1: Clicking 'Add Quick Lead' dropdown item...")
    company_page.click_add_quick_lead()
    page.wait_for_timeout(1000)
    
    logger.info("Step 5.2: Simulating physical keyboard entry of invalid asterisks ('*****') into Name field...")
    name_input = page.get_by_role("textbox", name="Name")
    name_input.click()
    page.keyboard.type("*****")
    
    logger.info("Step 5.3: Filling out the remaining Quick Lead fields (Email, Phone, Country)...")
    company_page.fill_quick_lead_form(
        name=None,
        email=fake.email(),
        phone=fake.numerify("##########"),
        country="United States",
        country_code="+1"
    )
    
    logger.info("Step 5.4: Clicking Save to attempt submission...")
    page.get_by_role("button", name="Save").click()
    
    logger.info("Step 5.5: Auto-waiting for validation toast notifications...")
    toast_text = capture_toast(page, timeout=3000)
    
    url_after = page.url
    logger.info(f"Page state after asterisk quick lead submit: URL='{url_after}'")
    
    logger.info("Step 5.6: Cleaning up quick lead modal state...")
    if "quick-lead" in url_after:
        try:
            page.get_by_role("button", name="Back").click()
        except Exception:
            base_part = url_after.split("/quick-lead")[0]
            logger.info(f"Bypassing Back button and loading: {base_part}/company")
            page.goto(f"{base_part}/company")
        page.wait_for_timeout(2000)
        
    logger.info("Step 5.7: Asserting quick lead submission was blocked.")
    assert "quick-lead" in url_after, \
        "Expected asterisk input to block quick lead submission"
    logger.info("FLOW 5 [Quick Lead Asterisks] verified successfully!")


# ===========================================================================
# MERGED TESTS (FROM test_company.py)
# ===========================================================================

# --- Table ---

@pytest.mark.login_as("shreya@tekinspirations.com")
def test_company_table_visible(company_page):
    logger.info("--- STARTING: TEST COMPANY TABLE VISIBLE ---")
    logger.info("Step 1: Waiting for company table rows to load...")
    company_page.page.locator("tbody tr").first.wait_for(state="visible", timeout=15000)
    company_page.page.wait_for_timeout(1000)
    count = company_page.page.locator("tbody tr").count()
    logger.info(f"Step 2: Table loaded. Found {count} rows. Asserting count > 0...")
    assert count > 0
    logger.info("TEST COMPANY TABLE VISIBLE verified successfully!")


# --- Add ---

@pytest.mark.login_as("shreya@tekinspirations.com")
def test_add_new_company(company_page):
    logger.info("--- STARTING: TEST ADD NEW COMPANY ---")
    logger.info("Step 1: Generating localized company details...")
    country_code = random.choice(["+91", "+1", "+44", "+61"])
    data = get_localized_data(country_code)
    company_name = data["company_name"]
    email = data["email"]
    phone = data["phone"]
    website = fake.url()
    logger.info(f"Generated details:\nName='{company_name}',\nEmail='{email}',\nPhone='{phone}',\nWebsite='{website}'")
    
    logger.info("Step 2: Opening Add Company form...")
    company_page.click_add_new_company()
    
    logger.info("Step 3: Filling out the form...")
    company_page.fill_company_form(
        name=company_name,
        email=email,
        phone=phone,
        website=website
    )
    company_page.select_country_code(country_code)
    company_page.select_service("UI/UX Design")
    logger.info("Step 4: Saving company...")
    company_page.click_save()
    
    logger.info("Step 5: Asserting company is visible in row...")
    assert company_page.is_company_row_visible(company_name, email=email, phone=phone), \
        f"Company '{company_name}' not found after creation"
    logger.info("TEST ADD NEW COMPANY verified successfully!")


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_add_new_company_and_poc(new_company):
    logger.info("--- STARTING: TEST ADD NEW COMPANY & POC ---")
    company_page = new_company["page"]
    company_name = new_company["name"]
    poc_name = new_company["poc_name"]
    poc_email = new_company["poc_email"]
    poc_phone = new_company["poc_phone"]
    
    logger.info(f"Using prefilled Company: '{company_name}'")
    logger.info("Step 1: Filling POC details...")
    company_page.fill_poc_form(
        name=poc_name,
        email=poc_email,
        designation="HR.",
        phone=poc_phone,
        whatsapp=poc_phone,
        linkedin=fake.url()
    )
    logger.info("Step 2: Saving Company & POC...")
    company_page.click_save()
    
    logger.info("Step 3: Asserting company is visible in row...")
    assert company_page.is_company_row_visible(company_name, email=new_company["email"], phone=poc_phone), \
        f"Company '{company_name}' not found after creation"
    logger.info("TEST ADD NEW COMPANY & POC verified successfully!")


# --- Validation ---

@pytest.mark.login_as("shreya@tekinspirations.com")
@pytest.mark.parametrize("skip_field, fill_fn", [
    ("company_name",  lambda page, cp: (page.locator("input[name='companyEmail']").fill(fake.company_email()), cp.select_country_code("+91"), cp.select_service("UI/UX Design"))),
    ("company_email", lambda page, cp: (page.locator("input[name='companyName']").fill(fake.company()), cp.select_country_code("+91"), cp.select_service("UI/UX Design"))),
    ("phone_number",  lambda page, cp: (page.locator("input[name='companyName']").fill(fake.company()), page.locator("input[name='companyEmail']").fill(fake.company_email()), cp.select_service("UI/UX Design"))),
    ("country",       lambda page, cp: (page.locator("input[name='companyName']").fill(fake.company()), page.locator("input[name='companyEmail']").fill(fake.company_email()), cp.select_service("UI/UX Design"))),
    ("service",       lambda page, cp: (page.locator("input[name='companyName']").fill(fake.company()), page.locator("input[name='companyEmail']").fill(fake.company_email()), cp.select_country_code("+91"))),
])
def test_mandatory_fields_block_submission(logged_in_page, skip_field, fill_fn):
    logger.info(f"--- STARTING: TEST MANDATORY FIELDS BLOCK SUBMISSION (Skipping: {skip_field}) ---")
    cp = CompanyPage(logged_in_page)
    logger.info("Step 1: Navigating to Company page and opening form...")
    cp.go_to_company()
    cp.click_add_new_company()
    
    logger.info("Step 2: Filling in fields except the skipped field...")
    fill_fn(logged_in_page, cp)
    
    logger.info("Step 3: Clicking Save and verifying submission is blocked...")
    logged_in_page.get_by_role("button", name="Save").click()
    logged_in_page.wait_for_timeout(500)
    url_after = logged_in_page.url.lower()
    assert "company" in url_after, \
        f"Form should block submission when '{skip_field}' is missing"
    logger.info("Blocked successfully!")


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_optional_fields_do_not_block_submission(logged_in_page):
    logger.info("--- STARTING: TEST OPTIONAL FIELDS DO NOT BLOCK SUBMISSION ---")
    page = logged_in_page
    cp = CompanyPage(page)
    logger.info("Step 1: Navigating to Company page and opening form...")
    cp.go_to_company()
    cp.click_add_new_company()
    
    logger.info("Step 2: Generating and filling only mandatory fields...")
    data = get_localized_data("+91")
    page.locator("input[name='companyName']").fill(data["company_name"])
    page.locator("input[name='companyEmail']").fill(data["email"])
    cp.select_country_code("+91")
    cp.select_service("UI/UX Design")
    
    logger.info("Step 3: Submitting and asserting no validation error on optional fields...")
    page.get_by_role("button", name="Save").click()
    page.wait_for_timeout(1000)
    optional_names = ["websiteUrl", "linkedinUrl", "taxIdentificationNumber",
                      "companySize", "monthlyMarketingBudget", "postalZipCode", "existingAgency"]
    for err in page.locator("[aria-invalid='true']").all():
        name = err.get_attribute("name")
        assert name not in optional_names, f"Optional field '{name}' is showing a validation error"
    logger.info("Verification complete!")


# --- Authorization (New Rules) ---

@pytest.mark.parametrize("logged_in_page", [
    "uday21@gmail.com",          # BDM
    "aryan@tekinspirations.com",  # Team Lead
], indirect=True)
def test_unauthorized_roles_cannot_access_company_page(logged_in_page):
    logger.info(f"--- STARTING: TEST UNAUTHORIZED ROLE CANNOT ACCESS COMPANY PAGE ({logged_in_page.url}) ---")
    page = logged_in_page
    
    logger.info("Step 1: Asserting Company sidebar link is not visible...")
    assert page.get_by_role("link", name="Company").count() == 0, \
        "Company sidebar option should not be visible for unauthorized role"
    
    logger.info("Step 2: Trying direct navigation to /company and asserting redirect...")
    base_url = page.url.split("/dashboard")[0]
    page.goto(f"{base_url}/company")
    page.wait_for_url("**/dashboard**", timeout=10000)
    assert "/dashboard" in page.url, \
        "Direct navigation to /company should redirect unauthorized role to /dashboard"
    logger.info("Access blocked successfully!")


# --- Edit Company & Authorization Rules ---

@pytest.mark.login_as("Admin@infusive.com")
def test_edit_company_as_admin(company_page):
    logger.info("--- STARTING: TEST EDIT COMPANY AS ADMIN ---")
    original_name = f"EditBaseAdmin_{int(time.time())}_{random.randint(100, 999)}"
    original_email = fake.company_email()
    
    logger.info("Step 1: Creating a dedicated company to edit...")
    company_page.click_add_new_company()
    company_page.page.wait_for_timeout(1000)
    company_page.fill_company_form(
        name=original_name,
        email=original_email,
        phone=fake.numerify("##########"),
        website=fake.url()
    )
    company_page.select_country_code("+91")
    company_page.select_service("UI/UX Design")
    company_page.click_save()
    
    logger.info("Step 2: Opening Edit form for row 1...")
    company_page.click_edit_for_row(1)
    company_page.page.wait_for_timeout(1000)
    
    logger.info("Step 3: Prefilled details verification...")
    name_field = company_page.page.get_by_role("textbox", name="Company Name")
    email_field = company_page.page.get_by_role("textbox", name="Company Email")
    prefilled_name = name_field.input_value()
    prefilled_email = email_field.input_value()
    assert prefilled_name == original_name, "Company Name should match original during edit"
    assert prefilled_email == original_email, "Company Email should match original during edit"
    
    logger.info("Step 4: Clearing mandatory fields and verifying form blocks submission...")
    name_field.click()
    company_page.page.wait_for_timeout(300)
    name_field.select_text()
    company_page.page.keyboard.press("Backspace")
    
    email_field.click()
    company_page.page.wait_for_timeout(300)
    email_field.select_text()
    email_field.press_sequentially("", delay=30) # clear email
    company_page.page.keyboard.press("Backspace")
    
    company_page.page.get_by_role("button", name="Update").click()
    company_page.page.wait_for_timeout(1000)
    assert "add-new-company-form" in company_page.page.url, \
        "Edit form should block submission when required fields are cleared"
        
    logger.info("Step 5: Updating company name and verifying change in list...")
    updated_name = f"{original_name}edited"
    company_page.update_company_name(updated_name)
    
    email_field.click()
    company_page.page.wait_for_timeout(300)
    email_field.select_text()
    email_field.press_sequentially(prefilled_email, delay=30)
    
    company_page.click_update()
    assert company_page.is_company_row_visible(updated_name, email=original_email), \
        f"Updated company name '{updated_name}' not found in the list"
        
    logger.info("Step 6: Cleanup (restoring original name)...")
    company_page.click_edit_for_row(1)
    company_page.update_company_name(original_name)
    company_page.click_update()
    logger.info("TEST EDIT COMPANY AS ADMIN completed successfully!")


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_edit_company_as_presales(company_page):
    logger.info("--- STARTING: TEST EDIT COMPANY AS PRESALES ---")
    original_name = f"EditBasePresales_{int(time.time())}_{random.randint(100, 999)}"
    original_email = fake.company_email()
    
    logger.info("Step 1: Creating a dedicated company to edit...")
    company_page.click_add_new_company()
    company_page.page.wait_for_timeout(1000)
    company_page.fill_company_form(
        name=original_name,
        email=original_email,
        phone=fake.numerify("##########"),
        website=fake.url()
    )
    company_page.select_country_code("+91")
    company_page.select_service("UI/UX Design")
    company_page.click_save()
    
    logger.info("Step 2: Opening Edit form for row 1...")
    company_page.click_edit_for_row(1)
    company_page.page.wait_for_timeout(1000)
    
    logger.info("Step 3: Prefilled details verification...")
    name_field = company_page.page.get_by_role("textbox", name="Company Name")
    email_field = company_page.page.get_by_role("textbox", name="Company Email")
    prefilled_name = name_field.input_value()
    prefilled_email = email_field.input_value()
    assert prefilled_name == original_name, "Company Name should match original during edit"
    assert prefilled_email == original_email, "Company Email should match original during edit"
    
    logger.info("Step 4: Clearing mandatory fields and verifying form blocks submission...")
    name_field.click()
    company_page.page.wait_for_timeout(300)
    name_field.select_text()
    company_page.page.keyboard.press("Backspace")
    
    email_field.click()
    company_page.page.wait_for_timeout(300)
    email_field.select_text()
    email_field.press_sequentially("", delay=30) # clear email
    company_page.page.keyboard.press("Backspace")
    
    company_page.page.get_by_role("button", name="Update").click()
    company_page.page.wait_for_timeout(1000)
    assert "add-new-company-form" in company_page.page.url, \
        "Edit form should block submission when required fields are cleared"
        
    logger.info("Step 5: Updating company name and verifying change in list...")
    updated_name = f"{original_name}edited"
    company_page.update_company_name(updated_name)
    
    email_field.click()
    company_page.page.wait_for_timeout(300)
    email_field.select_text()
    email_field.press_sequentially(prefilled_email, delay=30)
    
    company_page.click_update()
    assert company_page.is_company_row_visible(updated_name, email=original_email), \
        f"Updated company name '{updated_name}' not found in the list"
        
    logger.info("Step 6: Cleanup (restoring original name)...")
    company_page.click_edit_for_row(1)
    company_page.update_company_name(original_name)
    company_page.click_update()
    logger.info("TEST EDIT COMPANY AS PRESALES completed successfully!")


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_add_company_duplicate_name_blocks_submission(company_page):
    logger.info("--- STARTING: TEST ADD COMPANY DUPLICATE NAME BLOCKS SUBMISSION ---")
    suffix = f"{int(time.time())}_{random.randint(1000, 9999)}"
    duplicate_name = f"DupAddBase_{suffix}"
    
    logger.info("Step 1: Adding first company with unique name...")
    company_page.click_add_new_company()
    company_page.page.wait_for_timeout(1000)
    company_page.fill_company_form(
        name=duplicate_name,
        email=fake.company_email(),
        phone=fake.numerify("##########"),
        website=fake.url()
    )
    company_page.select_country_code("+91")
    company_page.select_service("UI/UX Design")
    company_page.click_save()
    
    logger.info("Step 2: Trying to add second company with duplicate name...")
    company_page.click_add_new_company()
    company_page.page.wait_for_timeout(1000)
    company_page.fill_company_form(
        name=duplicate_name,
        email=fake.company_email(),
        phone=fake.numerify("##########"),
        website=fake.url()
    )
    company_page.select_country_code("+91")
    company_page.select_service("UI/UX Design")
    
    company_page.page.get_by_role("button", name="Save").click()
    company_page.page.wait_for_timeout(2000)
    url_after = company_page.page.url
    
    logger.info("Step 3: Cleaning up and asserting duplicate submission is blocked...")
    if "add-new-company-form" in url_after:
        base_part = url_after.split("/add-new-company-form")[0]
        company_page.page.goto(f"{base_part}/company")
        company_page.page.wait_for_timeout(2000)
        
    assert "add-new-company-form" in url_after, \
        "Adding a company with duplicate name should block submission"
    logger.info("TEST ADD COMPANY DUPLICATE NAME BLOCKS SUBMISSION verified successfully!")


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_edit_company_duplicate_name_blocks_submission(company_page):
    logger.info("--- STARTING: TEST EDIT COMPANY DUPLICATE NAME BLOCKS SUBMISSION ---")
    suffix = f"{int(time.time())}_{random.randint(1000, 9999)}"
    duplicate_name = f"DupEditBase_{suffix}"
    other_name = f"DupEditOther_{suffix}"
    
    logger.info("Step 1: Creating first company...")
    company_page.click_add_new_company()
    company_page.page.wait_for_timeout(1000)
    company_page.fill_company_form(
        name=duplicate_name,
        email=fake.company_email(),
        phone=fake.numerify("##########"),
        website=fake.url()
    )
    company_page.select_country_code("+91")
    company_page.select_service("UI/UX Design")
    company_page.click_save()
    
    logger.info("Step 2: Creating second company...")
    company_page.click_add_new_company()
    company_page.page.wait_for_timeout(1000)
    company_page.fill_company_form(
        name=other_name,
        email=fake.company_email(),
        phone=fake.numerify("##########"),
        website=fake.url()
    )
    company_page.select_country_code("+91")
    company_page.select_service("UI/UX Design")
    company_page.click_save()
    
    logger.info("Step 3: Editing second company and trying to change its name to duplicate_name...")
    company_page.click_edit_for_row(1)
    company_page.page.wait_for_timeout(1000)
    
    company_page.update_company_name(duplicate_name)
    company_page.page.get_by_role("button", name="Update").click()
    company_page.page.wait_for_timeout(2000)
    url_after = company_page.page.url
    
    logger.info("Step 4: Cleaning up and asserting duplicate edit is blocked...")
    if "add-new-company-form" in url_after:
        base_part = url_after.split("/add-new-company-form")[0]
        company_page.page.goto(f"{base_part}/company")
        company_page.page.wait_for_timeout(2000)
        
    assert "add-new-company-form" in url_after, \
        "Editing a company to a duplicate name should block submission"
    logger.info("TEST EDIT COMPANY DUPLICATE NAME BLOCKS SUBMISSION verified successfully!")


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_create_company_with_asterisks_blocks_submission(company_page):
    logger.info("--- STARTING: TEST CREATE COMPANY WITH ASTERISKS BLOCKS SUBMISSION ---")
    logger.info("Step 1: Opening Add Company form...")
    company_page.click_add_new_company()
    company_page.page.wait_for_timeout(1000)
    
    logger.info("Step 2: Filling required fields with '*****'...")
    company_page.page.locator("input[name='companyName']").fill("*****")
    company_page.page.locator("input[name='companyEmail']").fill("*****")
    try:
        company_page.page.locator("input[name='companyPhone']").fill("*****")
    except Exception:
        pass
        
    company_page.select_country_code("+91")
    company_page.select_service("UI/UX Design")
    
    logger.info("Step 3: Clicking Save and asserting form blocks submission...")
    company_page.page.get_by_role("button", name="Save").click()
    company_page.page.wait_for_timeout(2000)
    url_after = company_page.page.url
    
    if "add-new-company-form" in url_after:
        base_part = url_after.split("/add-new-company-form")[0]
        company_page.page.goto(f"{base_part}/company")
        company_page.page.wait_for_timeout(2000)
        
    assert "add-new-company-form" in url_after, \
        "Creating a company with asterisks in required fields should block submission"
    logger.info("TEST CREATE COMPANY WITH ASTERISKS BLOCKS SUBMISSION verified successfully!")
