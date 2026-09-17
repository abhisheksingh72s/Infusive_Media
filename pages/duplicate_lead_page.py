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
        logger.info("Navigating to Duplicate Lead page...")
        dup_link = self.page.locator("a[href='/Duplicatelead'], a[href*='Duplicate'], a[href*='duplicate']")
        if dup_link.count() > 0 and dup_link.first.is_visible():
            dup_link.first.click()
        else:
            lead_lnk = self.page.get_by_role("link", name="Lead")
            if lead_lnk.count() == 0 or not lead_lnk.first.is_visible():
                lead_lnk = self.page.locator("//a[contains(., 'Lead')]")
            if lead_lnk.count() > 0 and lead_lnk.first.is_visible():
                lead_lnk.first.click()
                self.page.wait_for_timeout(1000)
            
            dup_link = self.page.locator("a[href='/Duplicatelead'], a[href*='Duplicate'], a[href*='duplicate']")
            if dup_link.count() > 0 and dup_link.first.is_visible():
                dup_link.first.click()
            else:
                try:
                    self.page.get_by_role("link", name="Duplicate Lead").click()
                except Exception:
                    base_url = self.page.url.split("/company")[0].split("/dashboard")[0]
                    self.page.goto(f"{base_url}/Duplicatelead")

        try:
            self.page.wait_for_url("**/Duplicatelead**", timeout=15000)
        except Exception:
            pass
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
