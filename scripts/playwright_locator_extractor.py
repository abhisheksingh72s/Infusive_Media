import os
import json
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

# Load environment variables from the project's .env file
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

def get_env(key, fallback=None):
    return os.getenv(key) or fallback

# Resolve credentials – map existing keys to the requested logical names
PRE_USERNAME = get_env("USER_11_EMAIL")
PRE_PASSWORD = get_env("USER_11_PASSWORD")
BDM_USERNAME = get_env("USER_12_EMAIL")
BDM_PASSWORD = get_env("USER_12_PASSWORD")

# Base URL – try to read from .env, otherwise fallback to a hard‑coded value
BASE_URL = get_env("BASE_URL", "https://infusive-front.jobvritta.com")

# Container for the extracted locators
LOCATORS = {}

def record(name: str, locator: str, page_name: str, locator_type: str):
    """Store a locator definition.
    Args:
        name: Logical element name (as requested).
        locator: Playwright locator expression (e.g. page.get_by_role(...)).
        page_name: Human readable page where the element lives.
        locator_type: The Playwright helper used (getByRole, getByLabel, etc.).
    """
    LOCATORS[name] = {
        "playwright_locator": locator,
        "locator_type": locator_type,
        "page": page_name,
    }

def save_locators(file_path: Path):
    """Write the LOCATORS dict to a JSON file with pretty formatting."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(LOCATORS, f, indent=2)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # ------------------- Pre‑Sales Flow -------------------
        page.goto(f"{BASE_URL}/login")
        # record login fields
        record("username", "page.get_by_role('textbox', name='Email')", "Login", "getByRole")
        record("password", "page.get_by_role('textbox', name='Password')", "Login", "getByRole")
        record("login_button", "page.get_by_role('button', name='Login')", "Login", "getByRole")
        # perform login
        page.get_by_role('textbox', name='Email').fill(PRE_USERNAME)
        page.get_by_role('textbox', name='Password').fill(PRE_PASSWORD)
        page.get_by_role('button', name='Login').click()
        page.wait_for_url("**/dashboard")

        # Company module link
        record("company_module", "page.get_by_role('link', name='Company')", "Dashboard", "getByRole")
        page.get_by_role('link', name='Company').click()
        page.wait_for_selector("button:has-text('Add New Company')")

        # Add New Company button
        record("add_new_company_button", "page.get_by_role('button', name='Add New Company')", "Company", "getByRole")
        page.get_by_role('button', name='Add New Company').click()

        # Menu options – prefer role/menuitem if available
        record("add_new_company_option", "page.get_by_role('menuitem', name='Add New Company')", "CompanyMenu", "getByRole")
        record("add_new_company_and_poc_option", "page.get_by_role('menuitem', name='Add New Company & POC')", "CompanyMenu", "getByRole")
        record("add_quick_lead_option", "page.get_by_role('menuitem', name='Add Quick Lead')", "CompanyMenu", "getByRole")
        record("extract_content_option", "page.get_by_role('menuitem', name='Extract Content')", "CompanyMenu", "getByRole")
        # Click Quick Lead
        page.get_by_role('menuitem', name='Add Quick Lead').click()
        page.wait_for_selector("input[placeholder='Name']")

        # Quick Lead form fields
        record("company_name", "page.get_by_placeholder('Name')", "QuickLeadForm", "getByPlaceholder")
        record("contact_person", "page.get_by_placeholder('Contact Person')", "QuickLeadForm", "getByPlaceholder")
        record("mobile", "page.get_by_placeholder('Mobile')", "QuickLeadForm", "getByPlaceholder")
        record("email", "page.get_by_placeholder('Email')", "QuickLeadForm", "getByPlaceholder")
        record("submit_button", "page.get_by_role('button', name='Save')", "QuickLeadForm", "getByRole")
        # Fill minimal required fields for demo
        page.get_by_placeholder('Name').fill('DemoCo')
        page.get_by_role('button', name='Save').click()
        page.wait_for_timeout(2000)

        # Logout Pre‑Sales
        record("profile_menu", "page.get_by_role('button', name='profile menu')", "Dashboard", "getByRole")
        record("logout_button", "page.get_by_role('menuitem', name='Logout')", "ProfileMenu", "getByRole")
        page.get_by_role('button', name='profile menu').click()
        page.get_by_role('menuitem', name='Logout').click()
        page.wait_for_url("**/login")

        # ------------------- BDM Flow -------------------
        page.get_by_role('textbox', name='Email').fill(BDM_USERNAME)
        page.get_by_role('textbox', name='Password').fill(BDM_PASSWORD)
        page.get_by_role('button', name='Login').click()
        page.wait_for_url("**/dashboard")

        # Lead module
        record("lead_module", "page.get_by_role('link', name='Leads')", "Dashboard", "getByRole")
        page.get_by_role('link', name='Leads').click()

        # My Leads submodule
        record("my_leads_submodule", "page.get_by_role('link', name='My Leads')", "LeadPage", "getByRole")
        page.get_by_role('link', name='My Leads').click()
        page.wait_for_selector("input[placeholder='Search']")
        record("search_box", "page.get_by_placeholder('Search')", "MyLeads", "getByPlaceholder")
        page.get_by_placeholder('Search').fill('DemoCo')
        page.wait_for_timeout(1000)

        # Lead row – use a data attribute if present, otherwise first row
        record("lead_row", "page.locator('tr[data-lead-id]')", "MyLeads", "css")
        page.locator('tr[data-lead-id]').first.click()

        # Assigned To column (role = cell, name = Assigned To)
        record("assigned_to_column", "page.get_by_role('cell', name='Assigned To')", "LeadDetail", "getByRole")
        # Company link on lead detail
        record("company_link", "page.get_by_role('link', name='Company')", "LeadDetail", "getByRole")
        # Action button (usually a kebab menu)
        record("action_button", "page.get_by_role('button', name='Action')", "LeadDetail", "getByRole")
        page.get_by_role('button', name='Action').click()
        # Accept / Reject options in the Action menu
        record("accept_button", "page.get_by_role('menuitem', name='Accept')", "ActionMenu", "getByRole")
        record("reject_button", "page.get_by_role('menuitem', name='Reject')", "ActionMenu", "getByRole")
        page.get_by_role('menuitem', name='Accept').click()

        # Save extracted locators
        locators_path = Path(__file__).resolve().parents[1] / "locators_playwright.json"
        save_locators(locators_path)
        print(f"Playwright locators written to {locators_path}")

        browser.close()

if __name__ == "__main__":
    run()
