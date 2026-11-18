import logging
import re

logger = logging.getLogger(__name__)


class CompanyPage:

    def __init__(self, page):
        self.page = page

    def go_to_company(self):
        try:
            comp_link = self.page.locator("a:has-text('Companies'), a:has-text('Company'), a[href*='company']").first
            if comp_link.count() > 0 and comp_link.is_visible():
                comp_link.click()
            else:
                self.page.goto("https://infusive-front.jobvritta.com/company", wait_until="domcontentloaded")
        except Exception:
            self.page.goto("https://infusive-front.jobvritta.com/company", wait_until="domcontentloaded")

        self.page.wait_for_url("**/company**", timeout=60000)
        self.page.get_by_role("button", name="Add New Company").wait_for(timeout=60000)

    def search_company(self, query: str):
        """Search company by name or email in Company list table."""
        logger.info(f"Searching Company table for: '{query}'...")
        search_box = self.page.locator("input[placeholder*='Search' i], input[type='search'], input[name*='search' i]").first
        if search_box.is_visible():
            search_box.fill(query)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(2000)

    def click_add_new_company_menu(self):
        try:
            self.page.evaluate("() => document.querySelectorAll('.chakra-toast, [class*=\"chakra-toast\"]').forEach(el => el.remove())")
        except Exception:
            pass
        self.page.get_by_role("button", name="Add New Company").click()

    def click_add_new_company(self):
        self.click_add_new_company_menu()
        self.page.locator("//p[normalize-space()='Add New Company']").click()

    def click_add_new_company_and_poc(self):
        self.click_add_new_company_menu()
        self.page.get_by_text("Add New Company & POC", exact=True).click()
        self.page.get_by_role("button", name="Select Code").wait_for(timeout=60000)

    def click_add_quick_lead(self):
        try:
            self.page.evaluate("() => document.querySelectorAll('.chakra-toast, [class*=\"chakra-toast\"]').forEach(el => el.remove())")
        except Exception:
            pass

        if "/quick-lead" not in self.page.url:
            try:
                self.click_add_new_company_menu()
                self.page.wait_for_timeout(400)
                self.page.get_by_role("menuitem", name="Add Quick Lead").click(timeout=5000)
            except Exception:
                self.page.goto("https://infusive-front.jobvritta.com/quick-lead", wait_until="domcontentloaded")

        try:
            self.page.wait_for_url("**/quick-lead**", timeout=15000)
        except Exception:
            self.page.goto("https://infusive-front.jobvritta.com/quick-lead", wait_until="domcontentloaded")
            self.page.wait_for_url("**/quick-lead**", timeout=15000)

        name_loc = self.page.locator("input[name='Name'], input[placeholder*='Name']").first
        name_loc.wait_for(state="visible", timeout=30000)
        self.page.wait_for_timeout(500)

    def select_quick_lead_country_code(self, code, country=None):
        """
        Open the Country Code dropdown in the Phone Number field and select the code.
        Uses exact ISO/dial code matching to prevent US-overwriting.
        """
        self.page.wait_for_timeout(300)
        iso_map = {
            "united states": ("US (+1)", "US", "+1"),
            "united kingdom": ("GB (+44)", "GB", "+44"),
            "india": ("IN (+91)", "IN", "+91"),
            "canada": ("CA (+1)", "CA", "+1"),
            "australia": ("AU (+61)", "AU", "+61"),
            "germany": ("DE (+49)", "DE", "+49"),
            "france": ("FR (+33)", "FR", "+33"),
            "united arab emirates": ("AE (+971)", "AE", "+971"),
            "singapore": ("SG (+65)", "SG", "+65"),
            "japan": ("JP (+81)", "JP", "+81"),
        }

        # 1. Locate the menu button for Phone Number Country Code
        phone_control = self.page.locator(".chakra-form-control:has(label:has-text('Phone Number'))")
        btn = phone_control.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
        if btn.count() == 0 or not btn.is_visible():
            btn = self.page.locator("button:has-text('Select Code'), button[id^='menu-button-']").first

        # 2. Check if search input is already open; if not, click button to open menu
        search_input = self.page.locator("input[placeholder='Search country or code']").first
        if search_input.count() == 0 or not search_input.is_visible():
            btn.scroll_into_view_if_needed()
            btn.click()
            self.page.wait_for_timeout(300)
            if search_input.count() == 0 or not search_input.is_visible():
                search_input = self.page.locator(".chakra-menu__menu-list input").first

        search_input.wait_for(state="visible", timeout=5000)

        # Determine target item text and search keyword
        target_text = None
        search_term = code.replace("+", "").strip() if code else ""
        if country:
            c_key = country.strip().lower()
            if c_key in iso_map:
                target_text, iso_code, dial = iso_map[c_key]
                search_term = iso_code

        search_input.fill(search_term)
        self.page.wait_for_timeout(400)

        # 3. Select matching item
        if target_text:
            target_loc = self.page.locator("[role='menuitem']").filter(has_text=target_text).first
            if target_loc.is_visible():
                target_loc.click()
                self.page.wait_for_timeout(300)
                return

        clean_dial = f"(+{code.replace('+', '').strip()})"
        menu_item = self.page.locator("[role='menuitem']").filter(has_text=clean_dial).first
        if not menu_item.is_visible():
            menu_item = self.page.locator("[role='menuitem']").filter(has_text=search_term).first
        menu_item.wait_for(state="visible", timeout=5000)
        menu_item.click()
        self.page.wait_for_timeout(300)

    def fill_quick_lead_form(self, name, email, phone, country, service=None, country_code=None):
        """
        Fill Add Quick Lead form per user-specified CRM behavior:
          1. Name (Generic Corporate Name)
          2. Email
          3. Country * -> Selecting Country automatically populates the matching Country Code!
          4. Phone Number -> Just enter the number (no need to open country code dropdown)
          5. Service Interested In -> Select the requested service (e.g. PPC, Meta Ads, SEO)
        """
        logger.info(f"Filling Quick Lead form: Name -> Email -> Country (auto-sets Code) -> Phone Number -> Service...")

        # 1. NAME (Generic Corporate Name)
        if name is not None:
            name_input = self.page.locator("input[placeholder='Enter  Name'], input[placeholder='Enter Name'], input[name='Name']").first
            if name_input.count() == 0 or not name_input.is_visible():
                name_input = self.page.get_by_role("textbox", name="Name")
            name_input.fill(name)
            self.page.wait_for_timeout(300)

        # 2. EMAIL
        if email is not None:
            email_input = self.page.locator("input[placeholder='Enter Email'], input[name='Email']").first
            if email_input.count() == 0 or not email_input.is_visible():
                email_input = self.page.get_by_role("textbox", name="Email")
            email_input.fill(email)
            self.page.wait_for_timeout(300)

        # 3. COUNTRY * (Selecting Country automatically populates the Country Code!)
        if country is not None:
            try:
                self.page.evaluate("() => document.querySelectorAll('.chakra-toast, [class*=\"chakra-toast\"], .css-1hyhc6u').forEach(el => el.remove())")
            except Exception:
                pass
            country_control = self.page.locator(".chakra-form-control:has(label:has-text('Country'))")
            country_input = country_control.locator("input[placeholder='Search...']").first
            if country_input.count() == 0 or not country_input.is_visible():
                country_input = self.page.locator("input[placeholder='Search...']").first
            if country_input.count() == 0 or not country_input.is_visible():
                country_input = self.page.get_by_role("textbox", name="Country *")

            country_input.click(force=True)
            country_input.fill(country)
            self.page.wait_for_timeout(600)

            exact_opt = self.page.locator("li, [role='option']").filter(has_text=re.compile(f"^{re.escape(country)}$", re.IGNORECASE)).first
            if exact_opt.count() > 0 and exact_opt.is_visible():
                exact_opt.click(force=True)
            else:
                partial_opt = self.page.locator("li, [role='option']").filter(has_text=country).first
                if partial_opt.count() > 0 and partial_opt.is_visible():
                    partial_opt.click(force=True)
                else:
                    self.page.keyboard.press("ArrowDown")
                    self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(500)

        # 4. PHONE NUMBER (Enter Phone - country code was auto-populated by Country)
        if phone is not None:
            phone_input = self.page.locator("input[placeholder='Enter Phone'], input[name='phoneNumber']").first
            phone_input.fill(phone)
            self.page.wait_for_timeout(300)

        # 5. SERVICE INTERESTED IN
        if service is not None:
            svc_btn = self.page.locator(".chakra-form-control:has(label:has-text('Service Interested In')) button, button:has-text('Select Services')").first
            if svc_btn.is_visible():
                svc_btn.click()
                self.page.wait_for_timeout(400)
                item = self.page.locator(f"[role='menuitem']:has-text('{service}'), [role='option']:has-text('{service}')").first
                if item.is_visible():
                    item.click()
                    logger.info(f"Selected Quick Lead service: '{service}'")
                    self.page.wait_for_timeout(300)
                else:
                    self.page.keyboard.press("Escape")

    def fill_company_form(
        self,
        name=None,
        email=None,
        phone=None,
        website=None,
        poc_name=None,
        country_code=None,
        country=None,
        lead_source=None,
        service=None,
        note=None
    ):
        if name:
            self.fill_company_name(name)
        if email:
            self.fill_company_email(email)
        if phone:
            self.fill_company_phone(phone)
        if website:
            try:
                self.page.get_by_role("textbox", name="Website Url").fill(website)
            except Exception:
                pass
        if poc_name:
            self.fill_poc_name(poc_name)
        # Select Country FIRST so reactive country change auto-derives country_code
        if country:
            self.select_country(country)
            self.page.wait_for_timeout(500)
        elif country_code:
            self.select_country_code(country_code)
            self.page.wait_for_timeout(300)
        if service:
            self.select_service(service)
        if lead_source:
            self.select_lead_source(lead_source)
        if note:
            self.fill_note(note)

    def fill_poc_name(self, poc_name):
        self.page.wait_for_timeout(300)
        for loc in [
            self.page.get_by_role("textbox", name="POC Name *"),
            self.page.get_by_placeholder("Enter POC Name"),
            self.page.get_by_role("textbox", name="POC Name"),
            self.page.locator("input[name='pocName']"),
            self.page.locator("input[name='pocs.0.name']"),
        ]:
            try:
                if loc.first.is_visible():
                    loc.first.fill(poc_name)
                    return
            except Exception:
                pass

    def select_country(self, country_name="United States"):
        self.page.wait_for_timeout(300)
        try:
            label = self.page.locator("label").filter(has_text="Country").first
            if label.is_visible():
                for_id = label.get_attribute("for")
                if for_id:
                    country_input = self.page.locator(f"#{for_id}")
                else:
                    country_input = label.locator("..").locator("input").first
                country_input.scroll_into_view_if_needed()
                country_input.click()
                self.page.keyboard.type(country_name)
                self.page.wait_for_timeout(500)
                try:
                    option = self.page.locator("[role='option'], .chakra-select__option, li").filter(has_text=country_name).first
                    if option.is_visible():
                        option.click()
                        return
                except Exception:
                    pass
                self.page.keyboard.press("ArrowDown")
                self.page.keyboard.press("Enter")
                return
        except Exception:
            pass

        try:
            country_input = self.page.get_by_role("textbox", name="Country *")
            if not country_input.is_visible():
                country_input = self.page.get_by_placeholder("Search...").nth(1)
            if country_input.is_visible():
                country_input.click()
                country_input.fill(country_name)
                self.page.wait_for_timeout(500)
                try:
                    self.page.locator("li").filter(has_text=country_name).first.click(timeout=3000)
                except Exception:
                    self.page.keyboard.press("ArrowDown")
                    self.page.keyboard.press("Enter")
        except Exception:
            pass

    def select_lead_source(self, source_name="website"):
        self.page.wait_for_timeout(500)
        label = self.page.locator("label").filter(has_text="Lead Source").first
        label.wait_for(state="visible", timeout=10000)
        
        for_id = label.get_attribute("for")
        if for_id:
            lead_input = self.page.locator(f"#{for_id}")
        else:
            lead_input = self.page.locator("label").filter(has_text="Lead Source").locator("..").locator("input").first
            
        lead_input.scroll_into_view_if_needed()
        lead_input.click()
        self.page.wait_for_timeout(500)
        
        self.page.keyboard.type(source_name)
        self.page.wait_for_timeout(500)
        
        try:
            option = self.page.locator("[role='option'], .chakra-select__option, li").filter(has_text=source_name).first
            if option.is_visible():
                option.click()
                return
        except Exception:
            pass

        try:
            option = self.page.get_by_text(source_name, exact=False).first
            if option.is_visible():
                option.click()
                return
        except Exception:
            pass

        self.page.keyboard.press("ArrowDown")
        self.page.wait_for_timeout(200)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(500)

    def fill_note(self, text="Presales Test Note"):
        self.page.wait_for_timeout(500)
        jodit = self.page.locator("div.jodit-wysiwyg[contenteditable='true']")
        if not jodit.first.is_visible():
            jodit = self.page.locator("//p[contains(.,'Note/Response')]/following::div[contains(@class,'jodit-wysiwyg')][1]")
        if not jodit.first.is_visible():
            jodit = self.page.locator("div.jodit-wysiwyg")
            
        if jodit.first.is_visible():
            jodit.first.click()
            jodit.first.fill(text)
            return

        for sel in [
            self.page.get_by_role("textbox", name="Note"),
            self.page.get_by_role("textbox", name="Notes"),
            self.page.get_by_placeholder("Start typing..."),
            self.page.get_by_placeholder("Enter Note"),
            self.page.get_by_placeholder("Enter Notes"),
            self.page.get_by_placeholder("Note"),
            self.page.locator("textarea[name*='note']"),
            self.page.locator("input[name*='note']"),
        ]:
            try:
                if sel.first.is_visible():
                    sel.first.fill(text)
                    return
            except Exception:
                pass

    def select_country_code(self, code):
        self.page.wait_for_timeout(500)
        search_term = code.replace("+", "").strip()
        btn = self.page.locator("button:has-text('Select Code')").first
        if not btn.is_visible():
            active_btn = self.page.locator("button.chakra-menu__menu-button").first
            if active_btn.is_visible() and f"(+{search_term})" in active_btn.inner_text():
                logger.info(f"Country code (+{search_term}) already selected.")
                return
            btn = active_btn
        if not btn.is_visible():
            btn = self.page.get_by_role("button", name="Select Code")

        btn.click()
        search_input = self.page.locator("input[placeholder='Search country or code']").last
        search_input.wait_for(state="visible", timeout=5000)
        search_input.fill(search_term)
        menu_item = self.page.get_by_role("menuitem").filter(has_text=f"(+{search_term})").first
        if not menu_item.is_visible():
            menu_item = self.page.get_by_role("menuitem").filter(has_text=search_term).first
        menu_item.first.wait_for(state="visible", timeout=5000)
        menu_item.first.click()
        try:
            self.page.get_by_role("button").filter(has_text=f"(+{search_term})").wait_for(timeout=5000)
        except Exception:
            self.page.get_by_role("button").filter(has_text=search_term).wait_for(timeout=5000)

    def select_poc_country_code(self, index, code):
        import re
        self.page.wait_for_timeout(500)
        search_term = code.replace("+", "")
        btn = self.page.get_by_role("button", name="Select Code")
        if not btn.first.is_visible():
            btn = self.page.get_by_role("button").filter(has_text=re.compile(r"\(\+\d+\)"))
        if btn.count() > index and btn.nth(index).is_visible():
            btn.nth(index).click()
        elif btn.first.is_visible():
            btn.first.click()
        else:
            try:
                self.page.get_by_role("button").filter(has_text="Code").first.click()
            except Exception:
                pass

        try:
            search_input = self.page.get_by_placeholder("Search country or code").last
            search_input.wait_for(state="visible", timeout=5000)
            search_input.fill(search_term)
            menu_item = self.page.get_by_role("menuitem").filter(has_text=f"({code})")
            if not menu_item.first.is_visible():
                menu_item = self.page.get_by_role("menuitem").filter(has_text=f"(+{search_term})")
            menu_item.first.wait_for(state="visible", timeout=5000)
            menu_item.first.click()
        except Exception:
            pass

    def select_service(self, service_name):
        self.page.wait_for_timeout(500)
        self.page.get_by_role("button", name="Select Services").click()
        self.page.get_by_role("menuitem", name=service_name).click()
        self.page.get_by_role("textbox", name="Company Name").click()

    def click_next(self):
        self.page.get_by_role("button", name="Next", exact=True).click()
        try:
            self.page.locator("input[name='pocs.0.name']").wait_for(timeout=15000)
        except Exception:
            try:
                self.page.get_by_placeholder("Enter POC Name").wait_for(timeout=15000)
            except Exception:
                self.page.get_by_role("textbox", name="POC Name").wait_for(timeout=15000)

    def fill_poc_form(self, name, email, designation, phone=None, whatsapp=None, linkedin=None):
        poc_name_loc = self.page.locator("input[name='pocs.0.name']")
        if not poc_name_loc.is_visible():
            poc_name_loc = self.page.get_by_placeholder("Enter POC Name")
        if not poc_name_loc.is_visible():
            poc_name_loc = self.page.get_by_role("textbox", name="POC Name")
        poc_name_loc.fill(name)

        poc_email_loc = self.page.locator("input[name='pocs.0.email']")
        if not poc_email_loc.is_visible():
            poc_email_loc = self.page.get_by_placeholder("Enter Email")
        if not poc_email_loc.is_visible():
            poc_email_loc = self.page.get_by_role("textbox", name="Email")
        poc_email_loc.fill(email)

        designation_input = self.page.get_by_placeholder("Enter POC Designation").first
        if not designation_input.is_visible():
            designation_input = self.page.get_by_role("textbox", name="Designation *")
        designation_input.click()

        clean_desig = designation.rstrip(".")
        try:
            self.page.get_by_text(clean_desig, exact=True).first.click(timeout=3000)
        except Exception:
            try:
                self.page.get_by_text(clean_desig, exact=False).first.click(timeout=3000)
            except Exception:
                self.page.keyboard.press("ArrowDown")
                self.page.keyboard.press("Enter")

        if phone:
            phone_loc = self.page.locator("input[name='pocs.0.phoneNumber']")
            if not phone_loc.is_visible():
                phone_loc = self.page.get_by_placeholder("Enter Phone Number")
            if not phone_loc.is_visible():
                phone_loc = self.page.get_by_placeholder("Enter Phone")
            phone_loc.fill(phone)
        if whatsapp:
            whatsapp_loc = self.page.locator("input[name='pocs.0.whatsappNumber']")
            if not whatsapp_loc.is_visible():
                whatsapp_loc = self.page.get_by_placeholder("Enter WhatsApp Number")
            whatsapp_loc.fill(whatsapp)
        if linkedin:
            linkedin_loc = self.page.locator("input[name='pocs.0.linkedinUrl']")
            if not linkedin_loc.is_visible():
                linkedin_loc = self.page.get_by_role("textbox", name="LinkedIn URL")
            linkedin_loc.fill(linkedin)

    def click_edit_for_row(self, row_index):
        row = self.page.locator("tbody tr").nth(row_index - 1)
        row.wait_for(state="visible", timeout=15000)
        
        selectors = [
            f"//tbody/tr[{row_index}]/td[last()]//button",
            f"//tbody/tr[{row_index}]/td[last()]//*[name()='svg']",
            f"//tbody/tr[{row_index}]/td[10]/div[1]//*[name()='svg']",
            f"//tbody/tr[{row_index}]/td[10]/div[1]//*[name()='svg']//*[name()='g' and contains(@fill,'none')]"
        ]
        
        for sel in selectors:
            try:
                loc = self.page.locator(sel)
                if loc.first.is_visible(timeout=2000):
                    loc.first.click(force=True)
                    return
            except Exception:
                pass
                
        try:
            btn = row.locator("button, svg").last
            if btn.is_visible():
                btn.click(force=True)
                return
        except Exception:
            pass

        xpath = f"//tbody/tr[{row_index}]/td[10]/div[1]//*[name()='svg']//*[name()='g' and contains(@fill,'none')]"
        self.page.locator(xpath).click(force=True)

    def fill_stepper_poc_form(self, index, name, email, designation, phone, country_code="+1", same_as_phone=True):
        self.page.locator(f"input[name='pocs.{index}.name']").fill(name)
        self.page.locator(f"input[name='pocs.{index}.email']").fill(email)
        designation_input = self.page.get_by_placeholder("Enter POC Designation").first
        designation_input.click()
        clean_desig = designation.rstrip(".")
        try:
            self.page.get_by_text(clean_desig, exact=True).first.click(timeout=3000)
        except Exception:
            try:
                self.page.get_by_text(clean_desig, exact=False).first.click(timeout=3000)
            except Exception:
                self.page.keyboard.press("ArrowDown")
                self.page.keyboard.press("Enter")

        self.select_poc_country_code(index, country_code)
        self.page.locator(f"input[name='pocs.{index}.phoneNumber']").fill(phone)
        if same_as_phone:
            self.page.get_by_label("Same as Phone Number").first.click(force=True)

    def click_save(self):
        self.page.get_by_role("button", name="Save").click()
        try:
            self.page.wait_for_url("**/company**", timeout=15000)
        except Exception:
            self.page.get_by_text("successfully").wait_for(timeout=10000)
            self.page.wait_for_url("**/company**", timeout=10000)
        self.page.locator("tbody tr").first.wait_for(timeout=30000)

    def click_save_quick_lead(self):
        save_btn = self.page.get_by_role("button", name="Save")
        save_btn.scroll_into_view_if_needed()
        save_btn.click()
        try:
            self.page.wait_for_url("**/company**", timeout=15000)
        except Exception:
            try:
                self.page.get_by_text("successfully", exact=False).wait_for(timeout=5000)
            except Exception:
                pass
            if "quick-lead" not in self.page.url:
                try:
                    self.page.wait_for_url("**/company**", timeout=10000)
                except Exception:
                    pass
        try:
            self.page.locator("tbody tr").first.wait_for(timeout=30000)
        except Exception:
            pass

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

    # -------------------------------------------------------------------------
    # ROW-LEVEL POC MANAGEMENT ON COMPANY LIST PAGE (/company)
    # -------------------------------------------------------------------------

    def expand_company_pocs(self, company_name: str):
        """
        Click the user icon next to the specified company row to expand its POCs sub-table.
        """
        logger.info(f"Expanding POCs for company: '{company_name}'...")
        # Check if already expanded
        add_btn = self.page.locator("button:has-text('Add New POC')").first
        if add_btn.is_visible():
            logger.info("POC sub-table is already expanded.")
            return

        row = self.page.locator("tbody tr").filter(has_text=company_name).first
        row.wait_for(state="visible", timeout=20000)
        user_icon = row.locator("img[src*='user-icon']").first
        if not user_icon.is_visible():
            user_icon = row.locator("img.css-1bkxj8e, button:has(img)").first
        user_icon.scroll_into_view_if_needed()
        user_icon.click()
        self.page.wait_for_timeout(1000)
        # Wait for the expanded row containing 'Add New POC' button
        self.page.locator("button:has-text('Add New POC')").first.wait_for(state="visible", timeout=15000)
        logger.info(f"Successfully expanded POCs for '{company_name}'.")

    def click_add_new_poc_button(self):
        """
        Click the 'Add New POC' button within the expanded company POC section.
        """
        logger.info("Clicking 'Add New POC' button...")
        btn = self.page.locator("button:has-text('Add New POC')").first
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        self.page.locator("form#poc-form, input[name='pocs.0.name']").first.wait_for(state="visible", timeout=15000)
        logger.info("'Add new POC' form opened.")

    def click_add_more_poc_button(self, expected_next_index: int = 1):
        """
        Click 'Add More POC' button on #poc-form to append another POC block.
        """
        logger.info(f"Clicking 'Add More POC' button (waiting for block {expected_next_index})...")
        btn = self.page.locator("button:has-text('Add More POC')").first
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        self.page.locator(f"input[name='pocs.{expected_next_index}.name']").wait_for(state="visible", timeout=10000)
        logger.info(f"POC block {expected_next_index} appended.")

    def select_row_poc_country_code(self, code: str, index: int = 0):
        """
        Select country code in the Phone Number dropdown on the Add new POC form.
        """
        logger.info(f"Selecting POC phone country code for block {index}: '{code}'...")
        clean_code = code.replace("+", "").strip()
        menu_btn = self.page.locator("form#poc-form button[id^='menu-button-']").nth(index)
        if menu_btn.is_visible():
            btn_text = menu_btn.inner_text().strip()
            if f"+{clean_code}" in btn_text:
                logger.info(f"Country code (+{clean_code}) already selected on button.")
                return
            menu_btn.click()
            self.page.wait_for_timeout(300)
            search_input = self.page.locator("input[placeholder='Search country or code']:visible").first
            search_input.wait_for(state="visible", timeout=5000)
            search_input.fill(clean_code)
            self.page.wait_for_timeout(300)
            target = self.page.locator("button[role='menuitem']:visible").filter(has_text=f"(+{clean_code})").first
            if not target.is_visible():
                target = self.page.locator("button[role='menuitem']:visible").filter(has_text=clean_code).first
            target.wait_for(state="visible", timeout=5000)
            target.click()
            self.page.wait_for_timeout(300)

    def fill_add_new_poc_form(
        self,
        name: str,
        email: str,
        designation: str = "Manager",
        phone: str = None,
        country_code: str = None,
        whatsapp: str = None,
        same_as_phone: bool = True,
        alt_phone: str = None,
        alt_email: str = None,
        linkedin: str = None,
        index: int = 0,
    ):
        """
        Fill a POC block inside the dedicated Add New POC form (#poc-form).
        Supports multi-POC addition via block index (pocs.0, pocs.1, ...).
        """
        logger.info(f"Filling Add New POC block {index} for '{name}' ({email})...")

        # Wait for Company input to be populated (takes ~1s for React to resolve GET /Dropdown/company)
        if index == 0:
            comp_input = self.page.locator("input[placeholder*='Select Company' i]").first
            for _ in range(25):
                if comp_input.input_value():
                    break
                self.page.wait_for_timeout(200)

        # 1. POC Name
        name_input = self.page.locator(f"input[name='pocs.{index}.name']")
        name_input.wait_for(state="visible", timeout=10000)
        name_input.fill(name)

        # 2. Email
        self.page.locator(f"input[name='pocs.{index}.email']").fill(email)

        # 3. Designation (Must click rendered autocomplete list item to set designationId!)
        desig_input = self.page.locator("input[placeholder*='Designation' i]").nth(index)
        desig_input.click()
        desig_input.fill(designation)
        self.page.wait_for_timeout(400)
        li_option = self.page.locator("ul.css-155za0w li, li.css-wnxomm").filter(has_text=designation).first
        if li_option.is_visible():
            li_option.click()
        else:
            self.page.keyboard.press("ArrowDown")
            self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(200)

        # 4. Country Code & Phone
        if country_code:
            self.select_row_poc_country_code(country_code, index=index)
        if phone:
            self.page.locator(f"input[name='pocs.{index}.phoneNumber']").fill(phone)

        # 5. WhatsApp
        if same_as_phone:
            cb = self.page.locator("label.chakra-checkbox:has-text('Same as Phone Number')").nth(index)
            if cb.is_visible():
                cb.click()
        elif whatsapp:
            self.page.locator(f"input[name='pocs.{index}.whatsapp']").fill(whatsapp)

        # 6. Alternative Phone / Email / LinkedIn
        if alt_phone:
            self.page.locator(f"input[name='pocs.{index}.alternativePhone']").fill(alt_phone)
        if alt_email:
            self.page.locator(f"input[name='pocs.{index}.alternativeEmail']").fill(alt_email)
        if linkedin:
            self.page.locator(f"input[name='pocs.{index}.linkedinUrl']").fill(linkedin)

        self.page.wait_for_timeout(300)

    def save_add_new_poc_form(self):
        """
        Click the Save button for #poc-form and wait for completion.
        """
        logger.info("Saving Add New POC form...")
        save_btn = self.page.locator("button[form='poc-form'], button[type='submit']:has-text('Save')").first
        save_btn.scroll_into_view_if_needed()

        try:
            with self.page.expect_response(lambda res: "CompanyPoc/addUpdatepoc" in res.url, timeout=20000) as resp_info:
                save_btn.click()
            res = resp_info.value
            logger.info(f"CompanyPoc/addUpdatepoc response: status={res.status}")
        except Exception as e:
            logger.warning(f"Response wait exception: {e}")
            save_btn.click()

        self.page.wait_for_timeout(2000)
        # Check for success toast or form closure
        try:
            self.page.locator("form#poc-form").wait_for(state="hidden", timeout=10000)
        except Exception:
            pass
        logger.info("Add New POC form submitted.")

    def is_poc_visible_in_expanded_table(self, poc_name: str) -> bool:
        """
        Verify that a POC row with poc_name exists in the currently expanded POC table.
        """
        expanded_table = self.page.locator("tr.css-1rhyb73 table, td.css-1vmvwla table").first
        if not expanded_table.is_visible():
            return False
        matches = expanded_table.locator("tbody tr").filter(has_text=poc_name)
        return matches.count() > 0
