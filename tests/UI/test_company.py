import pytest
from faker import Faker
from pages.company_page import CompanyPage

fake = Faker()


@pytest.fixture
def company_page(logged_in_page):
    cp = CompanyPage(logged_in_page)
    cp.go_to_company()
    return cp


@pytest.fixture
def new_company(company_page):
    company_name = fake.company()
    company_page.click_add_new_company_and_poc()
    company_page.fill_company_form(
        name=company_name,
        email=fake.company_email(),
        phone=fake.numerify("##########"),
        website=fake.url()
    )
    company_page.select_country_code("+91")
    company_page.select_service("UI/UX Design")
    company_page.click_next()
    return {"page": company_page, "name": company_name}


# --- Table ---

def test_company_table_visible(company_page):
    assert company_page.page.locator("tbody tr").count() > 0


# --- Add ---

def test_add_new_company(company_page):
    company_name = fake.company()
    company_page.click_add_new_company()
    company_page.fill_company_form(
        name=company_name,
        email=fake.company_email(),
        phone=fake.numerify("##########"),
        website=fake.url()
    )
    company_page.select_country_code("+91")
    company_page.select_service("UI/UX Design")
    company_page.click_save()
    assert company_page.is_company_row_visible(company_name), \
        f"Company '{company_name}' not found after creation"


def test_add_new_company_and_poc(new_company):
    company_page = new_company["page"]
    company_name = new_company["name"]
    company_page.fill_poc_form(
        name=fake.name(),
        email=fake.email(),
        designation="HR.",
        phone=fake.numerify("##########"),
        whatsapp=fake.numerify("##########"),
        linkedin=fake.url()
    )
    company_page.click_save()
    assert company_page.is_company_row_visible(company_name), \
        f"Company '{company_name}' not found after creation"


# --- Validation ---

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


def test_optional_fields_do_not_block_submission(company_form):
    page = company_form
    cp = CompanyPage(page)
    page.locator("input[name='companyName']").fill(fake.company())
    page.locator("input[name='companyEmail']").fill(fake.company_email())
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
