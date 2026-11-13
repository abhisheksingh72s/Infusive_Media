"""
Invoice Ledger Workflow
=======================
Encapsulates searching, inspecting, and asserting generated invoices
in the Master Invoices ledger (/invoice-list-page).
"""

import logging
from playwright.sync_api import Page
from pages.invoice_page import InvoicePage

logger = logging.getLogger(__name__)


class InvoiceWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.invoice_page = InvoicePage(page)

    def verify_invoice_in_ledger(
        self,
        company_name: str,
        expected_status: str = "Pending",
    ) -> dict:
        """Search invoices by company/project and assert presence and status."""
        logger.info(f"Checking Invoices ledger for '{company_name}'...")
        self.invoice_page.go_to_invoices()
        self.page.wait_for_timeout(1000)
        self.invoice_page.search_invoices(company_name)
        self.page.wait_for_timeout(1000)

        rows = self.invoice_page.get_table_rows()
        inv_data = {}
        assert rows.count() > 0, f"Expected at least 1 invoice row in Ledger for '{company_name}', but found 0!"

        inv_data = self.invoice_page.get_invoice_row_data(0)
        if inv_data:
            inv_data["invoice_number"] = inv_data.get("invoice_no")
        logger.info(f"Verified Invoice in Ledger: {inv_data}")
        if expected_status:
            assert expected_status.lower() in inv_data["status"].lower(), (
                f"Expected status '{expected_status}', got '{inv_data['status']}'"
            )

        return inv_data
