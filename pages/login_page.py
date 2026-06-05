import os


class LoginPage:

    def __init__(self, page):
        self.page = page
        self.url = os.getenv("BASE_URL")

    def load(self):
        self.page.set_default_navigation_timeout(60000)
        self.page.goto(self.url)

    def is_illustration_visible(self):
        return self.page.get_by_role("img", name="Login Illustration").is_visible()

    def enter_email(self, email):
        self.page.get_by_role("textbox", name="Email").fill(email)

    def enter_password(self, password):
        self.page.get_by_role("textbox", name="Password").fill(password)

    def click_login(self):
        self.page.get_by_role("button", name="Login").click()

    def click_show_password(self):
        self.page.get_by_role("button", name="Show password").click()

    def is_hide_password_visible(self):
        return self.page.get_by_role("button", name="Hide password").is_visible()

    def wait_for_dashboard(self):
        self.page.wait_for_url("**/dashboard**", timeout=15000)

    def login(self, email, password):
        self.enter_email(email)
        self.enter_password(password)
        self.click_login()
