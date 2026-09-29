import logging
import os
import re
from typing import Any, Dict, List, Optional
from playwright.sync_api import Page, Locator, Response
from utilities.datepicker_helper import DatePickerHelper

logger = logging.getLogger(__name__)

# Standard UI Column Headers for Source Wise Report (16 columns)
EXPECTED_SOURCE_WISE_HEADERS = [
    "Source",
    "Created Leads",
    "Accepted",
    "Not Accepted",
    "Rejected",
    "Assigned",
    "Contacted",
    "Requirement Gathering",
    "Proposal Shared",
    "Negotiation",
    "Decision Pending",
    "Won",
    "Lost",
    "Not Interested",
    "Duplicate",
    "Unassigned"
]

HEADER_KEY_MAP = {
    "Source": "sourceName",
    "Created Leads": "createdLeads",
    "Accepted": "accepted",
    "Not Accepted": "notAccepted",
    "Rejected": "rejected",
    "Assigned": "assigned",
    "Contacted": "contacted",
    "Requirement Gathering": "requirementGathering",
    "Proposal Shared": "proposalShared",
    "Negotiation": "negotiation",
    "Decision Pending": "decisionPending",
    "Won": "won",
    "Lost": "lost",
    "Not Interested": "notInterested",
    "Duplicate": "duplicate",
    "Unassigned": "unassigned"
}

MODAL_HEADER_KEY_MAP = {
    "S.NO": "sNo",
    "User Name": "userName",
    "Source": "sourceName",
    "Created Leads": "createdLeads",
    "Accepted": "accepted",
    "Not Accepted": "notAccepted",
    "Pending": "pending",
    "Rejected": "rejected",
    "Assigned": "assigned",
    "Contacted": "contacted",
    "Requirement Gathering": "requirementGathering",
    "Proposal Shared": "proposalShared",
    "Negotiation": "negotiation",
    "Decision Pending": "decisionPending",
    "Won": "won",
    "Lost": "lost",
    "Not Interested": "notInterested",
    "Duplicate": "duplicate",
    "Unassigned": "unassigned"
}


class SourceWiseReportPage:
    """Page Object Model for the Source Wise Report page with dynamic DOM extraction."""

    def __init__(self, page: Page):
        self.page = page
        env_url = os.getenv("BASE_URL") or "https://infusive-front.jobvritta.com/login"
        clean_base = env_url.replace("/login", "").rstrip("/")
        self.report_url = f"{clean_base}/source-wise-report"

        # Captured API response holder
        self.captured_api_payloads: List[Dict[str, Any]] = []

        # Locators based on Chakra UI DOM
        self.heading: Locator = page.locator("p:has-text('Source Wise Report')")
        self.search_input: Locator = page.locator("input[placeholder='Search by source']")
        self.date_range_input: Locator = page.locator("input[placeholder='Select Date Range']")
        
        # Filter Popover Locators
        self.filter_btn: Locator = page.locator("button:has-text('Filter')").first
        self.filter_popover: Locator = page.locator("section[id*='popover-content']").first
        self.filter_search_input: Locator = page.locator("input[placeholder='Search Source Filter']")
        self.filter_reset_btn: Locator = page.locator("button:has-text('Reset')")
        self.filter_apply_btn: Locator = page.locator("button:has-text('Apply')")

        # Table Locators
        self.table: Locator = page.locator("table.chakra-table").first
        self.header_cells: Locator = page.locator("thead.table_header tr th")
        self.body_rows: Locator = page.locator("tbody tr")
        self.grand_total_row: Locator = page.locator("tbody tr:has-text('Grand Total')")
        
        # Pagination Locators
        self.pagination_info: Locator = page.locator("p:has-text('Showing')")
        self.page_size_select: Locator = page.locator("select.chakra-select")

        # Modal Drilldown Locators
        self.modal_content: Locator = page.locator("section.chakra-modal__content").first
        self.modal_title: Locator = page.locator("section.chakra-modal__content p.chakra-text").first
        self.radio_source_wise: Locator = page.locator("section.chakra-modal__content label:has-text('Source Wise')").first
        self.radio_user_wise: Locator = page.locator("section.chakra-modal__content label:has-text('User Wise')").first
        self.modal_close_btn: Locator = page.locator("section.chakra-modal__content button.chakra-modal__close-btn").first
        self.modal_header_cells: Locator = page.locator("section.chakra-modal__content thead tr th")
        self.modal_body_rows: Locator = page.locator("section.chakra-modal__content tbody tr")

    def attach_network_listener(self):
        """Listen to incoming network responses to capture report API payloads."""
        def handle_response(response: Response):
            if "/api/" in response.url.lower():
                logger.info("API RESPONSE CAPTURED: %s [%d] %s", response.request.method, response.status, response.url)
                if response.status == 200:
                    try:
                        data = response.json()
                        self.captured_api_payloads.append({
                            "url": response.url,
                            "method": response.request.method,
                            "data": data
                        })
                    except Exception:
                        pass
        self.page.on("response", handle_response)

    def navigate(self):
        """Navigate to Source Wise Report page via sidebar or direct URL."""
        logger.info("Navigating to Source Wise Report at %s...", self.report_url)
        
        self.attach_network_listener()

        try:
            report_menu = self.page.locator("a:has-text('Report'), button:has-text('Report'), .nav-item:has-text('Report')").first
            if report_menu.is_visible():
                report_menu.click()
                self.page.wait_for_timeout(500)
                source_sub = self.page.locator("a:has-text('Source Wise Report'), a[href*='source-wise-report']").first
                if source_sub.is_visible():
                    source_sub.click()
                else:
                    self.page.goto(self.report_url, wait_until="domcontentloaded")
            else:
                self.page.goto(self.report_url, wait_until="domcontentloaded")
        except Exception:
            self.page.goto(self.report_url, wait_until="domcontentloaded")

        self.page.wait_for_load_state("networkidle")
        self.table.wait_for(state="visible", timeout=15000)
        logger.info("Source Wise Report loaded successfully.")

    def get_table_headers(self) -> List[str]:
        """Extract clean text of all table headers from DOM."""
        headers = []
        count = self.header_cells.count()
        for idx in range(count):
            txt = (self.header_cells.nth(idx).text_content() or "").strip()
            headers.append(txt)
        logger.info("Extracted %d headers from DOM: %s", len(headers), headers)
        return headers

    def extract_table_to_json(self) -> List[Dict[str, Any]]:
        """
        Extract all source rows from the DOM table into structured JSON dictionaries.
        Excludes the Grand Total row.
        """
        headers = self.get_table_headers()
        rows_data = []
        total_rows = self.body_rows.count()

        for idx in range(total_rows):
            row = self.body_rows.nth(idx)
            row_text = row.text_content() or ""
            
            if "Grand Total" in row_text:
                continue

            cells = row.locator("td")
            cell_count = cells.count()
            if cell_count == 0:
                continue

            row_dict = {}
            for col_idx in range(min(len(headers), cell_count)):
                header_name = headers[col_idx]
                key = HEADER_KEY_MAP.get(header_name, header_name.lower())
                cell_text = (cells.nth(col_idx).text_content() or "").strip()

                if key in ["createdLeads", "accepted", "notAccepted", "rejected",
                            "assigned", "contacted", "requirementGathering", "proposalShared",
                            "negotiation", "decisionPending", "won", "lost", "notInterested",
                            "duplicate", "unassigned"]:
                    try:
                        row_dict[key] = int(cell_text.replace(",", ""))
                    except (ValueError, TypeError):
                        row_dict[key] = 0
                else:
                    row_dict[key] = cell_text

            rows_data.append(row_dict)

        logger.info("Extracted %d source rows from DOM table body.", len(rows_data))
        return rows_data

    def extract_grand_total_json(self) -> Dict[str, Any]:
        """Extract and parse the '📊 Grand Total' row from DOM."""
        headers = self.get_table_headers()
        total_dict = {"sourceName": "Grand Total"}

        if not self.grand_total_row.is_visible():
            logger.warning("Grand Total row not visible directly, searching in body rows...")
            row = self.page.locator("tbody tr").last
        else:
            row = self.grand_total_row.first

        cells = row.locator("td")
        cell_count = cells.count()

        for col_idx in range(min(len(headers), cell_count)):
            header_name = headers[col_idx]
            key = HEADER_KEY_MAP.get(header_name, header_name.lower())
            cell_text = (cells.nth(col_idx).text_content() or "").strip()

            if key in ["createdLeads", "accepted", "notAccepted", "rejected",
                        "assigned", "contacted", "requirementGathering", "proposalShared",
                        "negotiation", "decisionPending", "won", "lost", "notInterested",
                        "duplicate", "unassigned"]:
                try:
                    total_dict[key] = int(cell_text.replace(",", ""))
                except (ValueError, TypeError):
                    total_dict[key] = 0
            elif key == "sourceName":
                total_dict[key] = cell_text

        logger.info("Extracted Grand Total from DOM: %s", total_dict)
        return total_dict

    def open_lead_details_modal(self, source_name: str, metric_col_index: int = 1):
        """Click on the count cell for a specific source row to open the Lead Details Modal."""
        logger.info("Opening Lead Details modal for source '%s'...", source_name)
        row = self.page.locator(f"tbody tr:has-text('{source_name}')").first
        cell = row.locator("td").nth(metric_col_index)
        cell.click()
        self.page.wait_for_timeout(1000)
        self.modal_content.wait_for(state="visible", timeout=10000)
        logger.info("Modal opened successfully with title: %s", self.modal_title.text_content())

    def select_modal_view_mode(self, mode: str = "userWise"):
        """Select 'userWise' or 'sourceWise' radio button inside the modal."""
        logger.info("Selecting modal view mode radio: %s", mode)
        if mode.lower() == "userwise":
            self.radio_user_wise.click()
        else:
            self.radio_source_wise.click()
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("networkidle")

    def get_modal_headers(self) -> List[str]:
        """Extract headers from modal table."""
        headers = []
        count = self.modal_header_cells.count()
        for idx in range(count):
            txt = (self.modal_header_cells.nth(idx).text_content() or "").strip()
            headers.append(txt)
        logger.info("Extracted %d modal headers: %s", len(headers), headers)
        return headers

    def extract_modal_table_to_json(self) -> List[Dict[str, Any]]:
        """Extract all rows from modal table into structured JSON dictionaries."""
        headers = self.get_modal_headers()
        rows_data = []
        total_rows = self.modal_body_rows.count()

        for idx in range(total_rows):
            row = self.modal_body_rows.nth(idx)
            cells = row.locator("td")
            cell_count = cells.count()
            if cell_count == 0:
                continue

            row_dict = {}
            for col_idx in range(min(len(headers), cell_count)):
                header_name = headers[col_idx]
                key = MODAL_HEADER_KEY_MAP.get(header_name, header_name.lower())
                cell_text = (cells.nth(col_idx).text_content() or "").strip()

                if key in ["sNo", "createdLeads", "accepted", "notAccepted", "pending", "rejected",
                            "assigned", "contacted", "requirementGathering", "proposalShared",
                            "negotiation", "decisionPending", "won", "lost", "notInterested",
                            "duplicate", "unassigned"]:
                    try:
                        row_dict[key] = int(cell_text.replace(",", ""))
                    except (ValueError, TypeError):
                        row_dict[key] = 0
                else:
                    row_dict[key] = cell_text

            rows_data.append(row_dict)

        logger.info("Extracted %d rows from modal table.", len(rows_data))
        return rows_data

    def close_modal(self):
        """Close the Lead Details modal."""
        if self.modal_close_btn.is_visible():
            self.modal_close_btn.click()
            self.page.wait_for_timeout(500)
            logger.info("Modal closed successfully.")

    def search_by_source(self, source_name: str):
        """Type source name into the search bar."""
        self.search_input.fill(source_name)
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("networkidle")

    def get_pagination_text(self) -> str:
        """Return the pagination label, e.g., 'Showing 1-16 of 16 records'."""
        if self.pagination_info.is_visible():
            return (self.pagination_info.text_content() or "").strip()
        return ""

    def select_date_range(self, from_date: Any, to_date: Any) -> str:
        """Select a date range using the global DatePickerHelper utility."""
        return DatePickerHelper.select_date_range(
            page=self.page,
            input_element=self.date_range_input,
            from_date=from_date,
            to_date=to_date
        )
