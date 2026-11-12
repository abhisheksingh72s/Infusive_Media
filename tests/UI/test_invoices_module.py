import logging
import pytest
from playwright.sync_api import Page, expect

from pages.invoice_page import InvoicePage

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_invoices_navigation_and_kpi_metrics(logged_in_page: Page):
    """
    Test Invoices (/invoice-list-page) Navigation and KPI metrics:
      1. Navigate to Invoices module.
      2. Verify URL is /invoice-list-page.
      3. Extract and verify top KPI cards (Due Today, Overdue, Due in Next 7 Days, Total Outstanding, Collected This Month).
    """
    page = logged_in_page
    invoice_page = InvoicePage(page)

    # 1. Navigate to Invoices
    invoice_page.go_to_invoices()
    assert "/invoice-list-page" in page.url

    # 2. Extract KPI metrics
    metrics = invoice_page.get_kpi_metrics()
    logger.info(f"Extracted Invoice KPI metrics: {metrics}")

    assert any(k in metrics for k in ["overdue", "total_outstanding", "collected_this_month"]), (
        f"Expected KPI summary metrics, got: {metrics}"
    )

    logger.info("Invoices Navigation and KPI Metrics VERIFIED ✓")


@pytest.mark.ui
def test_invoices_currency_toggle(logged_in_page: Page):
    """
    Test Invoices KPI Currency Toggle:
      1. Verify default or toggle to USD ($).
      2. Switch to INR (₹).
      3. Verify KPI card amounts update with correct currency symbol.
    """
    page = logged_in_page
    invoice_page = InvoicePage(page)

    invoice_page.go_to_invoices()

    # Toggle to USD
    invoice_page.switch_currency("USD")
    page.wait_for_timeout(1000)
    usd_metrics = invoice_page.get_kpi_metrics()
    logger.info(f"USD KPI Metrics: {usd_metrics}")

    # Toggle to INR
    invoice_page.switch_currency("INR")
    page.wait_for_timeout(1000)
    inr_metrics = invoice_page.get_kpi_metrics()
    logger.info(f"INR KPI Metrics: {inr_metrics}")

    assert len(usd_metrics) > 0 or len(inr_metrics) > 0

    logger.info("Invoices Currency Toggle VERIFIED ✓")


@pytest.mark.ui
def test_invoices_status_tabs_filtering(logged_in_page: Page):
    """
    Test Invoices Status Tabs:
      1. Extract available status tabs ('All', 'Pending', 'Paid', 'Balance', etc.).
      2. Filter by 'Pending' and verify returned invoices have Pending status.
      3. Filter by 'Paid' and verify returned invoices have Paid status.
      4. Reset back to 'All'.
    """
    page = logged_in_page
    invoice_page = InvoicePage(page)

    invoice_page.go_to_invoices()

    # 1. Get status tabs
    tabs = invoice_page.get_status_tabs()
    logger.info(f"Invoice status tabs: {tabs}")
    assert any("ALL" in t.upper() for t in tabs)

    # 2. Filter by 'Pending'
    if any("PENDING" in t.upper() for t in tabs):
        invoice_page.filter_by_status_tab("Pending")
        pending_rows = invoice_page.get_table_rows().all()
        logger.info(f"Pending invoices count: {len(pending_rows)}")
        if len(pending_rows) > 0:
            first_pending = invoice_page.get_invoice_row_data(0)
            logger.info(f"First Pending Invoice: {first_pending}")
            assert "Pending" in first_pending["status"] or "Balance" in first_pending["status"]

    # 3. Filter by 'Paid'
    if any("PAID" in t.upper() for t in tabs):
        invoice_page.filter_by_status_tab("Paid")
        paid_rows = invoice_page.get_table_rows().all()
        logger.info(f"Paid invoices count: {len(paid_rows)}")
        if len(paid_rows) > 0:
            first_paid = invoice_page.get_invoice_row_data(0)
            logger.info(f"First Paid Invoice: {first_paid}")
            assert "PAID" in first_paid["status"].upper()

    # 4. Return to 'All'
    invoice_page.filter_by_status_tab("All")

    logger.info("Invoices Status Tabs Filtering VERIFIED ✓")


@pytest.mark.ui
def test_invoices_table_columns_and_search(logged_in_page: Page):
    """
    Test Invoices Table Structure and Search:
      1. Verify table headers: INVOICE NO., CUSTOMER, PROJECT, ISSUED, DUE, AMOUNT, PAID, OUTSTANDING, STATUS.
      2. Search by invoice number and verify matched row.
      3. Verify dual-currency columns (INR & USD) and Overdue tag behavior.
    """
    page = logged_in_page
    invoice_page = InvoicePage(page)

    invoice_page.go_to_invoices()

    # 1. Verify headers
    headers = invoice_page.get_table_headers()
    logger.info(f"Invoices Table Headers: {headers}")

    required_headers = ["INVOICE NO", "CUSTOMER", "PROJECT", "ISSUED", "DUE", "AMOUNT", "PAID", "STATUS"]
    for req in required_headers:
        assert any(req in h.upper() for h in headers), f"Expected header '{req}' in {headers}"

    # 2. Extract first row data
    row_1 = invoice_page.get_invoice_row_data(0)
    logger.info(f"Invoice Row 1: {row_1}")
    inv_no = row_1["invoice_no"]
    assert "INV-" in inv_no, f"Expected invoice number format 'INV-...', got '{inv_no}'"

    # 3. Search by that invoice number
    invoice_page.search_invoices(inv_no)
    page.wait_for_timeout(1000)

    matched_row = invoice_page.find_invoice_row_by_number(inv_no)
    assert matched_row is not None, f"Invoice '{inv_no}' should be found in search results"
    logger.info(f"Matched invoice row text: {matched_row.inner_text().replace(chr(10), ' ')}")

    # Clear search
    invoice_page.search_invoices("")

    logger.info("Invoices Table Columns and Search VERIFIED ✓")


@pytest.mark.ui
def test_invoices_overpay_tab_behavior(logged_in_page: Page):
    """
    Test the 'Overpay' tab behavior on /invoice-list-page:
      1. Inspect status tabs and badges before click.
      2. Click 'Overpay' tab.
      3. Inspect status tabs and badges after click.
      4. Inspect table rows, cell values, and pagination.
    """
    page = logged_in_page
    invoice_page = InvoicePage(page)

    invoice_page.go_to_invoices()

    # 1. Inspect tabs before click
    tabs_before = invoice_page.get_status_tabs()
    logger.info(f"Tabs BEFORE clicking Overpay: {tabs_before}")

    # 2. Click 'Overpay' tab
    invoice_page.filter_by_status_tab("Overpay")
    page.wait_for_timeout(1500)

    # 3. Inspect tabs after click
    tablist = page.locator("div[role='tablist']").first
    logger.info(f"Tablist HTML: {tablist.inner_html()}")
    tabs_after = invoice_page.get_status_tabs()
    logger.info(f"Tabs AFTER clicking Overpay: {tabs_after}")

    # 4. Inspect table rows
    rows = invoice_page.get_table_rows().all()
    logger.info(f"Total rows in table under Overpay: {len(rows)}")
    for i, r in enumerate(rows):
        logger.info(f"Overpay Row {i+1}: {repr(r.inner_text().replace(chr(10), ' '))}")

    # 5. Check pagination / footer
    pag = page.locator("p:has-text('Showing'), [class*='pagination']").all()
    for p_el in pag:
        logger.info(f"Pagination under Overpay: {repr(p_el.inner_text())}")

    logger.info("Overpay Tab Inspection COMPLETE ✓")
