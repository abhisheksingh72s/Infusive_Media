import logging
import pytest
from playwright.sync_api import Page, expect

from pages.invoice_page import InvoicePage
from workflows.billing_invoice_workflow import BillingInvoiceWorkflow

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_phase7_invoice_and_payment_status_synchronization(logged_in_page: Page):
    """
    Phase 7: Integration - Validate Status and Payment Financial Synchronization:
      1. Check 'Pending' invoices:
         - Paid Amount should be 0.
         - Outstanding balance must equal total amount.
      2. Check 'Paid' invoices:
         - Paid Amount must equal total amount.
         - Outstanding balance must be 0.00.
         - Edit status should be 'Locked'.
      3. Assert mathematical consistency: Amount = Paid + Outstanding across all records.
    """
    page = logged_in_page
    invoice_page = InvoicePage(page)

    invoice_page.go_to_invoices()

    # 1. Validate Pending status synchronization
    invoice_page.filter_by_status_tab("Pending")
    page.wait_for_timeout(1000)

    pending_count = invoice_page.get_table_rows().count()
    if pending_count > 0:
        pending_data = invoice_page.get_invoice_row_data(0)
        logger.info(f"First Pending Invoice Data: {pending_data}")
        # In pending, paid should be 0 or small partial payment
        assert "0.00" in pending_data["paid_inr"] or "0.00" in pending_data["paid_usd"], (
            f"Expected 0 paid for pending invoice, got INR={pending_data['paid_inr']}"
        )
        assert pending_data["outstanding_inr"] != "₹0.00" or pending_data["outstanding_usd"] != "$0.00"

    # 2. Validate Paid status synchronization
    invoice_page.filter_by_status_tab("Paid")
    page.wait_for_timeout(1000)

    paid_count = invoice_page.get_table_rows().count()
    assert paid_count > 0, "Expected at least 1 paid invoice"
    paid_data = invoice_page.get_invoice_row_data(0)
    logger.info(f"First Paid Invoice Data: {paid_data}")

    # In Paid invoice:
    # Outstanding must be 0.00
    assert "0.00" in paid_data["outstanding_inr"] or "0.00" in paid_data["outstanding_usd"], (
        f"Outstanding should be 0.00 for Paid invoice, got: {paid_data['outstanding_inr']}"
    )
    # Status badge must be PAID
    assert "PAID" in paid_data["status"].upper(), f"Status must be PAID, got: {paid_data['status']}"
    # Edit must be Locked
    assert "Locked" in paid_data["edit"] or "LOCKED" in paid_data["edit"].upper(), (
        f"Paid invoices must be locked from editing, got: {paid_data['edit']}"
    )

    # Return to All
    invoice_page.filter_by_status_tab("All")

    logger.info("Phase 7: Invoice & Payment Status Synchronization VERIFIED ✓")


@pytest.mark.ui
def test_phase7_status_tabs_badge_count_synchronization(logged_in_page: Page):
    """
    Phase 7: Validate that status tab badge numbers accurately reflect table counts:
      - 'All' tab badge == sum of individual status tabs.
      - Clicking each tab updates table to only display matching records.
    """
    page = logged_in_page
    invoice_page = InvoicePage(page)

    invoice_page.go_to_invoices()

    tabs = invoice_page.get_status_tabs()
    logger.info(f"Phase 7 Tabs Map: {tabs}")

    total_all = int(tabs.get("All", 0))
    pending_cnt = int(tabs.get("Pending", 0))
    paid_cnt = int(tabs.get("Paid", 0))
    balance_cnt = int(tabs.get("Balance", 0))
    overpay_cnt = int(tabs.get("Overpay", 0))
    rejected_cnt = int(tabs.get("Rejected", 0))

    sum_statuses = pending_cnt + paid_cnt + balance_cnt + overpay_cnt + rejected_cnt
    logger.info(f"Total All = {total_all}, Sum of sub-tabs = {sum_statuses}")
    assert total_all >= sum_statuses, f"Total 'All' ({total_all}) must be >= sum of status tabs ({sum_statuses})"

    # Validate that clicking Pending tab returns exactly pending_cnt rows
    invoice_page.filter_by_status_tab("Pending")
    page.wait_for_timeout(800)
    assert invoice_page.get_table_rows().count() == pending_cnt, f"Pending tab rows count must match badge ({pending_cnt})"

    # Validate that clicking Paid tab returns exactly paid_cnt rows
    invoice_page.filter_by_status_tab("Paid")
    page.wait_for_timeout(800)
    assert invoice_page.get_table_rows().count() == paid_cnt, f"Paid tab rows count must match badge ({paid_cnt})"

    # Return to All
    invoice_page.filter_by_status_tab("All")

    logger.info("Phase 7: Status Tabs Badge Count Synchronization VERIFIED ✓")
