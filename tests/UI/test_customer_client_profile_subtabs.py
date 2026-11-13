"""
Customer Details: Client Profile Sub-Tabs Comprehensive Validation Test
======================================================================
Module: Customers (/customers -> /customers/{id})
Sub-Tabs under Client Profile:
  1. Basic Information (Name, Industry, Website, Phone, Email, Status, Description)
  2. Billing Address (Same as Reg checkbox, Address 1 & 2, Country, State, City, Postal, Place of Supply)
  3. Tax & GST Details (Country, Currency auto-derivation, Tax Registration radio, Tax IDs)
"""

import os
import pathlib
import pytest
from playwright.sync_api import Page, expect

from pages.login_page import LoginPage
from pages.customer_page import CustomerPage


@pytest.mark.ui
@pytest.mark.regression
def test_customer_client_profile_all_three_subtabs(page: Page):
    """
    Validates the 3 sub-tabs under /customers/{id} -> Client Profile:
      - Sub-tab 1: Basic Information
      - Sub-tab 2: Billing Address
      - Sub-tab 3: Tax & GST Details (including disabled auto-derived Currency)
    """
    shots_dir = pathlib.Path("screenshots")
    shots_dir.mkdir(exist_ok=True)

    login_page = LoginPage(page)
    customer_page = CustomerPage(page)

    admin_email = os.environ.get("EMAIL")
    admin_pass = os.environ.get("PASSWORD")
    assert admin_email and admin_pass, "Admin credentials must be provided in .env."

    # 1. Login
    login_page.load()
    login_page.login(admin_email, admin_pass)
    login_page.wait_for_dashboard()

    # 2. Go to Customers and open first active customer profile
    customer_page.go_to_customers()
    page.wait_for_timeout(1500)

    # Click view details on first customer
    customer_page.click_view_customer_details()
    page.wait_for_timeout(1500)
    assert "/customers/" in page.url, f"Expected URL to contain '/customers/', got '{page.url}'"

    # 3. Switch to Main Tab 4: Client Profile
    customer_page.switch_to_customer_tab("Client Profile")
    page.wait_for_timeout(1000)

    # -------------------------------------------------------------------------
    # SUB-TAB 1: Basic Information
    # -------------------------------------------------------------------------
    customer_page.switch_to_client_profile_subtab("Basic Information")
    page.wait_for_timeout(800)

    basic_data = customer_page.get_basic_information()
    print(f"\n[SUB-TAB 1: Basic Information] Extracted Data: {basic_data}")
    assert basic_data["client_name"], "Client Name must not be empty!"
    assert basic_data["email"], "Client Email must not be empty!"

    save_basic_btn = page.locator("button:has-text('Save Basic Information')").first
    assert save_basic_btn.is_visible(), "'Save Basic Information' button must be visible."
    page.screenshot(path=str(shots_dir / "customer_subtab1_basic_info.png"))

    # -------------------------------------------------------------------------
    # SUB-TAB 2: Billing Address
    # -------------------------------------------------------------------------
    customer_page.switch_to_client_profile_subtab("Billing Address")
    page.wait_for_timeout(800)

    billing_data = customer_page.get_billing_address_data()
    print(f"[SUB-TAB 2: Billing Address] Extracted Data: {billing_data}")
    assert billing_data["country"], "Billing Address Country must not be empty!"
    assert billing_data["address_line_1"], "Address Line 1 must not be empty!"

    # Assert Place of Supply is visible
    pos_elem = page.locator("div:has-text('Place of Supply (For Tax Purposes)')").first
    assert pos_elem.is_visible(), "'Place of Supply' section must be visible in Billing Address!"

    save_addr_btn = page.locator("button:has-text('Save Billing Address')").first
    assert save_addr_btn.is_visible(), "'Save Billing Address' button must be visible."
    page.screenshot(path=str(shots_dir / "customer_subtab2_billing_address.png"))

    # -------------------------------------------------------------------------
    # SUB-TAB 3: Tax & GST Details
    # -------------------------------------------------------------------------
    customer_page.switch_to_client_profile_subtab("Tax & GST Details")
    page.wait_for_timeout(800)

    tax_data = customer_page.get_tax_gst_details_data()
    print(f"[SUB-TAB 3: Tax & GST Details] Extracted Data: {tax_data}")
    assert tax_data["country"], "Tax Country must not be empty!"
    assert tax_data["currency"], "Tax Currency must not be empty!"

    # Core Business Rule Assertion: Currency is disabled and auto-derived
    assert tax_data["is_currency_disabled"], (
        "BUSINESS RULE VIOLATION: Currency in Tax & GST Details must be disabled (auto-derived from country)!"
    )

    helper_text = page.locator("text='Set automatically from the billing country'").first
    assert helper_text.is_visible(), "Expected helper note 'Set automatically from the billing country' to be visible."

    # Assert Tax Registration Radios (Yes, No, Not Sure)
    for opt in ["yes", "no", "not_sure"]:
        radio = page.locator(f"input[type='radio'][value='{opt}']").first
        assert radio.count() > 0, f"Tax registration radio '{opt}' must exist!"

    # Assert Common Tax ID Types Reference card is present
    tax_types_card = page.locator("text='Common Tax ID Types by Country'").first
    assert tax_types_card.is_visible(), "Expected 'Common Tax ID Types by Country' reference card."

    save_tax_btn = page.locator("button:has-text('Save Tax & GST Details')").first
    assert save_tax_btn.is_visible(), "'Save Tax & GST Details' button must be visible."
    page.screenshot(path=str(shots_dir / "customer_subtab3_tax_gst_details.png"))

    print("\n[ALL 3 SUB-TABS VERIFIED SUCCESSFULLY ✓]")
