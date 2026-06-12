import pytest
import time
import random
from faker import Faker
from pages.company_page import CompanyPage

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
    company_name = f"{fk.company()}_{int(time.time())}_{random.randint(100, 999)}"
    company_name = company_name.replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("'", "").replace(",", "")
    poc_name = fk.name().replace("'", "").replace(",", "")
    phone = fk.numerify("##########")
    return {
        "company_name": company_name,
        "poc_name": poc_name,
        "phone": phone,
        "email": fk.company_email(),
        "poc_email": fk.email(),
    }


@pytest.fixture
def company_page(logged_in_page):
    cp = CompanyPage(logged_in_page)
    cp.go_to_company()
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
        "poc_name": data["poc_name"],
        "poc_email": data["poc_email"],
        "poc_phone": data["phone"]
    }


# --- Table ---

@pytest.mark.login_as("shreya@tekinspirations.com")
def test_company_table_visible(company_page):
    company_page.page.locator("tbody tr").first.wait_for(state="visible", timeout=15000)
    company_page.page.wait_for_timeout(1000)
    assert company_page.page.locator("tbody tr").count() > 0


# --- Add ---

@pytest.mark.login_as("shreya@tekinspirations.com")
def test_add_new_company(company_page):
    country_code = random.choice(["+91", "+1", "+44", "+61"])
    data = get_localized_data(country_code)
    company_name = data["company_name"]
    
    company_page.click_add_new_company()
    company_page.fill_company_form(
        name=company_name,
        email=data["email"],
        phone=data["phone"],
        website=fake.url()
    )
    company_page.select_country_code(country_code)
    company_page.select_service("UI/UX Design")
    company_page.click_save()
    assert company_page.is_company_row_visible(company_name), \
        f"Company '{company_name}' not found after creation"


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_add_new_company_and_poc(new_company):
    company_page = new_company["page"]
    company_name = new_company["name"]
    poc_name = new_company["poc_name"]
    poc_email = new_company["poc_email"]
    poc_phone = new_company["poc_phone"]
    
    company_page.fill_poc_form(
        name=poc_name,
        email=poc_email,
        designation="HR.",
        phone=poc_phone,
        whatsapp=poc_phone,
        linkedin=fake.url()
    )
    company_page.click_save()
    assert company_page.is_company_row_visible(company_name), \
        f"Company '{company_name}' not found after creation"


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
    cp = CompanyPage(logged_in_page)
    cp.go_to_company()
    cp.click_add_new_company()
    fill_fn(logged_in_page, cp)
    logged_in_page.get_by_role("button", name="Save").click()
    logged_in_page.wait_for_timeout(500)
    assert "company" in logged_in_page.url.lower(), \
        f"Form should block submission when '{skip_field}' is missing"


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_optional_fields_do_not_block_submission(logged_in_page):
    page = logged_in_page
    cp = CompanyPage(page)
    cp.go_to_company()
    cp.click_add_new_company()
    data = get_localized_data("+91")
    page.locator("input[name='companyName']").fill(data["company_name"])
    page.locator("input[name='companyEmail']").fill(data["email"])
    cp.select_country_code("+91")
    cp.select_service("UI/UX Design")
    # leave all optional fields empty
    page.get_by_role("button", name="Save").click()
    page.wait_for_timeout(1000)
    optional_names = ["websiteUrl", "linkedinUrl", "taxIdentificationNumber",
                      "companySize", "monthlyMarketingBudget", "postalZipCode", "existingAgency"]
    for err in page.locator("[aria-invalid='true']").all():
        name = err.get_attribute("name")
        assert name not in optional_names, f"Optional field '{name}' is showing a validation error"


# --- Authorization (New Rules) ---

@pytest.mark.parametrize("logged_in_page", [
    "uday21@gmail.com",          # BDM
    "aryan@tekinspirations.com",  # Team Lead
], indirect=True)
def test_unauthorized_roles_cannot_access_company_page(logged_in_page):
    page = logged_in_page
    
    # Verify Company sidebar link is not visible
    assert page.get_by_role("link", name="Company").count() == 0, \
        "Company sidebar option should not be visible for unauthorized role"
    
    # Verify direct navigation redirects back to dashboard
    base_url = page.url.split("/dashboard")[0]
    page.goto(f"{base_url}/company")
    page.wait_for_url("**/dashboard**", timeout=10000)
    assert "/dashboard" in page.url, \
        "Direct navigation to /company should redirect unauthorized role to /dashboard"


# --- Edit Company & Authorization Rules ---

@pytest.mark.login_as("Admin@infusive.com")
def test_edit_company_as_admin(company_page):
    import time
    import random
    original_name = f"EditBaseAdmin_{int(time.time())}_{random.randint(100, 999)}"
    original_email = fake.company_email()
    
    # 1. Create a dedicated company to edit
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
    
    # Click Edit for row 1
    company_page.click_edit_for_row(1)
    company_page.page.wait_for_timeout(1000)
    
    # 1. Verify that the form has prefilled data
    name_field = company_page.page.get_by_role("textbox", name="Company Name")
    email_field = company_page.page.get_by_role("textbox", name="Company Email")
    prefilled_name = name_field.input_value()
    prefilled_email = email_field.input_value()
    assert prefilled_name == original_name, "Company Name should match original during edit"
    assert prefilled_email == original_email, "Company Email should match original during edit"
    
    # 2. Clear mandatory fields and verify form blocks submission
    name_field.click()
    company_page.page.wait_for_timeout(300)
    name_field.select_text()
    company_page.page.keyboard.press("Backspace")
    
    email_field.click()
    company_page.page.wait_for_timeout(300)
    email_field.select_text()
    company_page.page.keyboard.press("Backspace")
    
    company_page.page.get_by_role("button", name="Update").click()
    company_page.page.wait_for_timeout(1000)
    assert "add-new-company-form" in company_page.page.url, \
        "Edit form should block submission when required fields are cleared"
        
    # Re-fill the form with a new unique name and the original email to complete edit test
    updated_name = f"{original_name}edited"
    company_page.update_company_name(updated_name)
    
    email_field.click()
    company_page.page.wait_for_timeout(300)
    email_field.select_text()
    email_field.press_sequentially(prefilled_email, delay=30)
    
    # Click Update
    company_page.click_update()
    
    # Verify that the updated company name is visible in the table
    assert company_page.is_company_row_visible(updated_name), \
        f"Updated company name '{updated_name}' not found in the list"
        
    # Cleanup: Edit it back to its original name to keep tests stateless
    company_page.click_edit_for_row(1)
    company_page.update_company_name(original_name)
    company_page.click_update()


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_edit_company_as_presales(company_page):
    import time
    import random
    original_name = f"EditBasePresales_{int(time.time())}_{random.randint(100, 999)}"
    original_email = fake.company_email()
    
    # 1. Create a dedicated company to edit
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
    
    # Click Edit for row 1
    company_page.click_edit_for_row(1)
    company_page.page.wait_for_timeout(1000)
    
    # 1. Verify that the form has prefilled data
    name_field = company_page.page.get_by_role("textbox", name="Company Name")
    email_field = company_page.page.get_by_role("textbox", name="Company Email")
    prefilled_name = name_field.input_value()
    prefilled_email = email_field.input_value()
    assert prefilled_name == original_name, "Company Name should match original during edit"
    assert prefilled_email == original_email, "Company Email should match original during edit"
    
    # 2. Clear mandatory fields and verify form blocks submission
    name_field.click()
    company_page.page.wait_for_timeout(300)
    name_field.select_text()
    company_page.page.keyboard.press("Backspace")
    
    email_field.click()
    company_page.page.wait_for_timeout(300)
    email_field.select_text()
    company_page.page.keyboard.press("Backspace")
    
    company_page.page.get_by_role("button", name="Update").click()
    company_page.page.wait_for_timeout(1000)
    assert "add-new-company-form" in company_page.page.url, \
        "Edit form should block submission when required fields are cleared"
        
    # Re-fill the form with a new unique name and the original email to complete edit test
    updated_name = f"{original_name}edited"
    company_page.update_company_name(updated_name)
    
    email_field.click()
    company_page.page.wait_for_timeout(300)
    email_field.select_text()
    email_field.press_sequentially(prefilled_email, delay=30)
    
    # Click Update
    company_page.click_update()
    
    # Verify that the updated company name is visible in the table
    assert company_page.is_company_row_visible(updated_name), \
        f"Updated company name '{updated_name}' not found in the list"
        
    # Cleanup: Edit it back to its original name to keep tests stateless
    company_page.click_edit_for_row(1)
    company_page.update_company_name(original_name)
    company_page.click_update()


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_add_company_duplicate_name_blocks_submission(company_page):
    import time
    import random
    suffix = f"{int(time.time())}_{random.randint(1000, 9999)}"
    duplicate_name = f"DupAddBase_{suffix}"
    
    # 1. Add first company with unique name
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
    
    # 2. Try to add second company with duplicate name
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
    
    # Submit and verify it blocks (user remains on the form page)
    company_page.page.get_by_role("button", name="Save").click()
    company_page.page.wait_for_timeout(2000)
    url_after = company_page.page.url
    
    # Clean up form page to go back
    if "add-new-company-form" in url_after:
        base_part = url_after.split("/add-new-company-form")[0]
        company_page.page.goto(f"{base_part}/company")
        company_page.page.wait_for_timeout(2000)
        
    assert "add-new-company-form" in url_after, \
        "Adding a company with duplicate name should block submission"


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_edit_company_duplicate_name_blocks_submission(company_page):
    import time
    import random
    suffix = f"{int(time.time())}_{random.randint(1000, 9999)}"
    duplicate_name = f"DupEditBase_{suffix}"
    other_name = f"DupEditOther_{suffix}"
    
    # 1. Create first company
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
    
    # 2. Create second company
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
    
    # 3. Edit second company (row 1) and try to change its name to first company name (duplicate)
    company_page.click_edit_for_row(1)
    company_page.page.wait_for_timeout(1000)
    
    company_page.update_company_name(duplicate_name)
    company_page.page.get_by_role("button", name="Update").click()
    company_page.page.wait_for_timeout(2000)
    url_after = company_page.page.url
    
    # Clean up form page to go back
    if "add-new-company-form" in url_after:
        base_part = url_after.split("/add-new-company-form")[0]
        company_page.page.goto(f"{base_part}/company")
        company_page.page.wait_for_timeout(2000)
        
    assert "add-new-company-form" in url_after, \
        "Editing a company to a duplicate name should block submission"


@pytest.mark.login_as("shreya@tekinspirations.com")
def test_create_company_with_asterisks_blocks_submission(company_page):
    company_page.click_add_new_company()
    company_page.page.wait_for_timeout(1000)
    
    # Fill companyName and companyEmail with '*****'
    company_page.page.locator("input[name='companyName']").fill("*****")
    company_page.page.locator("input[name='companyEmail']").fill("*****")
    
    # Try filling phone with '*****' (type=number may raise browser block)
    try:
        company_page.page.locator("input[name='companyPhone']").fill("*****")
    except Exception:
        pass
        
    company_page.select_country_code("+91")
    company_page.select_service("UI/UX Design")
    
    # Click Save and verify it blocks submission (keeps user on the form page)
    company_page.page.get_by_role("button", name="Save").click()
    company_page.page.wait_for_timeout(2000)
    url_after = company_page.page.url
    
    # Clean up form page to go back
    if "add-new-company-form" in url_after:
        base_part = url_after.split("/add-new-company-form")[0]
        company_page.page.goto(f"{base_part}/company")
        company_page.page.wait_for_timeout(2000)
        
    assert "add-new-company-form" in url_after, \
        "Creating a company with asterisks in required fields should block submission"


