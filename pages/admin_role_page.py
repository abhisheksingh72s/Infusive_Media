class AdminRolePage:

    def __init__(self, page):
        self.page = page

    def search(self, keyword):
        self.page.get_by_placeholder("Search Role Name....").fill(keyword)
        self.page.wait_for_timeout(1000)

    def has_no_results(self):
        return self.page.locator("tbody tr").count() == 0

    def go_to_admin_controller(self):
        self.page.get_by_role("link", name="Admin Controller").click()

    def click_add_new_role(self):
        self.page.get_by_role("button", name="Add New Role").click()
        self.page.wait_for_url("**/new-role**", timeout=60000)

    def fill_role_form(self, name, description):
        self.page.locator("input[name='name']").fill(name)
        self.page.locator("textarea[name='description']").fill(description)

    def click_submit(self):
        self.page.get_by_role("button", name="Submit").click()
        self.page.wait_for_url("**/roles**", timeout=60000)

    def is_role_row_visible(self, role_name, max_pages=50):
        self.page.locator("tbody tr").first.wait_for()
        for _ in range(max_pages):
            rows = self.page.locator("tbody tr").all()
            for row in rows:
                if role_name.lower() in row.inner_text().lower():
                    return True
            next_btn = self.page.get_by_role("button", name="Next")
            if not next_btn.is_enabled():
                return False
            next_btn.click()
            self.page.locator("tbody tr").first.wait_for()
        return False  # Guard: role not found within max_pages limit

    def click_edit_for_role(self, role_name):
        self.is_role_row_visible(role_name)
        self.page.locator(f"tbody tr:has-text('{role_name}')").get_by_role("button").first.click()
        self.page.wait_for_url("**/new-role**", timeout=60000)

    def update_role_name(self, name):
        field = self.page.locator("input[name='name']")
        field.wait_for()
        field.click()
        self.page.wait_for_timeout(300)
        field.select_text()
        field.press_sequentially(name, delay=30)

    def click_update(self):
        self.page.get_by_role("button", name="Update").click()
        self.page.wait_for_url("**/roles**", timeout=60000)
        self.page.locator("tbody tr").first.wait_for()
        # Go back to first page after update
        first_btn = self.page.get_by_role("button", name="1")
        if first_btn.is_visible():
            first_btn.click()
            self.page.locator("tbody tr").first.wait_for()

    def click_delete_for_row_by_name(self, role_name):
        self.is_role_row_visible(role_name)
        self.page.locator(f"tbody tr:has-text('{role_name}')").locator("button").last.click()

    def is_confirm_delete_visible(self):
        return self.page.get_by_role("alertdialog").is_visible()

    def confirm_delete(self):
        self.page.get_by_role("alertdialog").get_by_role("button", name="Delete").click()
        self.page.get_by_role("alertdialog").wait_for(state="hidden")

    def is_breadcrumb_visible(self):
        # TODO: Replace with a specific breadcrumb locator once the DOM selector is confirmed.
        # Suggested alternatives:
        #   self.page.locator("nav[aria-label='breadcrumb']").is_visible()
        #   self.page.get_by_role("navigation", name="breadcrumb").is_visible()
        return self.page.locator("nav").is_visible()

    def is_pagination_visible(self):
        return self.page.get_by_role("button", name="Next").is_visible()
