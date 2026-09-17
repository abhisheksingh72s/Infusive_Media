import pytest
import time
import random
import logging
from faker import Faker
from pages.agency_page import AgencyPage

logger = logging.getLogger(__name__)
fake = Faker("en_US")

@pytest.fixture
def agency_page(logged_in_page):
    """Fixture initializing AgencyPage after UI login."""
    ap = AgencyPage(logged_in_page)
    return ap

@pytest.mark.login_as("Admin@infusive.com")
def test_add_new_agency(agency_page):
    """
    Test Case: Add New Agency
    Module: Master
    Sub-module: Agency

    Steps:
      1. Login via Admin (Admin@infusive.com).
      2. Click Master module.
      3. Click Agency sub-module.
      4. Verify Agency listing/table is displayed.
      5. Click Add Options button.
      6. Select Add New Agency.
      7. Verify Add New Agency form is displayed.
      8. Fill all mandatory fields (Agency Name, Phone Country Code, Agency Phone Number, Country).
      9. Click Save Agency.
      10. Verify agency is successfully created in the Agency listing table (after refresh & search).
    """
    logger.info("==========================================================================")
    logger.info("STARTING TEST: Add New Agency (Master -> Agency)")
    logger.info("==========================================================================")

    # Step 1: Login via Admin (handled by @pytest.mark.login_as("Admin@infusive.com"))
    logger.info("Step 1: Authenticated with Admin user.")

    # Step 2, 3, 4: Navigate to Master -> Agency and verify listing table is displayed
    logger.info("Step 2-4: Navigating to Master -> Agency sub-module...")
    agency_page.go_to_agency()

    # Step 5: Click Add Options button
    logger.info("Step 5: Clicking Add Options button...")
    agency_page.click_add_options()

    # Step 6: Select Add New Agency
    logger.info("Step 6: Selecting 'Add New Agency' option...")
    agency_page.select_add_new_agency()

    # Step 7: Verify Add New Agency form is displayed
    logger.info("Step 7: Verifying Add New Agency form is displayed...")
    assert agency_page.is_add_agency_form_visible(), "Add New Agency form should be displayed"

    # Step 8: Fill all mandatory fields with realistic agency name
    real_agency_names = [
        "Apex Global Agency",
        "Horizon Media Agency",
        "Pinnacle Digital Agency",
        "Summit Creative Agency",
        "Vanguard Marketing Agency",
        "Nexus Brand Agency",
        "Elevation Interactive Agency",
        "Quantum Reach Agency",
        "Starlight Media Agency",
        "Beacon Strategic Agency"
    ]
    base_name = random.choice(real_agency_names)
    suffix = str(int(time.time()))[-4:]
    agency_name = f"{base_name} {suffix}"
    phone_number = fake.numerify("##########")
    logger.info(f"Step 8: Filling mandatory fields for realistic Agency '{agency_name}'...")
    agency_page.fill_agency_form(
        agency_name=agency_name,
        phone=phone_number,
        country_code="+1",
        country="United States"
    )

    # Step 9: Click Save Agency
    logger.info("Step 9: Clicking Save Agency button...")
    agency_page.click_save_agency()

    # Capture initial creation toast
    toast_text = agency_page.capture_toast()
    logger.info(f"Creation toast returned: '{toast_text}'")

    # Step 10: Refresh page and search for the created agency record
    logger.info("Step 10: Reloading page and searching for created agency record...")
    agency_page.reload_page()
    agency_page.search_agency(agency_name)

    is_found = agency_page.is_agency_visible_in_table(agency_name)
    assert is_found, f"Newly created agency '{agency_name}' should be displayed in search results after page refresh."

    # Step 11: Click action column '+' button on the searched agency record
    logger.info("Step 11: Clicking action column '+' button for the created agency record...")
    agency_page.click_action_plus_button(agency_name)

    # Step 12: Click 'Add Agency POC' button
    logger.info("Step 12: Clicking 'Add Agency POC' button...")
    agency_page.click_add_agency_poc()

    # Step 13: Fill Agency POC form
    poc_name = fake.name()
    poc_email = fake.email()
    poc_phone = fake.numerify("##########")
    logger.info(f"Step 13: Filling Agency POC form: Name='{poc_name}', Email='{poc_email}', Phone='{poc_phone}'...")
    agency_page.fill_agency_poc_form(
        poc_name=poc_name,
        poc_email=poc_email,
        poc_phone=poc_phone,
        country_code="+1",
        designation="Manager"
    )

    # Step 14: Save Agency POC
    logger.info("Step 14: Clicking Save POC button...")
    agency_page.click_save_poc()

    poc_toast = agency_page.capture_toast()
    logger.info(f"POC Creation toast returned: '{poc_toast}'")

    logger.info("==========================================================================")
    logger.info("TEST ADD NEW AGENCY & AGENCY POC COMPLETED SUCCESSFULLY!")
    logger.info("==========================================================================")
