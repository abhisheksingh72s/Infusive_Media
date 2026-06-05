class UsersPage:

    def __init__(self, page):
        self.page = page

    def go_to_users(self):
        self.page.get_by_role("link", name="Admin Controller").click()
        self.page.get_by_role("link", name="• Users").click()
        # Use a flexible wait as the URL might be /users or similar
        self.page.wait_for_load_state("networkidle")

    def click_add_new_user(self):
        self.page.get_by_role("button", name="Add New User").click()
        self.page.get_by_role("dialog", name="Add New User").wait_for(state="visible")

    def is_add_user_dialog_visible(self):
        return self.page.get_by_role("dialog", name="Add New User").is_visible()

    def fill_user_details(self, user_id, name, email, password, mobile):
        dialog = self.page.get_by_role("dialog", name="Add New User")
        
        # Step 1: User Id
        dialog.get_by_label("User Id", exact=False).fill(user_id)
        
        # Click the first submit button (to validate/fetch user and advance to step 2)
        # Using .first because in Step 2 there are two Submit buttons ("Submit" and "Cancel" and "Submit" again)
        # Actually in step 1 there's only one.
        dialog.get_by_role("button", name="Submit").first.click()
        
        if not user_id:
            # Cannot advance without a User Id
            return
            
        # Wait for Step 2 to render
        try:
            dialog.get_by_label("Name", exact=False).wait_for(timeout=3000)
        except Exception:
            # If Step 2 didn't load (e.g., 'User not found' error), we can't fill the rest.
            return
            
        # Step 2: Fill remaining fields
        dialog.get_by_label("Name", exact=False).fill(name)
        dialog.get_by_label("Email", exact=False).fill(email)
        dialog.get_by_label("Password", exact=False).fill(password)
        dialog.get_by_label("Mobile", exact=False).fill(mobile)

    def select_role(self, role_name):
        self.page.get_by_role("button", name="Select Role").click()
        self.page.get_by_role("menuitem", name=role_name).click()
        # Press escape to close the dropdown if it remains open (replaces clicking outside)
        self.page.keyboard.press("Escape")

    def click_submit(self):
        # In step 2, there are two submit buttons in the DOM. We need to click the last one.
        self.page.get_by_role("button", name="Submit").last.click()

    def is_notification_visible(self):
        try:
            self.page.get_by_role("region", name="Notifications-top-right").wait_for(state="visible", timeout=5000)
            return True
        except Exception:
            return False

    def search_user(self, keyword):
        # Fallback to a generic placeholder selector based on existing POM patterns
        search_input = self.page.locator("input[placeholder*='Search']").first
        search_input.fill(keyword)
        self.page.wait_for_timeout(1000)

    def get_row_index(self, row_name, max_pages=50):
        self.page.locator("tbody tr").first.wait_for(timeout=10000)
        for _ in range(max_pages):
            rows = self.page.locator("tbody tr").all()
            for i, row in enumerate(rows):
                if row_name.lower() in row.inner_text().lower():
                    return i + 1
            next_btn = self.page.get_by_role("button", name="Next")
            if next_btn.count() == 0 or not next_btn.first.is_enabled():
                raise ValueError(f"Row containing '{row_name}' not found")
            next_btn.first.click()
            self.page.locator("tbody tr").first.wait_for()
        raise ValueError(
            f"Row containing '{row_name}' not found after paginating through {max_pages} pages"
        )

    def is_user_row_visible(self, user_identifier):
        try:
            self.get_row_index(user_identifier)
            return True
        except ValueError:
            return False

    def is_submit_button_disabled(self):
        return self.page.get_by_role("button", name="Submit").is_disabled()

    def get_validation_message(self, field_name):
        # Pending Locator Confirmation
        raise NotImplementedError("Pending Locator Confirmation")
