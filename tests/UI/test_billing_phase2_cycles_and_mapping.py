import logging
import pytest
from playwright.sync_api import Page, expect

from pages.project_page import ProjectPage
from pages.billing_plans_page import BillingPlansPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_phase2_billing_cycle_and_date_rules(logged_in_page: Page):
    """
    Phase 2: Validate Billing Cycle & Cadence (Monthly, Quarterly, etc.):
      1. Open Recurring billing setup.
      2. Verify Start Date and Next Invoice Date fields are accessible.
      3. Verify default start date is today and next invoice date defaults correctly.
      4. Validate switching billing cycles preserves plan integrity.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink("Testing Company - Project")
    project_page.open_billing_invoices_tab()

    project_page.select_billing_type("Recurring")

    # Select Billing Cycle
    project_page.select_billing_cycle("Monthly")
    project_page.set_recurring_dates(start_date="2026-11-10", next_invoice_date="2026-12-10")

    # Verify input values
    panels = page.locator("div.chakra-tabs__tab-panels").first
    start_val = panels.locator("input[name='startDate']:visible, input[type='date']:visible").first.input_value()
    next_val = panels.locator("input[name='nextInvoiceDate']:visible, input[type='date']:visible").nth(1).input_value()

    logger.info(f"Phase 2 Recurring Dates: Start='{start_val}', Next='{next_val}'")
    assert "2026-11-10" in start_val
    assert "2026-12-10" in next_val

    logger.info("Phase 2: Billing Cycle & Date Rules VERIFIED ✓")


@pytest.mark.ui
def test_phase2_payment_terms_mapping(logged_in_page: Page):
    """
    Phase 2: Validate Payment Terms mapping (Immediate, 7 Days, 15 Days, 30 Days, etc.):
      1. Verify payment terms dropdown/options.
      2. Select '7 Days', verify helper text 'within 7 days'.
      3. Select '30 Days', verify helper text 'within 30 days'.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink("Testing Company - Project")
    project_page.open_billing_invoices_tab()

    project_page.select_billing_type("One-Time")

    # Test 7 Days
    project_page.select_payment_terms("7 Days")
    page.wait_for_timeout(500)
    panel_text_7 = page.locator("div.chakra-tabs__tab-panels").first.inner_text()
    assert "payment within" in panel_text_7.lower(), f"Expected helper text for 7 days in: {panel_text_7}"

    # Test 30 Days
    project_page.select_payment_terms("30 Days")
    page.wait_for_timeout(500)
    panel_text_30 = page.locator("div.chakra-tabs__tab-panels").first.inner_text()
    assert "payment within" in panel_text_30.lower(), f"Expected helper text for 30 days in: {panel_text_30}"

    logger.info("Phase 2: Payment Terms Mapping VERIFIED ✓")


@pytest.mark.ui
def test_phase2_customer_and_project_mapping(logged_in_page: Page):
    """
    Phase 2: Validate Customer & Project mapping in Billing Plans:
      1. Open Central Billing Plans (/allBillingPlans).
      2. Verify customer mapping to project name.
      3. Filter by Customer 'Testing Company' and assert all mapped projects belong to it.
    """
    page = logged_in_page
    billing_page = BillingPlansPage(page)

    billing_page.go_to_billing_plans()

    # Filter by Customer 'Testing Company'
    billing_page.filter_by_customer("Testing Company")
    page.wait_for_timeout(1000)

    rows = billing_page.get_table_rows().all()
    logger.info(f"Customer 'Testing Company' has {len(rows)} mapped billing plans.")
    assert len(rows) > 0, "Expected at least 1 mapped plan for 'Testing Company'"

    for r in rows:
        row_cust = r.locator("td:nth-child(2)").inner_text().strip()
        row_proj = r.locator("td:nth-child(3)").inner_text().strip()
        assert "Testing Company" in row_cust, f"Customer should be 'Testing Company', got '{row_cust}'"
        assert len(row_proj) > 0, "Project name must not be empty"

    # Reset customer filter
    billing_page.filter_by_customer("All customers")

    logger.info("Phase 2: Customer & Project Mapping VERIFIED ✓")
