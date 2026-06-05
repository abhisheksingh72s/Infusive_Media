class PagesPage:

    def __init__(self, page):
        self.page = page

    def search(self, keyword):
        self.page.get_by_placeholder("Search Page Name....").fill(keyword)
        self.page.wait_for_timeout(1000)

    def has_no_results(self):
        return self.page.locator("tbody tr").count() == 0

    def go_to_pages(self):
        self.page.get_by_role("link", name="Admin Controller").click()
        self.page.get_by_role("link", name="Pages").click()
        self.page.wait_for_url("**/pages**", timeout=10000)

    def click_add_new(self):
        self.page.get_by_role("button", name="Add New").click()
        self.page.wait_for_url("**/new-page**", timeout=10000)

    def fill_page_form(self, name, label, url):
        self.page.locator("input[name='name']").fill(name)
        self.page.locator("input[name='label']").fill(label)
        self.page.locator("input[name='url']").fill(url)

    def click_save(self):
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_url("**/pages**", timeout=10000)

    def get_row_index(self, row_name, max_pages=50):
        self.page.locator("tbody tr").first.wait_for()
        for _ in range(max_pages):
            rows = self.page.locator("tbody tr").all()
            for i, row in enumerate(rows):
                if row_name.lower() in row.inner_text().lower():
                    return i + 1
            next_btn = self.page.get_by_role("button", name="Next")
            if not next_btn.is_enabled():
                raise ValueError(f"Row '{row_name}' not found")
            next_btn.click()
            self.page.locator("tbody tr").first.wait_for()
        raise ValueError(
            f"Row '{row_name}' not found after paginating through {max_pages} pages"
        )

    def is_row_visible(self, row_name):
        try:
            self.get_row_index(row_name)
            return True
        except ValueError:
            return False

    def click_edit_for_row(self, row_index):
        self.page.locator("tbody tr").nth(row_index - 1).locator("button").first.click()

    def update_page_name(self, name):
        field = self.page.locator("input[name='name']")
        field.clear()
        field.fill(name)
        label_field = self.page.locator("input[name='label']")
        label_field.clear()
        label_field.fill(name)

    def click_update(self):
        self.page.get_by_role("button", name="Update").click()
        self.page.wait_for_url("**/pages**", timeout=10000)

    def click_delete_for_row(self, row_index):
        self.page.locator("tbody tr").nth(row_index - 1).locator("button").last.click()

    def is_delete_popup_visible(self):
        return self.page.get_by_role("alertdialog").is_visible()

    def confirm_delete(self):
        self.page.get_by_role("alertdialog").get_by_role("button", name="Delete").click()
        self.page.get_by_role("alertdialog").wait_for(state="hidden")

    def is_pagination_visible(self):
        return self.page.get_by_role("button", name="Next").is_visible()
