import os
import logging
from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)


class CustomerPage:
    """
    Page Object Model for the Customers Module (/customers and /customers/{id}).
    Handles:
      - Phase 5: Navigation to Customers list
      - Table inspection, column header verification
      - Search by Customer Name / Email
      - Row data extraction (Customer Name, Email, Phone, Address, Outstanding, Status)
      - View details action (/customers/{id})
      - Detail profile assertions (Customer ID, Name, Email, Address)
    """

    def __init__(self, page: Page):
        self.page = page

    def get_base_url(self) -> str:
        base_url = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")
        return base_url.replace("/login", "").rstrip("/")

    def go_to_customers(self):
        """Navigate to the Customers module."""
        logger.info("Navigating to Customers module (/customers)...")

        cust_link = self.page.locator("a[href='/customers'], a[href*='customers']")
        try:
            if cust_link.count() > 0 and cust_link.first.is_visible():
                cust_link.first.click()
            else:
                base_url = self.get_base_url()
                self.page.goto(f"{base_url}/customers", wait_until="domcontentloaded")
        except Exception as e:
            logger.warning(f"Sidebar click navigation failed: {e}. Navigating directly via URL.")
            base_url = self.get_base_url()
            self.page.goto(f"{base_url}/customers", wait_until="domcontentloaded")

        try:
            self.page.wait_for_url("**/customers*", timeout=15000)
        except Exception:
            pass

        self.page.wait_for_timeout(1500)
        logger.info(f"On Customers page. Current URL: {self.page.url}")

    def get_table_headers(self) -> list:
        """Return list of table header names."""
        self.page.locator("thead th, table th").first.wait_for(state="visible", timeout=10000)
        headers = [h.inner_text().strip() for h in self.page.locator("thead th, table th").all() if h.inner_text().strip()]
        logger.info(f"Customers table headers: {headers}")
        return headers

    def search_customer(self, query: str):
        """Search for a customer by name or email."""
        logger.info(f"Searching Customers table for: '{query}'...")
        search_box = self.page.get_by_placeholder("Search by name, email", exact=False)
        if search_box.count() == 0 or not search_box.first.is_visible():
            search_box = self.page.locator("input[placeholder*='Search'], input[type='search']")

        if search_box.count() > 0 and search_box.first.is_visible():
            search_box.first.fill(query)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(1500)
        else:
            logger.warning("Customer search input not found; filtering rows directly.")

    def get_customer_rows(self) -> list:
        """Return all rows currently visible in the customers table."""
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=10000)
            return self.page.locator("tbody tr").all()
        except Exception:
            return []

    def verify_customer_exists(self, customer_name: str) -> bool:
        """Search and check if customer row exists in table."""
        logger.info(f"Verifying customer existence for: '{customer_name}'...")
        self.search_customer(customer_name)
        rows = self.get_customer_rows()
        for r in rows:
            if customer_name.lower() in r.inner_text().lower():
                logger.info(f"Customer '{customer_name}' found in table ✓")
                return True

        # Fallback check across all rows without search filter
        all_text = self.page.locator("tbody").inner_text()
        found = customer_name.lower() in all_text.lower()
        if found:
            logger.info(f"Customer '{customer_name}' found in raw table body ✓")
        return found

    def get_customer_row_data(self, customer_name: str) -> dict:
        """
        Extract row data for the given customer name:
        Columns: S.NO, CUSTOMER NAME, EMAIL, PHONE, ADDRESS, OUTSTANDING, STATUS
        """
        logger.info(f"Extracting row data for customer: '{customer_name}'...")
        self.search_customer(customer_name)
        rows = self.get_customer_rows()
        for r in rows:
            if customer_name.lower() in r.inner_text().lower():
                cells = [td.inner_text().strip() for td in r.locator("td").all()]
                data = {
                    "s_no": cells[0] if len(cells) > 0 else "",
                    "name": cells[1] if len(cells) > 1 else "",
                    "email": cells[2] if len(cells) > 2 else "",
                    "phone": cells[3] if len(cells) > 3 else "",
                    "address": cells[4] if len(cells) > 4 else "",
                    "outstanding": cells[5] if len(cells) > 5 else "",
                    "status": cells[6] if len(cells) > 6 else "",
                }
                logger.info(f"Extracted customer data: {data}")
                return data

        raise ValueError(f"Customer '{customer_name}' not found in Customers table.")

    def click_view_customer_details(self, customer_name: str = ""):
        """
        Click the View Details (eye) action icon for the given customer or first available.
        Navigates to /customers/{id}.
        """
        logger.info(f"Opening Customer Details for: '{customer_name}'..." if customer_name else "Opening first Customer Details...")
        if customer_name:
            self.search_customer(customer_name)

        target_row = self.page.locator("tbody tr").first
        if customer_name:
            matching = self.page.locator("tbody tr").filter(has_text=customer_name).first
            if matching.count() > 0 and matching.is_visible():
                target_row = matching

        action_cell = target_row.locator("td:last-child")
        eye_icon = action_cell.locator("svg, div.css-1m9jp0d, div.css-ih2uuh")
        if eye_icon.count() > 0 and eye_icon.first.is_visible():
            eye_icon.first.click()
        else:
            action_cell.click()

        self.page.wait_for_timeout(2000)
        try:
            self.page.wait_for_url("**/customers/*", timeout=15000)
        except Exception:
            pass
        logger.info(f"Navigated to Customer Details. Current URL: {self.page.url}")

    def get_customer_detail_profile(self) -> dict:
        """
        Extract profile attributes from /customers/{id} detail page.
        """
        logger.info("Extracting customer detail profile...")
        self.page.wait_for_timeout(1500)
        content_loc = self.page.locator("text='Customer Details', div.chakra-card, main, #root").first
        try:
            content_loc.wait_for(state="visible", timeout=10000)
        except Exception:
            pass
        raw_text = self.page.locator("main, #root").inner_text()

        # Parse common detail fields
        profile = {
            "url": self.page.url,
            "raw_text": raw_text,
        }

        # Extract Customer ID if present (e.g. CUST-006)
        import re
        cust_id_match = re.search(r"CUST-\d+", raw_text)
        if cust_id_match:
            profile["customer_id"] = cust_id_match.group(0)

        logger.info(f"Customer profile details: {profile}")
        return profile
