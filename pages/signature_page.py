import os
import json
from playwright.sync_api import Page, expect

class SignaturePage:
    """
    Page Object Model for the Signature module.
    Refactored to generate unique, actionable Playwright locators for production use.
    """

    def __init__(self, page: Page):
        self.page = page
        self.sidebar_signature_link = self.page.locator("a[href='/signature']").first
        self.save_button = self.page.locator("//button[normalize-space()='Save Signature']").or_(
            self.page.locator("//button[normalize-space()='Save']")
        ).first
        self.cancel_button = self.page.locator("//button[normalize-space()='Cancel']").first

    def go_to_signature(self):
        """Navigate to Signature module from sidebar or direct URL."""
        if self.sidebar_signature_link.is_visible():
            self.sidebar_signature_link.click()
        else:
            base = self.page.url.split("/")[0] + "//" + self.page.url.split("/")[2]
            self.page.goto(f"{base}/signature", wait_until="domcontentloaded")
        self.wait_for_page_load()

    def wait_for_page_load(self):
        """Wait for the Signature page and editor elements to be visible."""
        self.page.wait_for_selector("div.jodit-wysiwyg, button", timeout=15000)
        self.page.wait_for_timeout(1000)

    @property
    def short_signature_editor(self):
        return self.page.locator(
            "//label[contains(normalize-space(),'Short Signature')]/following::div[contains(@class,'jodit-wysiwyg') and @contenteditable='true'][1]"
        ).first

    @property
    def full_signature_editor(self):
        return self.page.locator(
            "//label[contains(normalize-space(),'Full Signature')]/following::div[contains(@class,'jodit-wysiwyg') and @contenteditable='true'][1]"
        ).first

    def fill_short_signature(self, text: str):
        editor = self.short_signature_editor
        editor.click()
        editor.fill(text)

    def fill_full_signature(self, text: str):
        editor = self.full_signature_editor
        editor.click()
        editor.fill(text)

    def click_save(self):
        self.save_button.click()
        self.page.wait_for_timeout(2000)

    def click_cancel(self):
        if self.cancel_button.is_visible():
            self.cancel_button.click()

    def get_toast_message(self) -> str:
        toast = self.page.locator("//*[@role='status']").or_(
            self.page.locator("div.chakra-toast__inner")
        ).first
        if toast.is_visible():
            return toast.inner_text().strip()
        return ""

    def build_element_json(self, name: str, tag: str, el, default_xpath: str, default_css: str, default_pw: str) -> dict:
        """Construct structured element JSON with unique locators."""
        e_id = ""
        e_name = ""
        is_vis = False
        is_en = False

        if el:
            try:
                e_id = el.get_attribute("id") or ""
            except Exception:
                pass
            try:
                e_name = el.get_attribute("name") or ""
            except Exception:
                pass
            try:
                is_vis = el.is_visible()
            except Exception:
                is_vis = False
            try:
                is_en = el.is_enabled()
            except Exception:
                is_en = False

        xpath_loc = default_xpath
        css_loc = default_css
        pw_loc = default_pw

        if e_id:
            xpath_loc = f"//*[@id='{e_id}']"
            css_loc = f"#{e_id}"
            pw_loc = f"page.locator('#{e_id}')"
        elif e_name:
            xpath_loc = f"//{tag}[@name='{e_name}']"
            css_loc = f"{tag}[name='{e_name}']"
            pw_loc = f"page.locator(\"{tag}[name='{e_name}']\")"

        return {
            "element_name": name,
            "tag": tag,
            "locator": {
                "id": e_id,
                "name": e_name,
                "css": css_loc,
                "xpath": xpath_loc,
                "playwright": pw_loc
            },
            "is_visible": is_vis,
            "is_enabled": is_en
        }

    def extract_dom_elements(self) -> list:
        """
        Extract only actionable UI elements with unique, non-duplicate locators matching required schema:
        1. Short Signature Editor
        2. Full Signature Editor
        3. Save Signature Button
        4. Cancel Button (if present)
        5. Success Toast (single innermost/status container)
        6. Validation Messages (if present)
        """
        result = []

        # 1. Short Signature Editor
        short_el = self.short_signature_editor
        short_xpath = "//label[normalize-space()='Short Signature']/following::div[contains(@class,'jodit-wysiwyg') and @contenteditable='true'][1]"
        short_css = "label:has-text('Short Signature') + div .jodit-wysiwyg[contenteditable='true']"
        short_pw = f"page.locator(\"{short_xpath}\")"
        result.append(self.build_element_json("Short Signature Editor", "div", short_el, short_xpath, short_css, short_pw))

        # 2. Full Signature Editor
        full_el = self.full_signature_editor
        full_xpath = "//label[normalize-space()='Full Signature']/following::div[contains(@class,'jodit-wysiwyg') and @contenteditable='true'][1]"
        full_css = "label:has-text('Full Signature') + div .jodit-wysiwyg[contenteditable='true']"
        full_pw = f"page.locator(\"{full_xpath}\")"
        result.append(self.build_element_json("Full Signature Editor", "div", full_el, full_xpath, full_css, full_pw))

        # 3. Save Signature Button
        save_btn_xpath = "//button[normalize-space()='Save Signature']"
        save_btn_css = "button.btn_theme"
        save_btn_pw = 'page.get_by_role("button", name="Save Signature")'
        result.append(self.build_element_json("Save Signature Button", "button", self.save_button, save_btn_xpath, save_btn_css, save_btn_pw))

        # 4. Cancel Button (if present)
        if self.cancel_button.count() > 0 and self.cancel_button.is_visible():
            cancel_xpath = "//button[normalize-space()='Cancel']"
            cancel_css = "button.css-1u2w9fd"
            cancel_pw = 'page.get_by_role("button", name="Cancel")'
            result.append(self.build_element_json("Cancel Button", "button", self.cancel_button, cancel_xpath, cancel_css, cancel_pw))

        # 5. Success Toast (single innermost toast container)
        toast_el = self.page.locator("//*[@role='status']").or_(
            self.page.locator(".chakra-toast__inner")
        ).first
        if toast_el.count() > 0 and toast_el.is_visible():
            toast_xpath = "//*[@role='status']"
            toast_css = "[role='status']"
            toast_pw = 'page.locator("//*[@role=\'status\']")'
            result.append(self.build_element_json("Success Toast", "div", toast_el, toast_xpath, toast_css, toast_pw))

        # 6. Validation Messages (if present)
        val_msg = self.page.locator(".chakra-form__error-message").first
        if val_msg.count() > 0 and val_msg.is_visible():
            val_xpath = "//div[contains(@class,'chakra-form__error-message')]"
            val_css = ".chakra-form__error-message"
            val_pw = 'page.locator(".chakra-form__error-message")'
            result.append(self.build_element_json("Validation Message", "div", val_msg, val_xpath, val_css, val_pw))

        return result
