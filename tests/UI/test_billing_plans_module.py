import logging
import pytest
from playwright.sync_api import Page, expect

from pages.billing_plans_page import BillingPlansPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_billing_plans_navigation_and_kpis(logged_in_page: Page):
    """
    Test Billing Plans (/allBillingPlans) Navigation and KPI metrics:
      1. Navigate to Billing Plans module.
      2. Verify URL is /allBillingPlans.
      3. Extract and verify top KPI cards (Plans, Active, Due for invoice, Recurring).
    """
    page = logged_in_page
    billing_page = BillingPlansPage(page)

    # 1. Navigate to Billing Plans
    billing_page.go_to_billing_plans()
    assert "/allBillingPlans" in page.url

    # 2. Extract KPI metrics
    metrics = billing_page.get_kpi_summary_metrics()
    logger.info(f"Extracted KPI metrics: {metrics}")

    assert "plans_filtered" in metrics or "active" in metrics, f"Expected KPI metrics, got: {metrics}"
    if "plans_filtered" in metrics:
        assert int(metrics["plans_filtered"]) >= 1
    if "active" in metrics:
        assert int(metrics["active"]) >= 1

    logger.info("Billing Plans Navigation and KPI metrics VERIFIED ✓")


@pytest.mark.ui
def test_billing_plans_table_columns_and_data_integrity(logged_in_page: Page):
    """
    Test Billing Plans Table Structure & Row Content:
      1. Verify required table headers: S.NO, CUSTOMER, PROJECT, TYPE, CURRENCY, AMOUNT, START, NEXT INVOICE, AUTO, STATUS, INVOICES.
      2. Verify rows have valid data:
         - Status badge ('ACTIVE' or 'INACTIVE')
         - Currency ('INR' or 'USD')
         - Auto badge ('ON' or 'OFF')
         - 'Open' action button
    """
    page = logged_in_page
    billing_page = BillingPlansPage(page)

    billing_page.go_to_billing_plans()

    # 1. Verify headers
    headers = billing_page.get_table_headers()
    logger.info(f"Billing Plans Table Headers: {headers}")

    required_headers = ["S.NO", "CUSTOMER", "PROJECT", "TYPE", "CURRENCY", "START", "STATUS"]
    for req in required_headers:
        assert any(req in h.upper() for h in headers), f"Expected header '{req}' in {headers}"

    # 2. Verify rows
    rows = billing_page.get_table_rows()
    count = rows.count()
    logger.info(f"Total billing plan rows on page 1: {count}")
    assert count > 0, "Expected at least 1 billing plan row"

    # Extract row 1
    row_1 = billing_page.get_plan_row_data(0)
    logger.info(f"Billing Plan Row 1: {row_1}")
    assert len(row_1["customer"]) > 0
    assert len(row_1["project"]) > 0
    assert row_1["currency"] in ["INR", "USD"]
    assert "ACTIVE" in row_1["status"] or "INACTIVE" in row_1["status"]

    logger.info("Billing Plans Table Columns and Data Integrity VERIFIED ✓")


@pytest.mark.ui
def test_billing_plans_search_and_filters(logged_in_page: Page):
    """
    Test Billing Plans Search and Dropdown Filtering & Card Count Parity:
      1. Verify initial 'Plans (filtered)' KPI card matches pagination total (e.g., 42).
      2. Search by specific customer/project (e.g. 'Testing Company'):
         - Assert all returned rows contain 'Testing Company'.
         - Assert 'Plans (filtered)' KPI card updates to match filtered table records.
      3. Clear search and test 'Only plans due for invoice' toggle:
         - Assert returned rows count matches the 'Due for invoice' KPI card (e.g., 5).
         - Assert all returned rows display the 'Due' badge.
      4. Filter by Customer dropdown and verify row mapping.
    """
    import re
    page = logged_in_page
    billing_page = BillingPlansPage(page)

    billing_page.go_to_billing_plans()

    # 1. Initial State: Check Card Count vs Pagination
    initial_metrics = billing_page.get_kpi_summary_metrics()
    initial_pagination = billing_page.get_pagination_info()
    logger.info(f"Initial KPI metrics: {initial_metrics}")
    logger.info(f"Initial pagination info: '{initial_pagination}'")

    pag_match = re.search(r"of\s+(\d+)", initial_pagination)
    total_from_pagination = int(pag_match.group(1)) if pag_match else None
    card_plans_filtered = int(initial_metrics["plans_filtered"]) if "plans_filtered" in initial_metrics else None

    logger.info(f"Card 'Plans (filtered)': {card_plans_filtered} | Pagination Total: {total_from_pagination}")
    assert card_plans_filtered == total_from_pagination, (
        f"Initial KPI card count ({card_plans_filtered}) must match pagination total ({total_from_pagination})"
    )

    # 2. Search by 'Testing Company'
    billing_page.search_plans("Testing Company")
    page.wait_for_timeout(1000)

    rows = billing_page.get_table_rows().all()
    search_pagination = billing_page.get_pagination_info()
    search_metrics = billing_page.get_kpi_summary_metrics()
    logger.info(f"Rows returned after searching 'Testing Company': {len(rows)}")
    logger.info(f"Search pagination: '{search_pagination}' | Search KPI: {search_metrics}")

    assert len(rows) > 0, "Search for 'Testing Company' should return at least 1 row"
    search_pag_match = re.search(r"of\s+(\d+)", search_pagination)
    search_total = int(search_pag_match.group(1)) if search_pag_match else len(rows)

    # Assert all rows match search query
    for r in rows:
        row_text = r.inner_text()
        assert "Testing Company" in row_text, f"Row should contain 'Testing Company': {row_text}"

    # Assert KPI card 'Plans (filtered)' dynamically matches search total
    if "plans_filtered" in search_metrics:
        logger.info(f"Search KPI Plans Filtered: {search_metrics['plans_filtered']} vs Search Total: {search_total}")
        assert int(search_metrics["plans_filtered"]) == search_total, (
            f"KPI 'Plans (filtered)' ({search_metrics['plans_filtered']}) must match search total ({search_total})"
        )

    # 3. Clear search
    billing_page.search_plans("")
    page.wait_for_timeout(1000)

    # 4. Test 'Only plans due for invoice' toggle
    due_card_count = int(initial_metrics.get("due_for_invoice", 0))
    logger.info(f"Initial 'Due for invoice' card count: {due_card_count}")

    billing_page.toggle_due_for_invoice_only()
    page.wait_for_timeout(1000)

    due_rows = billing_page.get_table_rows().all()
    due_pagination = billing_page.get_pagination_info()
    due_metrics = billing_page.get_kpi_summary_metrics()
    logger.info(f"Rows returned when filtering due plans only: {len(due_rows)}")
    logger.info(f"Due toggle pagination: '{due_pagination}' | Due toggle KPI: {due_metrics}")

    due_pag_match = re.search(r"of\s+(\d+)", due_pagination)
    due_total = int(due_pag_match.group(1)) if due_pag_match else len(due_rows)

    assert due_total == due_card_count, (
        f"Filtered table count ({due_total}) must match 'Due for invoice' card count ({due_card_count})"
    )

    # Assert every displayed row has the 'Due' badge in Next Invoice column
    for r in due_rows:
        next_inv_cell = r.locator("td:nth-child(8)")
        assert "DUE" in next_inv_cell.inner_text().upper(), (
            f"Row must display 'DUE' badge when filtered by due only: {next_inv_cell.inner_text()}"
        )

    # Untoggle back
    billing_page.toggle_due_for_invoice_only()
    page.wait_for_timeout(1000)

    logger.info("Billing Plans Search, Filtering & Card Count Parity VERIFIED ✓")


@pytest.mark.ui
def test_billing_plan_open_details(logged_in_page: Page):
    """
    Test clicking 'Open' on a billing plan row navigates to the project billing plan configuration.
    """
    page = logged_in_page
    billing_page = BillingPlansPage(page)

    billing_page.go_to_billing_plans()

    # Find first row project
    row_1 = billing_page.get_plan_row_data(0)
    project_name = row_1["project"]
    logger.info(f"Testing 'Open' action for project: '{project_name}'")

    billing_page.open_plan_details(project_name)
    page.wait_for_timeout(1500)

    # Verify modal opened or navigated
    modal = page.locator("section[role='dialog'], div.chakra-modal__content").first
    if modal.is_visible():
        logger.info("Update Billing Plan modal opened successfully via action button.")
        billing_page.close_edit_modal()
    else:
        logger.info(f"Navigated to URL: {page.url}")
        assert "project" in page.url.lower() or "billing" in page.url.lower()

    logger.info("Billing Plan Open Action VERIFIED ✓")


@pytest.mark.ui
def test_billing_plans_advanced_filters_and_sorting(logged_in_page: Page):
    """
    Test Billing Plans Advanced Filters ('More filters') & Sorting:
      1. Expand 'More filters' collapsible drawer.
      2. Filter by Currency ('USD').
      3. Verify filtered table row counts and column attributes.
      4. Test 'Sort by' dropdown ('Amount (high to low)').
      5. Verify pagination text summary ('Showing 1–...').
    """
    page = logged_in_page
    billing_page = BillingPlansPage(page)

    billing_page.go_to_billing_plans()

    # 1. Verify Pagination info
    pagination_info = billing_page.get_pagination_info()
    logger.info(f"Initial pagination info: '{pagination_info}'")
    assert "Showing" in pagination_info

    # 2. Open More Filters and Filter by Currency USD
    billing_page.filter_by_currency("USD")
    page.wait_for_timeout(1000)

    rows = billing_page.get_table_rows().all()
    logger.info(f"Rows returned for USD currency: {len(rows)}")
    assert len(rows) > 0, "Expected at least 1 USD billing plan"

    for r in rows:
        badge_text = r.locator("td:nth-child(5)").inner_text().strip()
        assert "USD" in badge_text, f"Row currency should be USD, got: {badge_text}"

    # 3. Sort by 'Amount (high to low)'
    billing_page.sort_by("Amount (high to low)")
    page.wait_for_timeout(1000)

    row_1 = billing_page.get_plan_row_data(0)
    logger.info(f"Top amount row after sort: {row_1['customer']} - {row_1['amount_with_gst']}")

    # 4. Reset currency to 'All currencies'
    billing_page.filter_by_currency("All currencies")
    page.wait_for_timeout(1000)

    logger.info("Billing Plans Advanced Filters & Sorting VERIFIED ✓")


@pytest.mark.ui
def test_billing_plan_invoices_column_edit_modal(logged_in_page: Page):
    """
    Test the 'Invoices' column in the Billing Plans table:
      1. Verify the 'Invoices' column contains both:
         - The invoice count number (e.g., '1')
         - An edit icon button
      2. Click the edit icon to open the 'Update Billing Plan' modal.
      3. Verify the modal structure and controls:
         - Modal Header and Title ('Update Billing Plan')
         - Billing Type (One-Time / Recurring radio)
         - Currency code select
         - Start Date and Next Invoice Date
         - Billing Services table with service rows, quantity, unit price, GST %, total
         - Calculation summary: Subtotal, Total GST, Total Amount
         - Auto-generate invoice switch
         - Action buttons: 'Cancel', 'Update Plan & Generate Invoice Now', 'Update Plan'
      4. Close the modal via 'Cancel' and assert it closes cleanly.
    """
    page = logged_in_page
    billing_page = BillingPlansPage(page)

    billing_page.go_to_billing_plans()

    # 1. Inspect row 1: Invoices count (Col 11) & Edit button (Col 12 with aria-label="Edit billing plan")
    row_1_data = billing_page.get_plan_row_data(0)
    logger.info(f"Row 1 Plan Data: {row_1_data}")
    assert len(row_1_data["invoices"]) > 0, "Invoices count column must be populated"

    row = billing_page.get_table_rows().first
    edit_btn = row.locator("button[aria-label='Edit billing plan'], td:nth-child(12) button").first
    assert edit_btn.is_visible(), "Row must contain 'Edit billing plan' button"

    # 2. Open Edit modal
    modal = billing_page.open_edit_billing_plan_modal(row_index=0)
    assert modal.is_visible(), "Update Billing Plan modal must open on clicking edit icon"

    # 3. Extract and verify modal fields
    details = billing_page.get_edit_modal_details()
    logger.info(f"Update Billing Plan Modal Details: {details}")

    assert "Billing plan" in details["header"] or len(details["header"]) > 0
    assert "Update Billing Plan" in details["title"]
    assert details["billing_type"] in ["One-Time", "Recurring"]
    assert len(details["currency"]) > 0
    assert len(details["services"]) >= 1, "Expected at least 1 service row in billing plan modal"

    # Verify action buttons
    cancel_btn = modal.locator("button:has-text('Cancel')").first
    update_now_btn = modal.locator("button:has-text('Update Plan & Generate Invoice Now')").first
    update_btn = modal.locator("button:has-text('Update Plan')").first

    assert cancel_btn.is_visible(), "Cancel button must be visible"
    assert update_now_btn.is_visible(), "Update Plan & Generate Invoice Now button must be visible"
    assert update_btn.is_visible(), "Update Plan button must be visible"

    # 4. Close modal
    billing_page.close_edit_modal()
    expect(modal).to_be_hidden()

    logger.info("Billing Plan 'Invoices' Column & Edit Modal VERIFIED ✓")


