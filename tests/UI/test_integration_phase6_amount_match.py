import logging
import pytest
from playwright.sync_api import Page, expect

from pages.billing_plans_page import BillingPlansPage
from pages.invoice_page import InvoicePage
from workflows.billing_invoice_workflow import BillingInvoiceWorkflow

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_phase6_billing_plan_amount_matches_invoice_amount(logged_in_page: Page):
    """
    Phase 6: Integration - Verify Billing Amount Matches Invoice Amount:
      1. Fetch first active Billing Plan from /allBillingPlans.
      2. Record its Project name, Customer name, and 'Amount (with GST)'.
      3. Navigate to Invoices module (/invoice-list-page) and search by that Project name.
      4. Compare the Invoice Amount (INR or USD) with the Billing Plan Amount.
      5. Assert mathematical and financial amount parity.
    """
    page = logged_in_page
    workflow = BillingInvoiceWorkflow(page)
    billing_page = BillingPlansPage(page)
    invoice_page = InvoicePage(page)

    # 1. Get Billing Plan Data
    billing_page.go_to_billing_plans()
    plan_data = billing_page.get_plan_row_data(0)
    project_name = plan_data["project"]
    plan_amount_raw = plan_data["amount_with_gst"]
    logger.info(f"Target Billing Plan: Project='{project_name}', Plan Amount='{plan_amount_raw}'")

    # 2. Get Corresponding Invoice Data
    invoice_page.go_to_invoices()
    invoice_page.search_invoices(project_name)
    page.wait_for_timeout(1000)

    rows = invoice_page.get_table_rows()
    assert rows.count() > 0, f"Expected at least 1 invoice matching project '{project_name}'"

    inv_data = invoice_page.get_invoice_row_data(0)
    logger.info(f"Matched Invoice: No='{inv_data['invoice_no']}', INR='{inv_data['amount_inr']}', USD='{inv_data['amount_usd']}'")

    # 3. Assert Amount Match
    matched = workflow.verify_billing_amount_matches_invoice(
        billing_plan_project=project_name,
        invoice_no=inv_data["invoice_no"],
    )
    assert matched is True, (
        f"Billing plan amount '{plan_amount_raw}' did not match invoice amounts: "
        f"INR='{inv_data['amount_inr']}', USD='{inv_data['amount_usd']}'"
    )

    logger.info("Phase 6: Billing Amount Matches Invoice Amount VERIFIED ✓")
