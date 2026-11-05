import logging
import os

logger = logging.getLogger(__name__)


class TaskNotificationSettingsPage:
    """
    Page Object Model for Admin Controller -> Task Notification Settings
    URL: /tasknotificationSettings

    Table Structure:
      Columns: EVENT | ENABLED | ASSIGNED TO | CREATED BY | REVIEWER | CLIENT | MINUTES BEFORE
      Rows:
        - Task Created
        - Time (Worklog) Added
        - Timesheet Approved
        - Task Reminder
        - Task Updated

    Behavior:
      - Checkbox Checked (True)  => Email notification is delivered to that role for the event.
      - Checkbox Unchecked (False) => Email notification is skipped for that role.
    """

    ROLE_COLUMNS = {
        "ENABLED": 1,
        "ASSIGNED TO": 2,
        "CREATED BY": 3,
        "REVIEWER": 4,
        "CLIENT": 5,
    }

    def __init__(self, page):
        self.page = page
        base = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")
        self.base_url = base.replace("/login", "").rstrip("/")
        self.target_url = f"{self.base_url}/tasknotificationSettings"

    def go_to_task_notification_settings(self):
        """Navigate to Task Notification Settings."""
        logger.info("Navigating to %s...", self.target_url)
        self.page.goto(self.target_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)
        self.wait_for_table()

    def wait_for_table(self, timeout=30000):
        """Wait for the notification settings table body to render."""
        self.page.locator("tbody tr").first.wait_for(state="visible", timeout=timeout)

    def get_table_headers(self):
        """Return list of column headers from the table."""
        return [
            th.inner_text().strip().replace("\n", " ")
            for th in self.page.locator("thead th, table th").all()
            if th.inner_text().strip()
        ]

    def get_row_locator(self, event_name):
        """Locate table row by event name (e.g. 'Task Created')."""
        return self.page.locator(f"tbody tr:has-text('{event_name}')").first

    def get_checkbox(self, event_name, role_column_name):
        """
        Locate the checkbox for a specific event and role column.
        role_column_name can be: 'ENABLED', 'ASSIGNED TO', 'CREATED BY', 'REVIEWER', 'CLIENT'
        """
        row = self.get_row_locator(event_name)
        col_name = role_column_name.strip().upper()

        if col_name in self.ROLE_COLUMNS:
            col_index = self.ROLE_COLUMNS[col_name]
            td = row.locator("td").nth(col_index)
            return td.locator("input[type='checkbox'], [role='checkbox'], input").first

        # Fallback to header index matching
        headers = [h.upper() for h in self.get_table_headers()]
        if col_name in headers:
            col_index = headers.index(col_name)
            td = row.locator("td").nth(col_index)
            return td.locator("input[type='checkbox'], [role='checkbox'], input").first

        raise ValueError(f"Column '{role_column_name}' not found. Available: {list(self.ROLE_COLUMNS.keys())}")

    def is_role_notified(self, event_name, role_column_name):
        """Return True if checkbox is checked for the event & role, else False."""
        cb = self.get_checkbox(event_name, role_column_name)
        try:
            return cb.is_checked()
        except Exception:
            return cb.get_attribute("aria-checked") == "true" or cb.get_attribute("data-checked") is not None

    def set_role_notification(self, event_name, role_column_name, enable=True):
        """
        Toggle checkbox for an event & role.
        enable=True  => checked (mail sent)
        enable=False => unchecked (skip mail)
        """
        current_state = self.is_role_notified(event_name, role_column_name)
        logger.info(
            "Event '%s' | Role '%s': current=%s, target=%s",
            event_name, role_column_name, current_state, enable
        )

        if current_state != enable:
            cb = self.get_checkbox(event_name, role_column_name)
            try:
                cb.click()
            except Exception:
                cb.click(force=True)
            self.page.wait_for_timeout(500)

        new_state = self.is_role_notified(event_name, role_column_name)
        logger.info("Event '%s' | Role '%s': new_state=%s", event_name, role_column_name, new_state)
        return new_state

    def get_minutes_before(self, event_name="Task Reminder"):
        """Read 'MINUTES BEFORE' input value."""
        row = self.get_row_locator(event_name)
        text_input = row.locator("td").nth(6).locator("input")
        if text_input.count() > 0:
            return text_input.first.input_value()
        return row.locator("td").nth(6).inner_text().strip()

    def set_minutes_before(self, minutes: int, event_name="Task Reminder"):
        """Fill 'MINUTES BEFORE' input."""
        row = self.get_row_locator(event_name)
        text_input = row.locator("td").nth(6).locator("input").first
        text_input.click()
        text_input.fill(str(minutes))

    def get_full_matrix(self):
        """Retrieve full live status matrix of all events and checkboxes."""
        headers = self.get_table_headers()
        matrix = []
        for row in self.page.locator("tbody tr").all():
            tds = row.locator("td").all()
            event_name = tds[0].inner_text().strip()
            row_dict = {"event": event_name}
            for col_idx in range(1, len(tds)):
                col_name = headers[col_idx] if col_idx < len(headers) else f"col_{col_idx}"
                td = tds[col_idx]
                cb = td.locator("input[type='checkbox'], [role='checkbox']")
                if cb.count() > 0:
                    row_dict[col_name] = cb.first.is_checked()
                else:
                    text_input = td.locator("input")
                    if text_input.count() > 0:
                        row_dict[col_name] = text_input.first.input_value()
                    else:
                        row_dict[col_name] = td.inner_text().strip()
            matrix.append(row_dict)
        return matrix

    def click_save(self):
        """Click Save/Update button if present."""
        for sel in [
            self.page.get_by_role("button", name="Save"),
            self.page.get_by_role("button", name="Update"),
            self.page.get_by_role("button", name="Save Changes"),
            self.page.locator("//button[contains(.,'Save') or contains(.,'Update')]")
        ]:
            if sel.first.is_visible(timeout=1500):
                sel.first.click()
                self.page.wait_for_timeout(1000)
                return True
        return False

    def capture_toast(self, timeout=5000):
        """Capture toast/status alert message."""
        selectors = ["div[role='status']", "div[role='alert']", ".toast", "[class*='toast']"]
        for s in selectors:
            loc = self.page.locator(s)
            if loc.first.is_visible(timeout=timeout):
                return loc.first.inner_text().strip()
        return ""
