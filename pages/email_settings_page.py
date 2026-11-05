import logging
import os

logger = logging.getLogger(__name__)


class EmailSettingsPage:
    """
    Page Object Model for Admin Controller -> Email Settings
    URL: /email-settings

    Controls global redirection of all transactional & notification emails:
      - To*: Default recipient override (e.g. qa.tekinspirations@gmail.com)
      - CC*: Carbon copy recipient (e.g. qa.tekinspirations@gmail.com)
      - BCC*: Blind carbon copy recipient (e.g. qa.tekinspirations@gmail.com)
      - Update: Saves the settings
    """

    def __init__(self, page):
        self.page = page
        base = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")
        self.base_url = base.replace("/login", "").rstrip("/")
        self.target_url = f"{self.base_url}/email-settings"

    def go_to_email_settings(self):
        """Navigate to /email-settings."""
        logger.info("Navigating to %s...", self.target_url)
        self.page.goto(self.target_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)
        self.page.locator("input[name='to']").wait_for(state="visible", timeout=30000)

    def get_email_settings(self) -> dict:
        """Fetch current To, CC, and BCC configured values."""
        to_val = self.page.locator("input[name='to']").input_value()
        cc_val = self.page.locator("input[name='cc']").input_value()
        bcc_val = self.page.locator("input[name='bcc']").input_value()
        settings = {"to": to_val, "cc": cc_val, "bcc": bcc_val}
        logger.info("Current Email Settings: %s", settings)
        return settings

    def update_email_settings(self, to_email: str = None, cc_email: str = None, bcc_email: str = None):
        """Update To, CC, and BCC fields and submit."""
        if to_email is not None:
            inp = self.page.locator("input[name='to']")
            inp.fill("")
            inp.fill(to_email)
        if cc_email is not None:
            inp = self.page.locator("input[name='cc']")
            inp.fill("")
            inp.fill(cc_email)
        if bcc_email is not None:
            inp = self.page.locator("input[name='bcc']")
            inp.fill("")
            inp.fill(bcc_email)

        self.page.get_by_role("button", name="Update").click()
        self.page.wait_for_timeout(1000)

    def capture_toast(self, timeout=5000):
        """Capture toast/status alert message."""
        selectors = ["div[role='status']", "div[role='alert']", ".toast", "[class*='toast']"]
        for s in selectors:
            loc = self.page.locator(s)
            if loc.first.is_visible(timeout=timeout):
                return loc.first.inner_text().strip()
        return ""
