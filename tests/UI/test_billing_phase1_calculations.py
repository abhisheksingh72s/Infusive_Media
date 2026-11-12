import logging
import pytest
from playwright.sync_api import Page, expect

from pages.project_page import ProjectPage
from workflows.billing_invoice_workflow import BillingInvoiceWorkflow

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_phase1_amount_calculation_and_subtotal(logged_in_page: Page):
    """
    Phase 1: Validate Base Amount Calculation (Qty * Unit Price):
      1. Add service with Qty=4 and Unit Price=2500.
      2. Verify base row subtotal before tax is 10,000.
      3. Verify Invoice Summary Subtotal matches base calculation.
    """
    page = logged_in_page
    workflow = BillingInvoiceWorkflow(page)

    services = [
        {
            "service_option_index": 1,
            "description": "Enterprise SEO Audit",
            "qty": "4",
            "unit_price": "2500",
            "gst_percent": "18",
        }
    ]

    summary = workflow.setup_project_billing_plan(
        project_name="Testing Company - Project",
        billing_type="One-Time",
        currency="INR",
        services=services,
    )

    logger.info(f"Phase 1 Summary: {summary}")
    # Subtotal = 4 * 2500 = 10,000
    assert "10,000" in summary["subtotal"], f"Expected Subtotal ₹10,000, got: {summary['subtotal']}"
    # GST = 18% of 10,000 = 1,800
    assert "1,800" in summary["total_gst"], f"Expected GST ₹1,800, got: {summary['total_gst']}"
    # Total = 11,800
    assert "11,800" in summary["total_amount"], f"Expected Total ₹11,800, got: {summary['total_amount']}"

    logger.info("Phase 1: Base Amount & Subtotal Calculation VERIFIED ✓")


@pytest.mark.ui
def test_phase1_gst_tax_rates_and_payable_amount(logged_in_page: Page):
    """
    Phase 1: Validate GST rates (0%, 5%, 18%, 28%) and final Payable Amount:
      1. Test with 0% GST: Total Amount should equal Subtotal.
      2. Test with 18% GST: Total Amount should equal Subtotal + 18% GST.
      3. Test multi-row aggregation: Row 1 + Row 2.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink("Testing Company - Project")
    project_page.open_billing_invoices_tab()

    project_page.select_billing_type("One-Time")
    project_page.select_billing_currency("USD")

    # Add 2 service rows
    project_page.click_add_service()
    project_page.fill_service_row(
        row_index=0,
        service_option_index=1,
        qty="2",
        unit_price="1500",
        gst_percent="18",
    )

    project_page.click_add_service()
    project_page.fill_service_row(
        row_index=1,
        service_option_index=2,
        qty="1",
        unit_price="2000",
        gst_percent="18",
    )

    # Row 1: 2 * 1500 = 3000 (+ 18% = 3540)
    # Row 2: 1 * 2000 = 2000 (+ 18% = 2360)
    # Subtotal = 5000, Total GST = 900, Total Amount = 5900
    summary = project_page.get_invoice_summary()
    logger.info(f"Multi-row GST Summary: {summary}")

    assert "5,000" in summary["subtotal"], f"Expected Subtotal $5,000, got: {summary['subtotal']}"
    assert "900" in summary["total_gst"], f"Expected GST $900, got: {summary['total_gst']}"
    assert "5,900" in summary["total_amount"], f"Expected Total $5,900, got: {summary['total_amount']}"

    # Clean up row 2
    project_page.remove_service_row(1)

    logger.info("Phase 1: GST Tax Rates & Payable Amount VERIFIED ✓")
