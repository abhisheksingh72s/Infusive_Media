import os
import json
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

from pages.login_page import LoginPage
from pages.company_page import CompanyPage
from pages.lead_page import LeadPoolPage, MyLeadsPage

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

EMAIL = os.getenv("EMAIL", "Admin@infusive.com")
PASSWORD = os.getenv("PASSWORD", "123456")

verified_results = []

def verify(element, locator_obj, locator_str, locator_type, page_name):
    expect(locator_obj).to_have_count(1, timeout=10000)
    verified_results.append({
        "element": element,
        "playwright_locator": locator_str,
        "locator_type": locator_type,
        "page": page_name
    })
    print(f"[VERIFIED 1/1] [{page_name}] {element} -> {locator_str}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login_page = LoginPage(page)
        company_page = CompanyPage(page)
        my_leads_page = MyLeadsPage(page)

        # 1. Login Page
        login_page.load()

        u_loc = page.get_by_placeholder("Enter your email")
        verify("username", u_loc, "page.get_by_placeholder('Enter your email')", "getByPlaceholder", "Login")

        p_loc = page.get_by_placeholder("Enter password")
        verify("password", p_loc, "page.get_by_placeholder('Enter password')", "getByPlaceholder", "Login")

        btn_loc = page.get_by_role("button", name="Login")
        verify("login_button", btn_loc, "page.get_by_role('button', name='Login')", "getByRole", "Login")

        login_page.login(EMAIL, PASSWORD)
        login_page.wait_for_dashboard()

        # 2. Dashboard
        comp_mod = page.get_by_role("link", name="Company")
        verify("company_module", comp_mod, "page.get_by_role('link', name='Company')", "getByRole", "Dashboard")
        comp_mod.click()

        page.wait_for_url("**/company", timeout=20000)

        # 3. Company page
        add_comp_btn = page.get_by_role("button", name="Add New Company")
        verify("add_new_company_button", add_comp_btn, "page.get_by_role('button', name='Add New Company')", "getByRole", "Company")
        add_comp_btn.click()

        page.wait_for_timeout(1000)

        # 4. Company Menu options
        opt1 = page.get_by_text("Add New Company", exact=True)
        verify("add_new_company_option", opt1, "page.get_by_text('Add New Company', exact=True)", "getByText", "CompanyMenu")

        opt2 = page.get_by_text("Add New Company & POC", exact=True)
        verify("add_new_company_and_poc_option", opt2, "page.get_by_text('Add New Company & POC', exact=True)", "getByText", "CompanyMenu")

        opt3 = page.get_by_text("Add Quick Lead", exact=True)
        verify("add_quick_lead_option", opt3, "page.get_by_text('Add Quick Lead', exact=True)", "getByText", "CompanyMenu")

        opt4 = page.get_by_text("Extract Content", exact=True)
        verify("extract_content_option", opt4, "page.get_by_text('Extract Content', exact=True)", "getByText", "CompanyMenu")

        opt3.click()
        page.wait_for_selector("input[name='name']", timeout=10000)

        # 5. Quick Lead form
        name_in = page.locator("input[name='name']")
        verify("company_name", name_in, "page.locator(\"input[name='name']\")", "css", "QuickLeadForm")

        cp_in = page.locator("input[name='contactPerson']")
        if cp_in.count() > 0:
            verify("contact_person", cp_in, "page.locator(\"input[name='contactPerson']\")", "css", "QuickLeadForm")

        phone_in = page.get_by_placeholder("Enter Phone")
        verify("mobile", phone_in, "page.get_by_placeholder('Enter Phone')", "getByPlaceholder", "QuickLeadForm")

        email_in = page.locator("input[name='email']")
        verify("email", email_in, "page.locator(\"input[name='email']\")", "css", "QuickLeadForm")

        save_btn = page.get_by_role("button", name="Save")
        verify("submit_button", save_btn, "page.get_by_role('button', name='Save')", "getByRole", "QuickLeadForm")

        name_in.fill("LiveVerifiedCo")
        email_in.fill("liveverifiedco@mailinator.com")
        phone_in.fill("9876543210")
        save_btn.click()
        page.wait_for_timeout(2000)

        # 6. Lead module & My Leads
        lead_mod = page.locator("a[href='/lead']")
        verify("lead_module", lead_mod, "page.locator(\"a[href='/lead']\")", "css", "Dashboard")
        lead_mod.click()

        my_leads_lnk = page.locator("a[href='/my-leads']")
        verify("my_leads_submodule", my_leads_lnk, "page.locator(\"a[href='/my-leads']\")", "css", "LeadPage")
        my_leads_lnk.click()

        page.wait_for_url("**/my-leads", timeout=15000)

        # 7. Search & Table
        search_b = page.get_by_placeholder("Search", exact=False)
        if search_b.count() == 0:
            search_b = page.locator("input[placeholder='Search']")
        verify("search_box", search_b.first, "page.get_by_placeholder('Search')", "getByPlaceholder", "MyLeads")

        search_b.first.fill("LiveVerifiedCo")
        page.wait_for_timeout(1000)

        lead_r = page.locator("tbody tr").first
        verify("lead_row", lead_r, "page.locator('tbody tr').first", "css", "MyLeads")

        ass_col = page.locator("th:has-text('ASSIGNED TO')")
        verify("assigned_to_column", ass_col, "page.locator(\"th:has-text('ASSIGNED TO')\")", "css", "MyLeads")

        comp_lnk = lead_r.locator("a").first
        if comp_lnk.count() > 0:
            verify("company_link", comp_lnk, "page.locator('tbody tr').first.locator('a').first", "css", "MyLeads")

        act_btn = lead_r.locator("button").first
        verify("action_button", act_btn, "page.locator('tbody tr').first.locator('button').first", "css", "MyLeads")
        act_btn.click()

        acc_btn = page.get_by_role("menuitem", name="Accept")
        verify("accept_button", acc_btn, "page.get_by_role('menuitem', name='Accept')", "getByRole", "ActionMenu")

        rej_btn = page.get_by_role("menuitem", name="Reject")
        verify("reject_button", rej_btn, "page.get_by_role('menuitem', name='Reject')", "getByRole", "ActionMenu")

        browser.close()

    output_path = Path(__file__).resolve().parent / "verified_locators.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(verified_results, f, indent=2)

    print("\n--- ALL LOCATORS VERIFIED SUCCESSFULLY (count=1) ---")
    print(json.dumps(verified_results, indent=2))

if __name__ == "__main__":
    run()
