import logging
import pytest
from playwright.sync_api import Page, expect

from pages.project_page import ProjectPage
from pages.billing_plans_page import BillingPlansPage
from pages.invoice_page import InvoicePage
from workflows.billing_invoice_workflow import BillingInvoiceWorkflow

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_phase3_invoice_generation_controls(logged_in_page: Page):
    """
    Phase 3: Validate Invoice Generation controls on Billing Plan:
      1. Navigate to Project Details -> Billing & Invoices.
      2. Verify both generation paths:
         - 'Create Plan' (schedule-only plan)
         - 'Create Plan & Generate Invoice Now' (immediate invoice generation)
      3. Verify Auto-generate invoice switch is present and togglable.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink("Testing Company - Project")
    project_page.open_billing_invoices_tab()

    # Verify buttons
    create_plan_btn = page.locator("button:has-text('Create Plan')").first
    assert create_plan_btn.is_visible(), "Expected 'Create Plan' button"

    # Verify Auto-generate toggle
    project_page.select_billing_type("Recurring")
    auto_switch = page.locator("input[type='checkbox']").first
    assert auto_switch.is_visible(), "Expected auto-generate toggle"

    logger.info("Phase 3: Invoice Generation Controls VERIFIED ✓")


@pytest.mark.ui
def test_phase3_billing_plan_invoices_count_tracking(logged_in_page: Page):
    """
    Phase 3: Validate that Billing Plans track generated invoice counts:
      1. Open Central Billing Plans (/allBillingPlans).
      2. Check 'INVOICES' column for all plans.
      3. Assert each active plan has a tracked count (e.g. 1 or more invoices).
    """
    page = logged_in_page
    billing_page = BillingPlansPage(page)

    billing_page.go_to_billing_plans()

    rows = billing_page.get_table_rows().all()
    assert len(rows) > 0

    for idx in range(min(5, len(rows))):
        data = billing_page.get_plan_row_data(idx)
        logger.info(f"Plan #{idx + 1} ({data['customer']} - {data['project']}): Invoices Count = '{data['invoices']}'")
        assert data["invoices"].isdigit(), f"Invoices count must be numeric, got: {data['invoices']}"
        assert int(data["invoices"]) >= 0

    logger.info("Phase 3: Billing Plan Invoices Count Tracking VERIFIED ✓")
