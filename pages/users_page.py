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

    def submit_empty_user_id(self):
        dialog = self.page.get_by_role("dialog", name="Add New User")
        dialog.get_by_label("User Id", exact=False).fill("")
        dialog.get_by_role("button", name="Submit").click()

    def is_submit_button_disabled(self):
        return self.page.get_by_role("button", name="Submit").is_disabled()

    def get_validation_message(self, field_name):
        raise NotImplementedError("Pending Locator Confirmation")

    def get_user_email_by_name(self, user_name: str) -> str:
        """
        Search for user by Name, locate matching row, and extract Email ID.
        Raises ValueError if user is not found or ambiguous.
        """
        self.page.locator("table, tbody tr").first.wait_for(state="visible", timeout=15000)
        self.search_user(user_name)
        self.page.wait_for_timeout(1500)

        rows = self.page.locator("tbody tr").all()
        matching = []

        for row in rows:
            cells = [c.inner_text().strip() for c in row.locator("td").all()]
            if len(cells) >= 3:
                full_name = cells[1]
                email = cells[2]
                if user_name.lower() == full_name.lower() or user_name.lower() in full_name.lower():
                    matching.append((full_name, email))

        if len(matching) == 0:
            raise ValueError(f"User '{user_name}' not found in Users table.")

        exact = [email for name, email in matching if name.lower() == user_name.lower()]
        if len(exact) == 1:
            return exact[0]

        if len(matching) == 1:
            return matching[0][1]

        raise ValueError(f"Ambiguous user search for '{user_name}': found {len(matching)} matches: {matching}")

    def get_all_users(self) -> list:
        """
        Iterate through all rows in the Users table (handling pagination if present).
        Extracts [{'name': full_name, 'email': email, 'role': role}, ...] for every user.
        Raises ValueError if Users table is empty.
        """
        table = self.page.locator("table").first
        table.wait_for(state="visible", timeout=15000)
        self.page.locator("tbody tr").first.wait_for(state="visible", timeout=15000)

        all_users = []
        max_pages = 50

        for _ in range(max_pages):
            rows = self.page.locator("tbody tr").all()
            for row in rows:
                cells = [c.inner_text().strip() for c in row.locator("td").all()]
                if len(cells) >= 6:
                    name = cells[1]
                    email = cells[2]
                    role = cells[5]
                    if name and email:
                        all_users.append({
                            "name": name,
                            "email": email,
                            "role": role
                        })

            next_btn = self.page.get_by_role("button", name="Next").or_(
                self.page.locator("button:has-text('Next')")
            ).first
            if next_btn.count() == 0 or not next_btn.is_enabled():
                break

            next_btn.click()
            self.page.wait_for_timeout(1000)
            self.page.locator("tbody tr").first.wait_for(state="visible")

        if not all_users:
            raise ValueError("Users table is empty; no user records found.")

        unique_users = []
        seen_emails = set()
        for u in all_users:
            if u["email"] not in seen_emails:
                seen_emails.add(u["email"])
                unique_users.append(u)

        return unique_users
