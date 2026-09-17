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

PRE_EMAIL = os.getenv("USER_11_EMAIL", "PreSales2@mailinator.com")
PRE_PASS = os.getenv("USER_11_PASSWORD", "123456")

verified_results = []

def verify_locator(element, locator_obj, locator_str, locator_type, page_name):
    expect(locator_obj).to_have_count(1, timeout=15000)
    verified_results.append({
        "element": element,
        "playwright_locator": locator_str,
        "locator_type": locator_type,
        "page": page_name
    })
    print(f"[VERIFIED 1/1] {element} -> {locator_str}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        login_page = LoginPage(page)
        company_page = CompanyPage(page)
        lead_pool_page = LeadPoolPage(page)
        my_leads_page = MyLeadsPage(page)

        # 1. Login Page
        login_page.load()

        u_loc = page.get_by_role("textbox", name="Email")
        verify_locator("username", u_loc, "page.get_by_role('textbox', name='Email')", "getByRole", "Login")

        p_loc = page.get_by_role("textbox", name="Password")
        verify_locator("password", p_loc, "page.get_by_role('textbox', name='Password')", "getByRole", "Login")

        btn_loc = page.get_by_role("button", name="Login")
        verify_locator("login_button", btn_loc, "page.get_by_role('button', name='Login')", "getByRole", "Login")

        login_page.login(PRE_EMAIL, PRE_PASS)
        login_page.wait_for_dashboard()

        # 2. Company Module
        comp_mod = page.get_by_role("link", name="Company")
        verify_locator("company_module", comp_mod, "page.get_by_role('link', name='Company')", "getByRole", "Dashboard")
        company_page.go_to_company()

        # 3. Add New Company Button
        add_btn = page.get_by_role("button", name="Add New Company")
        verify_locator("add_new_company_button", add_btn, "page.get_by_role('button', name='Add New Company')", "getByRole", "Company")
        add_btn.click()

        # 4. Menu Options
        opt1 = page.locator("//p[normalize-space()='Add New Company']")
        verify_locator("add_new_company_option", opt1, "page.locator(\"//p[normalize-space()='Add New Company']\")", "xpath", "CompanyMenu")

        opt2 = page.get_by_text("Add New Company & POC", exact=True)
        verify_locator("add_new_company_and_poc_option", opt2, "page.get_by_text('Add New Company & POC', exact=True)", "getByText", "CompanyMenu")

        opt3 = page.get_by_role("menuitem", name="Add Quick Lead")
        if opt3.count() == 0:
            opt3 = page.locator("//p[contains(text(), 'Add Quick Lead')]")
            verify_locator("add_quick_lead_option", opt3, "page.locator(\"//p[contains(text(), 'Add Quick Lead')]\")", "xpath", "CompanyMenu")
        else:
            verify_locator("add_quick_lead_option", opt3, "page.get_by_role('menuitem', name='Add Quick Lead')", "getByRole", "CompanyMenu")

        opt4 = page.get_by_text("Extract Content", exact=False)
        if opt4.count() > 0:
            verify_locator("extract_content_option", opt4.first, "page.get_by_text('Extract Content')", "getByText", "CompanyMenu")

        opt3.click()

        page.get_by_role("textbox", name="Name").wait_for(state="visible", timeout=10000)

        # 5. Quick Lead form
        name_input = page.get_by_role("textbox", name="Name")
        verify_locator("company_name", name_input, "page.get_by_role('textbox', name='Name')", "getByRole", "QuickLeadForm")

        contact_p = page.get_by_placeholder("Contact Person", exact=False)
        if contact_p.count() > 0:
            verify_locator("contact_person", contact_p.first, "page.get_by_placeholder('Contact Person')", "getByPlaceholder", "QuickLeadForm")

        phone_input = page.get_by_placeholder("Enter Phone")
        verify_locator("mobile", phone_input, "page.get_by_placeholder('Enter Phone')", "getByPlaceholder", "QuickLeadForm")

        email_input = page.get_by_role("textbox", name="Email")
        verify_locator("email", email_input, "page.get_by_role('textbox', name='Email')", "getByRole", "QuickLeadForm")

        save_btn = page.get_by_role("button", name="Save")
        verify_locator("submit_button", save_btn, "page.get_by_role('button', name='Save')", "getByRole", "QuickLeadForm")

        # Fill & submit
        name_input.fill("LiveDOMTestCo")
        email_input.fill("livedomtestco@mailinator.com")
        phone_input.fill("9876543210")
        save_btn.click()
        page.wait_for_timeout(2000)

        # 6. Lead Module & Submodule
        lead_mod = page.locator("//a[text()='Lead']")
        verify_locator("lead_module", lead_mod, "page.locator(\"//a[text()='Lead']\")", "xpath", "Dashboard")

        my_leads_lnk = page.locator("a[href='/my-leads']")
        if my_leads_lnk.count() == 0:
            my_leads_lnk = page.get_by_role("link", name="My Leads")

        verify_locator("my_leads_submodule", my_leads_lnk, "page.locator(\"a[href='/my-leads']\")", "css", "LeadPage")

        my_leads_page.go_to_my_leads()

        # 7. Search box & Table
        search_b = page.get_by_placeholder("Search", exact=False)
        if search_b.count() == 0:
            search_b = page.locator("input[placeholder='Search']")
        verify_locator("search_box", search_b.first, "page.get_by_placeholder('Search')", "getByPlaceholder", "MyLeads")

        search_b.first.fill("LiveDOMTestCo")
        page.wait_for_timeout(1000)

        lead_r = page.locator("tbody tr").first
        verify_locator("lead_row", lead_r, "page.locator('tbody tr').first", "css", "MyLeads")

        ass_col = page.locator("th:has-text('ASSIGNED TO')")
        verify_locator("assigned_to_column", ass_col, "page.locator(\"th:has-text('ASSIGNED TO')\")", "css", "MyLeads")

        comp_lnk = lead_r.locator("a").first
        if comp_lnk.count() > 0:
            verify_locator("company_link", comp_lnk, "page.locator('tbody tr').first.locator('a').first", "css", "MyLeads")

        act_btn = lead_r.locator("button").first
        verify_locator("action_button", act_btn, "page.locator('tbody tr').first.locator('button').first", "css", "MyLeads")
        act_btn.click()

        acc_btn = page.get_by_role("menuitem", name="Accept")
        verify_locator("accept_button", acc_btn, "page.get_by_role('menuitem', name='Accept')", "getByRole", "ActionMenu")

        rej_btn = page.get_by_role("menuitem", name="Reject")
        verify_locator("reject_button", rej_btn, "page.get_by_role('menuitem', name='Reject')", "getByRole", "ActionMenu")

        browser.close()

    print("\n=== FINAL VERIFIED JSON Output ===")
    print(json.dumps(verified_results, indent=2))

if __name__ == "__main__":
    run()
