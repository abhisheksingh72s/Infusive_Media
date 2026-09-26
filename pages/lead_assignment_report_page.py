import logging
import os
import re
from typing import Any, Dict, List, Optional
from playwright.sync_api import Page, Locator, Response

logger = logging.getLogger(__name__)

# Standard UI Column Headers for Lead Assignment Report
EXPECTED_ASSIGNMENT_HEADERS = [
    "S.No",
    "User Name",
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
    "Not Interested"
]

HEADER_KEY_MAP = {
    "S.No": "sNo",
    "User Name": "userName",
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
}


class LeadAssignmentReportPage:
    """Page Object Model for the Lead Assignment Report page with dynamic DOM extraction."""

    def __init__(self, page: Page):
        self.page = page
        env_url = os.getenv("BASE_URL") or "https://infusive-front.jobvritta.com/login"
        clean_base = env_url.replace("/login", "").rstrip("/")
        self.report_url = f"{clean_base}/lead-report"

        # Captured API response holder
        self.captured_api_payloads: List[Dict[str, Any]] = []

        # Locators based on Chakra UI DOM
        self.heading: Locator = page.locator("p:has-text('Lead Assignment Report')")
        self.search_input: Locator = page.locator("input[placeholder='Search by name']")
        self.date_range_input: Locator = page.locator("input[placeholder='Select Date Range']")
        
        # Filter Popover Locators
        self.filter_btn: Locator = page.locator("button:has-text('Filter')").first
        self.filter_popover: Locator = page.locator("section[id*='popover-content']").first
        self.filter_search_input: Locator = page.locator("input[placeholder='Search Assign To']")
        self.filter_reset_btn: Locator = page.locator("button:has-text('Reset')")
        self.filter_apply_btn: Locator = page.locator("button:has-text('Apply')")

        # Sort By Popover Locators
        self.sort_by_btn: Locator = page.locator("button:has-text('User Name'), button[id*='popover-trigger-']").last

        # Table Locators
        self.table: Locator = page.locator("table.chakra-table").first
        self.header_cells: Locator = page.locator("thead.table_header tr th")
        self.body_rows: Locator = page.locator("tbody tr")
        self.grand_total_row: Locator = page.locator("tbody tr:has-text('Grand Total')")
        
        # Pagination Locators
        self.pagination_info: Locator = page.locator("p:has-text('Showing')")
        self.page_size_select: Locator = page.locator("select.chakra-select")

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
        """Navigate to Lead Assignment Report page via sidebar or direct URL."""
        logger.info("Navigating to Lead Assignment Report at %s...", self.report_url)
        
        self.attach_network_listener()

        # Try clicking sidebar Report menu -> Lead Assignment Report
        try:
            report_menu = self.page.locator("a:has-text('Report'), button:has-text('Report'), .nav-item:has-text('Report')").first
            if report_menu.is_visible():
                report_menu.click()
                self.page.wait_for_timeout(500)
                assign_sub = self.page.locator("a:has-text('Assignment Report'), a:has-text('Lead Assignment'), a[href*='lead-report']").first
                if assign_sub.is_visible():
                    assign_sub.click()
                else:
                    self.page.goto(self.report_url, wait_until="domcontentloaded")
            else:
                self.page.goto(self.report_url, wait_until="domcontentloaded")
        except Exception:
            self.page.goto(self.report_url, wait_until="domcontentloaded")

        self.page.wait_for_load_state("networkidle")
        self.table.wait_for(state="visible", timeout=15000)
        logger.info("Lead Assignment Report loaded successfully.")

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
        Extract all user rows from the DOM table into structured JSON dictionaries.
        Excludes the Grand Total row.
        """
        headers = self.get_table_headers()
        rows_data = []
        total_rows = self.body_rows.count()

        for idx in range(total_rows):
            row = self.body_rows.nth(idx)
            row_text = row.text_content() or ""
            
            # Skip Grand Total row
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

                # Cast numeric columns to integer
                if key in ["sNo", "createdLeads", "accepted", "notAccepted", "rejected",
                            "assigned", "contacted", "requirementGathering", "proposalShared",
                            "negotiation", "decisionPending", "won", "lost", "notInterested"]:
                    try:
                        row_dict[key] = int(cell_text.replace(",", ""))
                    except (ValueError, TypeError):
                        row_dict[key] = 0
                else:
                    row_dict[key] = cell_text

            rows_data.append(row_dict)

        logger.info("Extracted %d user rows from DOM table body.", len(rows_data))
        return rows_data

    def extract_grand_total_json(self) -> Dict[str, Any]:
        """Extract and parse the '📊 Grand Total' row from DOM."""
        headers = self.get_table_headers()
        total_dict = {"userName": "Grand Total"}

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
                        "negotiation", "decisionPending", "won", "lost", "notInterested"]:
                try:
                    total_dict[key] = int(cell_text.replace(",", ""))
                except (ValueError, TypeError):
                    total_dict[key] = 0
            elif key == "userName":
                total_dict[key] = cell_text

        logger.info("Extracted Grand Total from DOM: %s", total_dict)
        return total_dict

    def search_by_name(self, name: str):
        """Type name into the search bar."""
        self.search_input.fill(name)
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("networkidle")

    def get_pagination_text(self) -> str:
        """Return the pagination label, e.g., 'Showing 1-10 of 10 records'."""
        if self.pagination_info.is_visible():
            return (self.pagination_info.text_content() or "").strip()
        return ""

    def get_captured_report_data(self) -> Optional[List[Dict[str, Any]]]:
        """Return the extracted backend API rows captured during page load."""
        for item in self.captured_api_payloads:
            logger.info("Inspecting captured API call: %s %s", item.get("method"), item.get("url"))
            payload = item.get("data")
            if isinstance(payload, dict):
                if "data" in payload and isinstance(payload["data"], list):
                    return payload["data"]
            elif isinstance(payload, list):
                return payload
        return None
