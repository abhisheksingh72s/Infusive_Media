import logging

logger = logging.getLogger(__name__)

class AgencyPage:
    """Page Object Model for Master -> Agency module."""

    def __init__(self, page):
        self.page = page

    def go_to_agency(self):
        """Navigate to Master -> Agency module after Admin login."""
        logger.info("Step 1: Admin login completed.")
        self.page.wait_for_timeout(2000)

        # Step 2: Click Master module
        logger.info("Step 2: Clicking Master module via page.get_by_text('Master', exact=True)...")
        master_el = self.page.get_by_text("Master", exact=True)
        if not master_el.is_visible():
            master_el = self.page.get_by_text("Masters", exact=True)
        if not master_el.is_visible():
            master_el = self.page.locator("a[href='/roles']")
        
        master_el.first.click()
        logger.info("Successfully clicked Master module!")
        self.page.wait_for_timeout(1000)

        # Step 3: Click Agency sub-module
        logger.info("Step 3: Clicking Agency sub-module via page.get_by_text('Agency', exact=True)...")
        agency_el = self.page.get_by_text("Agency", exact=True)
        if not agency_el.is_visible():
            agency_el = self.page.get_by_role("link", name="Agency")
        if not agency_el.is_visible():
            agency_el = self.page.locator("a[href*='agency']")
        
        if agency_el.is_visible():
            agency_el.first.click()
            logger.info("Successfully clicked Agency sub-module!")
        else:
            base_url = self.page.url.split("/dashboard")[0]
            self.page.goto(f"{base_url}/agency")

        # Step 4: Verify Agency listing/table is displayed
        logger.info("Step 4: Verifying Agency listing/table is displayed...")
        try:
            self.page.wait_for_url("**/agency**", timeout=15000)
        except Exception:
            pass
        self.page.wait_for_timeout(2000)

    def click_add_options(self):
        """Click Add Options button: page.get_by_role('button', name='Add Options')."""
        logger.info("Clicking Add Options button...")
        self.page.wait_for_timeout(1000)
        btn = self.page.get_by_role("button", name="Add Options")
        if not btn.is_visible():
            btn = self.page.get_by_role("button", name="Add New Agency")
        if not btn.is_visible():
            btn = self.page.get_by_text("Add Options", exact=True)
        if not btn.is_visible():
            btn = self.page.locator("//button[contains(.,'Add Options') or contains(.,'Add')]").first
        btn.click()
        self.page.wait_for_timeout(1000)

    def select_add_new_agency(self):
        """Select Add New Agency from menu: page.get_by_text('Add New Agency', exact=True)."""
        logger.info("Selecting Add New Agency menu item...")
        item = self.page.get_by_text("Add New Agency", exact=True)
        if not item.is_visible():
            item = self.page.get_by_role("menuitem", name="Add New Agency")
        if not item.is_visible():
            item = self.page.locator("p.chakra-text:has-text('Add New Agency')")
        
        if item.is_visible():
            item.first.click()
            self.page.wait_for_timeout(1500)

    def is_add_agency_form_visible(self, timeout=5000):
        """Verify Add New Agency form header or input field is visible."""
        for sel in [
            self.page.get_by_role("textbox", name="Agency Name"),
            self.page.get_by_placeholder("Enter Agency Name"),
            self.page.locator("input[name='agencyName']"),
            self.page.get_by_placeholder("Enter Phone")
        ]:
            try:
                sel.first.wait_for(state="visible", timeout=timeout)
                return True
            except Exception:
                pass
        return False

    def select_country_code(self, code):
        """Select country code for phone number."""
        search_term = code.replace("+", "")
        try:
            self.page.get_by_role("button", name="Select Code").click()
            search_input = self.page.get_by_placeholder("Search country or code").last
            search_input.wait_for(state="visible", timeout=5000)
            search_input.fill(search_term)
            menu_item = self.page.get_by_role("menuitem").filter(has_text=f"(+{search_term})")
            menu_item.first.wait_for(state="visible", timeout=5000)
            menu_item.first.click()
        except Exception:
            pass

    def select_country(self, country_name="United States"):
        """Select country for Agency form."""
        try:
            country_input = self.page.get_by_role("textbox", name="Country")
            if not country_input.is_visible():
                country_input = self.page.get_by_placeholder("Search...")
            if country_input.first.is_visible():
                country_input.first.click()
                country_input.first.fill(country_name)
                self.page.wait_for_timeout(500)
                try:
                    self.page.locator("li").filter(has_text=country_name).first.click(timeout=3000)
                except Exception:
                    self.page.keyboard.press("ArrowDown")
                    self.page.keyboard.press("Enter")
        except Exception:
            pass

    def fill_agency_form(self, agency_name, phone, country_code="+1", country="United States"):
        """Fill all mandatory fields of the Agency form."""
        logger.info(f"Filling Agency Form: Name='{agency_name}', Phone='{phone}', Country='{country}'...")
        
        # Agency Name
        name_input = None
        for sel in [
            self.page.get_by_role("textbox", name="Agency Name"),
            self.page.get_by_placeholder("Enter Agency Name"),
            self.page.locator("input[name='agencyName']"),
            self.page.locator("form input").first
        ]:
            try:
                if sel.first.is_visible(timeout=1500):
                    name_input = sel.first
                    break
            except Exception:
                pass

        if name_input:
            name_input.fill(agency_name)

        # Phone Country Code & Phone Number
        if country_code:
            self.select_country_code(country_code)

        phone_input = None
        for sel in [
            self.page.get_by_placeholder("Enter Phone"),
            self.page.get_by_placeholder("Enter Phone Number"),
            self.page.get_by_role("textbox", name="Agency Phone Number"),
            self.page.get_by_role("textbox", name="Phone"),
            self.page.locator("input[name='phone']"),
            self.page.locator("input[type='tel']"),
            self.page.locator("input[placeholder*='Phone' i]")
        ]:
            try:
                if sel.first.is_visible(timeout=1500):
                    phone_input = sel.first
                    break
            except Exception:
                pass

        if phone_input:
            phone_input.fill(phone)

        # Country
        if country:
            self.select_country(country)

    def click_save_agency(self):
        """Click Save Agency button: page.get_by_role('button', name='Save Agency')."""
        logger.info("Clicking Save Agency button...")
        btn = self.page.get_by_role("button", name="Save Agency")
        if not btn.is_visible():
            btn = self.page.get_by_role("button", name="Save")
        btn.click()

    def capture_toast(self, timeout=5000):
        """Capture toast notification text."""
        selectors = [
            "div[role='status']",
            "div[role='alert']",
            ".toast",
            ".hot-toast",
            "[class*='toast']",
            "[class*='Toast']"
        ]
        combined_selector = ", ".join(selectors)
        try:
            self.page.locator(combined_selector).first.wait_for(state="visible", timeout=timeout)
        except Exception:
            pass
        texts = []
        for sel in selectors:
            try:
                locs = self.page.locator(sel)
                for i in range(locs.count()):
                    el = locs.nth(i)
                    if el.is_visible():
                        txt = el.inner_text().strip()
                        if txt:
                            texts.append(txt)
            except Exception:
                pass
        return " | ".join(set(texts))

    def is_agency_visible_in_table(self, agency_name):
        """Verify created agency is displayed in the table listing."""
        self.page.locator("tbody tr").first.wait_for(timeout=30000)
        rows = self.page.locator("tbody tr").all()
        for row in rows:
            if agency_name.lower() in row.inner_text().lower():
                return True
        return False

    def reload_page(self):
        """Reload the page and wait for table to render."""
        logger.info("Reloading Agency page...")
        self.page.reload()
        self.page.wait_for_timeout(2000)
        try:
            self.page.locator("tbody tr").first.wait_for(timeout=15000)
        except Exception:
            pass

    def search_agency(self, agency_name):
        """Search for agency in the table search input."""
        logger.info(f"Searching for agency: '{agency_name}'...")
        for sel in [
            self.page.get_by_placeholder("Search..."),
            self.page.get_by_placeholder("Search"),
            self.page.locator("input[placeholder*='Search']"),
            self.page.locator("input[type='search']")
        ]:
            try:
                if sel.first.is_visible(timeout=1500):
                    sel.first.click()
                    sel.first.fill("")
                    sel.first.fill(agency_name)
                    self.page.keyboard.press("Enter")
                    self.page.wait_for_timeout(2000)
                    return True
            except Exception:
                pass
        return False

    def click_action_plus_button(self, agency_name=None):
        """Click the green '+' button in the Action column of the agency row (div.css-1ph3qxj)."""
        logger.info(f"Clicking action column '+' button for agency '{agency_name}'...")
        self.page.locator("tbody tr").first.wait_for(timeout=15000)
        
        target_row = None
        if agency_name:
            rows = self.page.locator("tbody tr").all()
            for r in rows:
                if agency_name.lower() in r.inner_text().lower():
                    target_row = r
                    break
        if not target_row:
            target_row = self.page.locator("tbody tr").first

        action_cell = target_row.locator("td").last

        # Target div.css-1ph3qxj directly
        plus_btn = action_cell.locator("div.css-1ph3qxj, .css-1ph3qxj")
        if not plus_btn.is_visible():
            plus_btn = action_cell.get_by_text("+", exact=True)
        if not plus_btn.is_visible():
            plus_btn = action_cell.locator("> *:nth-child(2)")

        if plus_btn.first.is_visible():
            logger.info("Found green '+' button (div.css-1ph3qxj). Clicking it...")
            plus_btn.first.click(force=True)
            self.page.wait_for_timeout(2000)
        else:
            logger.warning("div.css-1ph3qxj not visible, clicking last element in action cell...")
            action_cell.locator("*").last.click(force=True)
            self.page.wait_for_timeout(2000)

    def click_add_agency_poc(self):
        """Click 'Add Agency POC' button."""
        logger.info("Clicking 'Add Agency POC' button...")
        for sel in [
            self.page.get_by_role("button", name="Add Agency POC"),
            self.page.get_by_role("button", name="Add POC"),
            self.page.get_by_text("Add Agency POC", exact=False),
            self.page.get_by_text("Add POC", exact=False),
            self.page.locator("//button[contains(.,'POC') or contains(.,'Poc') or contains(.,'Add')]")
        ]:
            try:
                if sel.first.is_visible(timeout=2000):
                    sel.first.click()
                    self.page.wait_for_timeout(1000)
                    return True
            except Exception:
                pass
        return False

    def fill_agency_poc_form(self, poc_name, poc_email, poc_phone, country_code="+1", designation="Manager"):
        """Fill Agency POC form fields."""
        logger.info(f"Filling Agency POC form: Name='{poc_name}', Email='{poc_email}', Phone='{poc_phone}', Designation='{designation}'...")
        
        # Name
        for sel in [
            self.page.get_by_role("textbox", name="POC Name"),
            self.page.get_by_role("textbox", name="Name"),
            self.page.get_by_placeholder("Enter Name"),
            self.page.get_by_placeholder("Enter POC Name"),
            self.page.locator("input[name*='name']")
        ]:
            try:
                if sel.first.is_visible(timeout=1000):
                    sel.first.fill(poc_name)
                    break
            except Exception:
                pass

        # Email
        for sel in [
            self.page.get_by_role("textbox", name="POC Email"),
            self.page.get_by_role("textbox", name="Email"),
            self.page.get_by_placeholder("Enter Email"),
            self.page.get_by_placeholder("Enter POC Email"),
            self.page.locator("input[name*='email']")
        ]:
            try:
                if sel.first.is_visible(timeout=1000):
                    sel.first.fill(poc_email)
                    break
            except Exception:
                pass

        # Phone Country Code & Phone
        if country_code:
            self.select_country_code(country_code)

        for sel in [
            self.page.get_by_placeholder("Enter Phone"),
            self.page.get_by_placeholder("Enter Phone Number"),
            self.page.get_by_role("textbox", name="Phone"),
            self.page.locator("input[name*='phone']")
        ]:
            try:
                if sel.first.is_visible(timeout=1000):
                    sel.first.fill(poc_phone)
                    break
            except Exception:
                pass

        # Designation
        for sel in [
            self.page.get_by_role("textbox", name="Designation"),
            self.page.get_by_placeholder("Enter Designation"),
            self.page.locator("input[name*='designation']")
        ]:
            try:
                if sel.first.is_visible(timeout=1000):
                    sel.first.fill(designation)
                    break
            except Exception:
                pass

    def click_save_poc(self):
        """Click Save POC button."""
        logger.info("Clicking Save POC button...")
        for sel in [
            self.page.get_by_role("button", name="Save POC"),
            self.page.get_by_role("button", name="Save Poc"),
            self.page.get_by_role("button", name="Save"),
            self.page.locator("//button[contains(.,'Save')]")
        ]:
            try:
                if sel.first.is_visible(timeout=1500):
                    sel.first.click()
                    self.page.wait_for_timeout(1000)
                    return True
            except Exception:
                pass
        return False
