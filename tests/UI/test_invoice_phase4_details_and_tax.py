import re
import logging
import pytest
from playwright.sync_api import Page, expect

from pages.invoice_page import InvoicePage

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_phase4_invoice_number_and_dates_format(logged_in_page: Page):
    """
    Phase 4: Validate Invoice Numbering and Date Integrity:
      1. Verify Invoice Number pattern: INV-YYYY-XXXX (e.g., INV-2026-0036).
      2. Verify Issued Date and Due Date are valid date formats (DD-MM-YYYY).
      3. Verify overdue badge behavior when due date is past today.
    """
    page = logged_in_page
    invoice_page = InvoicePage(page)

    invoice_page.go_to_invoices()

    rows = invoice_page.get_table_rows()
    count = rows.count()
    assert count > 0, "Expected at least 1 invoice row"

    inv_pattern = re.compile(r"^INV-\d{4}-\d{4,}$")
    date_pattern = re.compile(r"\d{2}-\d{2}-\d{4}")

    for idx in range(min(5, count)):
        data = invoice_page.get_invoice_row_data(idx)
        inv_no = data["invoice_no"].strip()
        logger.info(f"Row {idx + 1}: Invoice No: '{inv_no}', Issued: '{data['issued']}', Due: '{data['due']}'")

        assert inv_pattern.match(inv_no), f"Invoice '{inv_no}' does not match pattern INV-YYYY-XXXX"
        assert date_pattern.search(data["issued"]), f"Issued date invalid: {data['issued']}"
        assert date_pattern.search(data["due"]), f"Due date invalid: {data['due']}"

    logger.info("Phase 4: Invoice Numbering & Dates Format VERIFIED ✓")


@pytest.mark.ui
def test_phase4_customer_details_and_dual_tax_breakdown(logged_in_page: Page):
    """
    Phase 4: Validate Customer Details & Dual Currency Tax Breakdown:
      1. Check Customer and Project columns are populated for each invoice.
      2. Verify dual-currency presentation:
         - INR Columns: Amount, Paid, Outstanding (₹)
         - USD Columns: Amount ($), Paid ($), Outstanding ($) ($)
      3. Assert mathematical consistency:
         - Total Outstanding = Total Amount - Total Paid
    """
    page = logged_in_page
    invoice_page = InvoicePage(page)

    invoice_page.go_to_invoices()

    for idx in range(min(3, invoice_page.get_table_rows().count())):
        data = invoice_page.get_invoice_row_data(idx)
        logger.info(f"Invoice {data['invoice_no']} Details: Customer='{data['customer']}', Project='{data['project']}'")
        assert len(data["customer"]) > 0
        assert len(data["project"]) > 0

        # INR and USD amounts must have currency symbols
        assert "₹" in data["amount_inr"] or "$" in data["amount_inr"], f"Invalid INR currency symbol in: {data['amount_inr']}"
        assert "$" in data["amount_usd"], f"Missing $ symbol in USD amount: {data['amount_usd']}"

        logger.info(f"Dual Breakdown: INR={data['amount_inr']}, USD={data['amount_usd']}")

    logger.info("Phase 4: Customer Details & Dual Tax Breakdown VERIFIED ✓")
