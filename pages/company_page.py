class CompanyPage:

    def __init__(self, page):
        self.page = page

    def go_to_company(self):
        self.page.get_by_role("link", name="Company").click()
        self.page.wait_for_url("**/company**", timeout=60000)
        self.page.locator("tbody tr").first.wait_for(timeout=60000)

    def click_add_new_company_menu(self):
        self.page.get_by_role("button", name="Add New Company").click()

    def click_add_new_company(self):
        self.click_add_new_company_menu()
        self.page.locator("//p[normalize-space()='Add New Company']").click()

    def click_add_new_company_and_poc(self):
        self.click_add_new_company_menu()
        self.page.get_by_text("Add New Company & POC", exact=True).click()
        self.page.get_by_role("button", name="Select Code").wait_for(timeout=60000)

    def fill_company_form(self, name, email, phone, website):
        self.page.get_by_role("textbox", name="Company Name").fill(name)
        self.page.get_by_role("textbox", name="Company Email").fill(email)
        self.page.get_by_placeholder("Enter Phone").fill(phone)
        self.page.get_by_role("textbox", name="Website Url").fill(website)

    def select_country_code(self, code):
        search_term = code.replace("+", "")
        self.page.get_by_role("button", name="Select Code").click()
        self.page.get_by_placeholder("Search country or code").fill(search_term)
        self.page.get_by_role("menuitem", name=f"IN (+{search_term})").click()
        self.page.get_by_role("button").filter(has_text=f"(+{search_term})").wait_for()

    def select_service(self, service_name):
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
            self.page.get_by_role("textbox", name="WhatsApp").fill(whatsapp)
        if linkedin:
            self.page.get_by_role("textbox", name="LinkedIn URL").fill(linkedin)

    def click_save(self):
        self.page.get_by_role("button", name="Save").click()
        self.page.get_by_text("successfully").wait_for(timeout=60000)
        self.page.wait_for_url("**/company**", timeout=60000)
        self.page.locator("tbody tr").first.wait_for(timeout=60000)

    def is_company_row_visible(self, company_name):
        self.page.locator("tbody tr").first.wait_for(timeout=60000)
        while True:
            rows = self.page.locator("tbody tr").all()
            for row in rows:
                if company_name.lower() in row.inner_text().lower():
                    return True
            next_btn = self.page.get_by_role("button", name="Next")
            if not next_btn.is_enabled():
                return False
            next_btn.click()
            self.page.locator("tbody tr").first.wait_for(timeout=60000)
