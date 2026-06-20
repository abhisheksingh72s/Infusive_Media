class CompanyPage:

    def __init__(self, page):
        self.page = page

    def go_to_company(self):
        self.page.get_by_role("link", name="Company").click()
        self.page.wait_for_url("**/company**", timeout=60000)
        self.page.get_by_role("button", name="Add New Company").wait_for(timeout=60000)

    def click_add_new_company_menu(self):
        self.page.get_by_role("button", name="Add New Company").click()

    def click_add_new_company(self):
        self.click_add_new_company_menu()
        self.page.locator("//p[normalize-space()='Add New Company']").click()

    def click_add_new_company_and_poc(self):
        self.click_add_new_company_menu()
        self.page.get_by_text("Add New Company & POC", exact=True).click()
        self.page.get_by_role("button", name="Select Code").wait_for(timeout=60000)

    def click_add_quick_lead(self):
        self.click_add_new_company_menu()
        self.page.get_by_role("menuitem", name="Add Quick Lead").click()
        self.page.get_by_role("textbox", name="Name").wait_for(timeout=60000)
        self.page.wait_for_timeout(2000)

    def select_quick_lead_country_code(self, code):
        self.page.wait_for_timeout(500)
        search_term = code.replace("+", "")
        self.page.get_by_role("button", name="Select Code").click()
        search_input = self.page.get_by_role("textbox", name="Phone Number *")
        search_input.wait_for(state="visible")
        search_input.fill(search_term)
        menu_item = self.page.get_by_role("menuitem").filter(has_text=f"(+{search_term})")
        menu_item.first.wait_for(state="visible")
        menu_item.first.click()

    def fill_quick_lead_form(self, name, email, phone, country, country_code=None):
        if name is not None:
            self.page.get_by_role("textbox", name="Name").fill(name)
        if email is not None:
            self.page.get_by_role("textbox", name="Email").fill(email)
        if country_code is not None:
            self.select_quick_lead_country_code(country_code)
        if phone is not None:
            self.page.get_by_placeholder("Enter Phone").fill(phone)
        if country is not None:
            country_input = self.page.get_by_role("textbox", name="Country *")
            country_input.click()
            country_input.fill(country)
            self.page.wait_for_timeout(1000)
            try:
                self.page.locator("li").filter(has_text=country).first.click(timeout=3000)
            except Exception:
                self.page.keyboard.press("Escape")

    def fill_company_form(self, name, email, phone, website):
        self.page.get_by_role("textbox", name="Company Name").fill(name)
        self.page.get_by_role("textbox", name="Company Email").fill(email)
        self.page.get_by_placeholder("Enter Phone").fill(phone)
        self.page.get_by_role("textbox", name="Website Url").fill(website)

    def select_country_code(self, code):
        self.page.wait_for_timeout(500)
        search_term = code.replace("+", "")
        self.page.get_by_role("button", name="Select Code").click()
        search_input = self.page.get_by_placeholder("Search country or code").last
        search_input.wait_for(state="visible")
        search_input.fill(search_term)
        menu_item = self.page.get_by_role("menuitem").filter(has_text=f"(+{search_term})")
        menu_item.first.wait_for(state="visible")
        menu_item.first.click()
        try:
            self.page.get_by_role("button").filter(has_text=f"(+{search_term})").wait_for(timeout=5000)
        except Exception:
            self.page.get_by_role("button").filter(has_text=search_term).wait_for(timeout=5000)

    def select_poc_country_code(self, index, code):
        import re
        self.page.wait_for_timeout(500)
        btn = self.page.get_by_role("button").filter(has_text=re.compile(r"\(\+\d+\)")).nth(index)
        btn.click()
        search_input = self.page.get_by_placeholder("Search country or code").last
        search_input.wait_for(state="visible")
        search_input.fill(code.replace("+", ""))
        menu_item = self.page.get_by_role("menuitem").filter(has_text=f"({code})")
        menu_item.first.wait_for(state="visible")
        menu_item.first.click()

    def select_service(self, service_name):
        self.page.wait_for_timeout(500)
        self.page.get_by_role("button", name="Select Services").click()
        self.page.get_by_role("menuitem", name=service_name).click()
        self.page.locator(".css-1obpgi7").click()

    def click_next(self):
        self.page.get_by_role("button", name="Next").click()
        self.page.get_by_role("textbox", name="POC Name").wait_for(timeout=60000)

    def fill_poc_form(self, name, email, designation, phone=None, whatsapp=None, linkedin=None):
        self.page.get_by_role("textbox", name="POC Name").fill(name)
        self.page.get_by_role("textbox", name="Email").fill(email)
        self.page.get_by_role("textbox", name="Designation *").click()
        self.page.get_by_text(designation, exact=True).click()
        if phone:
            self.page.get_by_placeholder("Enter Phone Number").fill(phone)
        if whatsapp:
            self.page.get_by_placeholder("Enter WhatsApp Number").fill(whatsapp)
        if linkedin:
            self.page.get_by_role("textbox", name="LinkedIn URL").fill(linkedin)

    def click_save(self):
        self.page.get_by_role("button", name="Save").click()
        try:
            self.page.wait_for_url("**/company**", timeout=15000)
        except Exception:
            self.page.get_by_text("successfully").wait_for(timeout=10000)
            self.page.wait_for_url("**/company**", timeout=10000)
        self.page.locator("tbody tr").first.wait_for(timeout=30000)

    def click_save_quick_lead(self):
        self.page.get_by_role("button", name="Save").click()
        try:
            self.page.wait_for_url("**/company**", timeout=5000)
        except Exception:
            try:
                self.page.get_by_text("successfully", exact=False).wait_for(timeout=5000)
            except Exception:
                pass
            if "quick-lead" in self.page.url:
                try:
                    self.page.get_by_role("button", name="Back").click()
                except Exception:
                    pass
            self.page.wait_for_url("**/company**", timeout=10000)
        self.page.locator("tbody tr").first.wait_for(timeout=30000)

    def is_company_row_visible(self, company_name, email=None, phone=None):
        self.page.locator("tbody tr").first.wait_for(timeout=60000)
        rows = self.page.locator("tbody tr").all()
        
        name_mask = "*" * len(company_name)
        
        for row in rows:
            cells = row.locator("td").all()
            if not cells:
                continue
            
            cell_name = cells[0].inner_text().strip()
            cell_phone = cells[1].inner_text().strip() if len(cells) > 1 else ""
            cell_email = cells[2].inner_text().strip() if len(cells) > 2 else ""
            
            name_matched = False
            if company_name.lower() in cell_name.lower():
                name_matched = True
            elif cell_name == name_mask:
                name_matched = True
                
            if name_matched:
                match_email = True
                match_phone = True
                
                if email:
                    email_mask = email[:4] + "*" * (len(email) - 4)
                    if cell_email != email_mask and email.lower() not in cell_email.lower():
                        match_email = False
                        
                if phone:
                    last_four = phone[-4:] if len(phone) >= 4 else phone
                    phone_mask = "******" + last_four
                    if cell_phone != phone_mask and phone not in cell_phone:
                        match_phone = False
                        
                if match_email and match_phone:
                    return True
                    
        return False

    def click_edit_for_row(self, row_index):
        xpath = f"//tbody/tr[{row_index}]/td[10]/div[1]//*[name()='svg']//*[name()='g' and contains(@fill,'none')]"
        self.page.locator(xpath).click(force=True)

    def update_company_name(self, name):
        field = self.page.get_by_role("textbox", name="Company Name")
        field.click()
        self.page.wait_for_timeout(300)
        field.select_text()
        field.press_sequentially(name, delay=30)

    def click_update(self):
        self.page.get_by_role("button", name="Update").click()
        self.page.wait_for_url("**/company**", timeout=60000)
        self.page.locator("tbody tr").first.wait_for(timeout=60000)

    def capture_toast(self, timeout=5000):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Attempting to capture toast notification...")
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
            logger.info(f"Waiting up to {timeout}ms for toast matching selectors: {combined_selector}")
            self.page.locator(combined_selector).first.wait_for(state="visible", timeout=timeout)
            logger.info("A toast element became visible in the DOM.")
        except Exception:
            logger.info("No toast element became visible within the timeout.")
            pass
            
        texts = []
        for sel in selectors:
            try:
                locs = self.page.locator(sel)
                count = locs.count()
                for i in range(count):
                    el = locs.nth(i)
                    if el.is_visible():
                        txt = el.inner_text().strip()
                        if txt:
                            texts.append(txt)
            except Exception:
                pass
        toast_text = " | ".join(set(texts))
        logger.info(f"Captured Toast Content: '{toast_text}'")
        return toast_text

    def fill_stepper_poc_form(self, index, name, email, designation, phone, country_code="+1", same_as_phone=True):
        self.page.locator(f"input[name='pocs.{index}.name']").fill(name)
        self.page.locator(f"input[name='pocs.{index}.email']").fill(email)
        designation_input = self.page.get_by_placeholder("Enter POC Designation").first
        designation_input.click()
        self.page.get_by_text(designation, exact=True).click()
        self.select_poc_country_code(index, country_code)
        self.page.locator(f"input[name='pocs.{index}.phoneNumber']").fill(phone)
        if same_as_phone:
            self.page.get_by_label("Same as Phone Number").first.click(force=True)

    def click_stepper_next(self):
        self.page.get_by_role("button", name="Next").click()
        self.page.locator("input[name='pocs.0.name']").wait_for(timeout=60000)

    def fill_company_name(self, name):
        self.page.locator("input[name='companyName']").fill(name)
        
    def fill_company_email(self, email):
        self.page.locator("input[name='companyEmail']").fill(email)
        
    def fill_company_phone(self, phone):
        try:
            self.page.locator("input[name='companyPhone']").fill(phone)
        except Exception:
            pass

    def type_quick_lead_name_keyboard(self, text):
        name_input = self.page.get_by_role("textbox", name="Name")
        name_input.click()
        self.page.keyboard.type(text)

    def navigate_to_company_list_if_needed(self):
        url = self.page.url
        if "add-new-company-form" in url:
            base_part = url.split("/add-new-company-form")[0]
            self.page.goto(f"{base_part}/company")
            self.page.wait_for_timeout(2000)
        elif "add-new-company-poc" in url:
            try:
                self.page.get_by_role("button", name="Back").click()
            except Exception:
                base_part = url.split("/add-new-company-poc")[0]
                self.page.goto(f"{base_part}/company")
            self.page.wait_for_timeout(2000)
        elif "quick-lead" in url:
            try:
                self.page.get_by_role("button", name="Back").click()
            except Exception:
                base_part = url.split("/quick-lead")[0]
                self.page.goto(f"{base_part}/company")
            self.page.wait_for_timeout(2000)

    def clear_company_name(self):
        field = self.page.get_by_role("textbox", name="Company Name")
        field.click()
        self.page.wait_for_timeout(300)
        field.select_text()
        self.page.keyboard.press("Backspace")

    def clear_company_email(self):
        field = self.page.get_by_role("textbox", name="Company Email")
        field.click()
        self.page.wait_for_timeout(300)
        field.select_text()
        self.page.keyboard.press("Backspace")

    def update_company_email(self, email):
        field = self.page.get_by_role("textbox", name="Company Email")
        field.click()
        self.page.wait_for_timeout(300)
        field.select_text()
        field.press_sequentially(email, delay=30)

    def get_company_name_value(self):
        return self.page.get_by_role("textbox", name="Company Name").input_value()

    def get_company_email_value(self):
        return self.page.get_by_role("textbox", name="Company Email").input_value()

    def get_element_dimensions(self, locator):
        if isinstance(locator, str):
            locator = self.page.locator(locator)
        locator.first.wait_for(state="attached", timeout=5000)
        box = locator.first.bounding_box()
        if not box:
            return {"width": 0, "height": 0, "x": 0, "y": 0}
        return box

    def get_element_css_property(self, locator, property_name):
        if isinstance(locator, str):
            locator = self.page.locator(locator)
        locator.first.wait_for(state="attached", timeout=5000)
        return locator.first.evaluate(
            "(el, prop) => window.getComputedStyle(el).getPropertyValue(prop)", property_name
        )
