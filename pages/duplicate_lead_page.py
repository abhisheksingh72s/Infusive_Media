import logging

logger = logging.getLogger(__name__)

class DuplicateLeadPage:
    def __init__(self, page):
        self.page = page
        # Map required locators
        self.lead_module = self.page.locator("//a[text()='Lead']")
        self.duplicate_lead_menu = self.page.locator("//a[@href='/Duplicatelead']")
        self.search_box = self.page.locator("input[placeholder='Search by company, POC or email...']")
        self.duplicate_table = self.page.locator(".chakra-table__container table")
        self.table_rows = self.page.locator(".chakra-table__container table tbody tr")

    def go_to_duplicate_lead(self):
        logger.info("Clicking on Lead module in sidebar...")
        self.lead_module.click()
        logger.info("Clicking on Duplicate Lead sub-menu...")
        self.duplicate_lead_menu.click()
        logger.info("Waiting for duplicate lead page load...")
        self.page.wait_for_url("**/Duplicatelead", timeout=30000)
        self.search_box.wait_for(state="visible", timeout=30000)

    def search_duplicate_lead(self, search_term):
        logger.info(f"Searching for duplicate lead with term: '{search_term}'")
        self.search_box.click()
        self.search_box.fill(search_term)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(2000) # Wait for table to filter

    def is_lead_visible_in_table(self, company_name, email=None, phone=None):
        logger.info(f"Verifying visibility of lead with company: '{company_name}', email: '{email}', phone: '{phone}'")
        try:
            self.table_rows.first.wait_for(state="visible", timeout=10000)
        except Exception:
            logger.warning("No rows found or loaded in the table.")
            return False

        rows = self.table_rows.all()
        for row in rows:
            cells = row.locator("td").all()
            if not cells:
                continue
            cell_texts = [cell.inner_text().strip() for cell in cells]
            row_text = " ".join(cell_texts).lower()
            logger.debug(f"Row content: '{row_text}'")
            if company_name.lower() in row_text:
                if email and email.lower() not in row_text:
                    continue
                if phone and phone not in row_text:
                    continue
                return True
        return False
