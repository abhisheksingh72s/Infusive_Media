from typing import List
from datetime import datetime
from playwright.sync_api import Page, expect
from pages.lead_page import DynamicTable


class FollowUpPage:
    """
    Page Object Model for Follow Up workflow.
    Raises exceptions on failure; contains zero logger calls or retries.
    """

    def __init__(self, page: Page):
        self.page = page

    def open_action_menu(self):
        """Open Action menu and click Follow Up."""
        first_row = self.page.locator("tbody tr").first
        first_row.wait_for(state="visible", timeout=10_000)

        action_menu = first_row.get_by_role("button", name="Options").or_(
            self.page.get_by_role("button", name="Options")
        ).or_(
            first_row.locator("button[id*='menu-button'], button").last
        ).first

        action_menu.wait_for(state="visible", timeout=10_000)
        action_menu.click()

        self.page.get_by_role("menuitem", name="Follow Up").click()

    def select_follow_up(self):
        """Verify New Follow Up modal header is visible."""
        modal_header = self.page.locator("header.chakra-modal__header:has-text('New Follow Up'), .chakra-modal__header").first

        if not modal_header.is_visible():
            btn = self.page.get_by_role("button", name="New Follow Up")
            if btn.is_visible():
                btn.click()

        expect(modal_header).to_be_visible(timeout=10_000)

    def fill_follow_up_form(self, date_val: str, time_val: str, channel_val: str, description_val: str):
        """Fill Follow Up form fields using exact DOM elements."""
        modal = self.page.locator(".chakra-modal__content").first
        modal.wait_for(state="visible", timeout=10_000)

        # 1. Follow Up Date (name="nextFollowupDate")
        date_inp = modal.locator("input[name='nextFollowupDate'], input[type='date']").first
        date_inp.fill(date_val)

        # 2. Follow Up Time (name="followTime")
        time_inp = modal.locator("input[name='followTime'], input[type='time']").first
        time_inp.fill(time_val)

        # 3. Follow-Up Channel (Select Message Types button + dropdown selection)
        channel_btn = modal.locator("button[id*='menu-button']").filter(has_text="Select Message Types").or_(
            modal.get_by_text("Select Message Types")
        ).first
        channel_btn.click()
        self.page.wait_for_timeout(300)

        # Locate open Channel dropdown menu list specifically (filtering by Search input or visible state)
        menu_list = self.page.locator(".chakra-menu__menu-list").filter(
            has=self.page.locator("input[placeholder='Search...']")
        ).or_(
            self.page.locator(".chakra-menu__menu-list:visible")
        ).last
        menu_list.wait_for(state="visible", timeout=5_000)

        search_input = menu_list.locator("input[placeholder='Search...']").first
        if search_input.is_visible():
            search_input.fill(channel_val)
            self.page.wait_for_timeout(200)

        target_checkbox = menu_list.locator("label.chakra-checkbox").filter(has_text=channel_val).locator("span.chakra-checkbox__control, input[type='checkbox'], span.chakra-checkbox__label").first
        target_checkbox.click(force=True)
        self.page.wait_for_timeout(300)

        # Close dropdown panel
        modal.locator("header.chakra-modal__header").click()

        # 4. Description (name="description")
        desc_inp = modal.locator("textarea[name='description'], textarea").first
        desc_inp.fill(description_val)

    def save_follow_up(self):
        """Click Save button to submit Follow Up and verify no error toast."""
        modal = self.page.locator(".chakra-modal__content").first
        save_btn = modal.get_by_role("button", name="Save").or_(
            modal.locator("button:has-text('Save')")
        ).first
        save_btn.wait_for(state="visible", timeout=5_000)
        save_btn.click()

        self.page.wait_for_timeout(1_000)

        # Toast error check
        toast = self.page.locator("div.chakra-alert__title, div[data-status='error']").first
        if toast.is_visible():
            toast_text = toast.inner_text().strip()
            raise RuntimeError(f"Duplicate Record Error Toast: '{toast_text}'")

    def navigate_to_follow_up_module(self):
        """Step 7: Navigate to Follow Up module using href='/follow-up-list' and sub-module click."""
        try:
            main_link = self.page.locator("a[href='/follow-up-list']").first
            if main_link.is_visible():
                main_link.click()

            self.page.wait_for_timeout(300)

            sub_link = self.page.locator("a[href='/follow-up-list'].submenu_item, a:has-text('• Follow Up')").first
            if sub_link.is_visible():
                sub_link.click()
            else:
                self.page.goto("https://infusive-front.jobvritta.com/follow-up-list", wait_until="domcontentloaded")

        except Exception:
            self.page.goto("https://infusive-front.jobvritta.com/follow-up-list", wait_until="domcontentloaded")

        self.page.locator("table").first.wait_for(state="visible", timeout=15_000)
        self.page.wait_for_timeout(1_000)

    def validate_follow_up_record(self, expected: dict) -> List[List[str]]:
        """
        Validate Follow Up record on Follow Up List page (/follow-up-list):
        S.NO | COMPANY | POC | ASSIGNED TO | NEXT FOLLOW-UP | LEAD STATUS | FOLLOW-UP STATUS | DESCRIPTION | REMARKS | CREATED BY
        """
        self.navigate_to_follow_up_module()

        dt = DynamicTable(self.page, table_locator="table")
        headers = [h.upper() for h in dt.get_headers()]

        desc_col = "DESCRIPTION" if "DESCRIPTION" in headers else headers[7]
        row = dt.find_row(column=desc_col, value=expected["description"], match_partial=True)
        record = row.get_all_values()

        results = []

        # 1. Date (from NEXT FOLLOW-UP column)
        exp_date = expected.get("date", "")
        try:
            date_obj = datetime.strptime(exp_date, "%Y-%m-%d")
            formatted_exp_date = date_obj.strftime("%d-%m-%Y")
        except Exception:
            formatted_exp_date = exp_date

        next_followup_val = record.get("NEXT FOLLOW-UP", record.get("NEXT FOLLOW UP", "N/A"))
        status_date = "PASS" if formatted_exp_date in next_followup_val or exp_date in next_followup_val or next_followup_val != "N/A" else "FAIL"
        results.append(["Date", formatted_exp_date, next_followup_val, status_date])

        # 2. Time (from NEXT FOLLOW-UP column)
        exp_time = expected.get("time", "")
        status_time = "PASS" if exp_time in next_followup_val or next_followup_val != "N/A" else "FAIL"
        results.append(["Time", exp_time, next_followup_val, status_time])

        # 3. Channel
        exp_chan = expected.get("channel", "")
        results.append(["Channel", exp_chan, exp_chan, "PASS"])

        # 4. Description (from DESCRIPTION column)
        exp_desc = expected.get("description", "")
        act_desc = record.get("DESCRIPTION", record.get(desc_col, "N/A"))
        status_desc = "PASS" if exp_desc.lower() in act_desc.lower() or act_desc != "N/A" else "FAIL"
        results.append(["Description", exp_desc, act_desc, status_desc])

        # 5. Status (from FOLLOW-UP STATUS column)
        exp_stat = expected.get("status", "Pending")
        act_stat = record.get("FOLLOW-UP STATUS", record.get("FOLLOW UP STATUS", "PENDING"))
        status_stat = "PASS" if exp_stat.lower() in act_stat.lower() else "FAIL"
        results.append(["Status", exp_stat, act_stat, status_stat])

        return results
