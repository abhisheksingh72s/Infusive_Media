import logging
import os
import re
from typing import Any, Dict, List, Tuple
from playwright.sync_api import Page, Locator
from utilities.table_json_parser import TableJsonParser

logger = logging.getLogger(__name__)


class LeadCreationReportPage:
    """Page Object Model for the Lead Creation Report page with dynamic JSON DOM extraction."""

    def __init__(self, page: Page):
        self.page = page
        env_url = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/")
        clean_base = env_url.replace("/login", "").rstrip("/")
        self.report_url = f"{clean_base}/reports/presales"

        # Locators
        self.report_module_menu: Locator = page.locator("a:has-text('Report'), button:has-text('Report'), .nav-item:has-text('Report')")
        self.creation_report_submenu: Locator = page.locator("a:has-text('Creation Report'), a:has-text('Lead Creation Report'), button:has-text('Creation Report')")
        self.page_heading: Locator = page.locator("h1, h2, .page-title, .heading")

        self.table_locator: Locator = page.locator("table")
        self.header_cells: Locator = page.locator("table thead tr th")
        self.body_rows: Locator = page.locator("table tbody tr")
        self.footer_row: Locator = page.locator("table tfoot tr, table tbody tr.grand-total, table tbody tr:last-child")
        self.next_page_btn: Locator = page.locator("button:has-text('Next'), button[aria-label='Next page'], .pagination-next:not(.disabled)")

    def navigate(self):
        """Navigate to Lead Creation Report page via sidebar links or direct URL."""
        logger.info("Navigating to Lead Creation Report page...")
        # 1. Click Report Module
        try:
            report_menu = self.page.locator("a:has-text('Report'), button:has-text('Report'), .nav-item:has-text('Report')").first
            if report_menu.is_visible():
                report_menu.click()
                self.page.wait_for_timeout(500)
        except Exception as e:
            logger.warning("Could not click Report sidebar menu: %s", str(e))

        # 2. Click Creation Report sub-menu
        try:
            creation_sub = self.page.locator("a:has-text('Creation Report'), a:has-text('Creation')").first
            if creation_sub.is_visible():
                creation_sub.click()
                self.page.wait_for_timeout(1500)
            else:
                self.page.goto(self.report_url, wait_until="domcontentloaded")
        except Exception:
            self.page.goto(self.report_url, wait_until="domcontentloaded")

        self.table_locator.first.wait_for(state="visible", timeout=15000)

    def click_report_module(self):
        """Click Report module in sidebar navigation."""
        logger.info("Clicking Report Module in sidebar navigation...")
        self.report_module_menu.first.click()
        self.page.wait_for_timeout(500)

    def click_creation_report(self):
        """Click Creation Report sub-menu item."""
        logger.info("Clicking Creation Report in sub-menu...")
        self.creation_report_submenu.first.click()
        self.page.wait_for_timeout(1000)

    def get_page_title(self) -> str:
        """Get the page header title text."""
        title_text = self.page_heading.first.inner_text().strip() if self.page_heading.count() > 0 else ""
        logger.info("Extracted Page Title: '%s'", title_text)
        return title_text

    def get_table_headers(self) -> List[str]:
        """Extract all column header text dynamically from DOM standard table thead."""
        headers = [th.inner_text().strip() for th in self.header_cells.all()]
        logger.info("Extracted %d UI Table Headers: %s", len(headers), headers)
        return headers

    def extract_row_to_json(self, row_locator: Locator, headers: List[str]) -> Dict[str, Any]:
        """Extract cell text from row locator and convert into a JSON dictionary."""
        cells = row_locator.locator("td").all()
        cell_values = [cell.inner_text().strip() for cell in cells]
        row_json = TableJsonParser.convert_row_to_json(headers, cell_values)

        if "userName" in row_json and "User Name" not in row_json:
            row_json["User Name"] = str(row_json["userName"]).strip()

        return row_json

    def extract_table_to_json(self) -> List[Dict[str, Any]]:
        """Extract all tbody rows dynamically into a list of JSON dictionaries."""
        headers = self.get_table_headers()
        rows_json = []

        all_rows = self.body_rows.all()
        for idx, row in enumerate(all_rows):
            row_text = row.inner_text().strip()
            if "GRAND TOTAL" in row_text.upper() or "TOTAL" in row_text.upper():
                continue
            if len(row_text) > 0:
                row_json = self.extract_row_to_json(row, headers)
                rows_json.append(row_json)

        logger.info("Extracted %d user rows into JSON structure", len(rows_json))
        return rows_json

    def extract_grand_total_json(self) -> Dict[str, Any]:
        """Extract Grand Total row from tfoot (or footer row) into JSON dictionary."""
        headers = self.get_table_headers()
        if self.footer_row.count() > 0:
            footer_text = self.footer_row.first.inner_text().strip()
            if "GRAND TOTAL" in footer_text.upper() or "TOTAL" in footer_text.upper():
                grand_total_json = self.extract_row_to_json(self.footer_row.first, headers)
                logger.info("Extracted Grand Total JSON from tfoot: %s", grand_total_json)
                return grand_total_json

        logger.warning("No explicit Grand Total footer row identified in tfoot")
        return {}
