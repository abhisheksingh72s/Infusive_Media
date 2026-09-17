import os
import time
import pytest
from pathlib import Path
from dotenv import load_dotenv

from pages.login_page import LoginPage
from pages.company_page import CompanyPage
from pages.lead_page import LeadPoolPage, MyLeadsPage, DynamicTable

load_dotenv(dotenv_path=Path(".env"), override=True)

def _logout(page) -> None:
    try:
        page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        page.context.clear_cookies()
    except Exception:
        pass
    from urllib.parse import urlparse
    parsed = urlparse(page.url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    page.goto(f"{base_url}/login", wait_until="domcontentloaded")
    page.wait_for_url("**/login", timeout=15_000)

@pytest.mark.ui
def test_diagnostic_lead_flow(page):
    login_page = LoginPage(page)
    company_page = CompanyPage(page)

    presales_email = os.getenv("USER_11_EMAIL", "PreSales2@mailinator.com")
    presales_pass = os.getenv("USER_11_PASSWORD", "123456")

    ts = str(int(time.time()))
    company_name = f"DiagCo{ts}"
    phone = f"9{ts[-9:]}"

    # 1. Login PreSales & Create Quick Lead
    login_page.load()
    login_page.login(presales_email, presales_pass)
    login_page.wait_for_dashboard()

    company_page.go_to_company()
    company_page.click_add_quick_lead()
    company_page.fill_quick_lead_form(
        name=company_name,
        email=f"{company_name.lower()}@mailinator.com",
        phone=phone,
        country="United States",
        country_code="+1"
    )
    page.get_by_role("button", name="Save").click()
    page.wait_for_timeout(2000)

    # 2. Check where it appears for PreSales (Lead Pool / Company List)
    print("\n=== PRESALES VIEW ===")
    page.goto("https://infusive-front.jobvritta.com/lead-pool")
    page.wait_for_timeout(2000)
    search_b = page.get_by_placeholder("Search", exact=False)
    if search_b.count() > 0:
        search_b.first.fill(company_name)
        page.wait_for_timeout(1000)

    try:
        table = DynamicTable(page)
        row = table.find_row(column="COMPANY", value=company_name, match_partial=True)
        print("FOUND IN PRESALES LEAD POOL!")
        print("Row data:", row.get_all_values())
    except Exception as e:
        print("NOT in PreSales Lead Pool:", e)

    # 3. Check Admin view
    _logout(page)
    login_page.login("Admin@infusive.com", "123456")
    login_page.wait_for_dashboard()
    print("\n=== ADMIN VIEW ===")
    page.goto("https://infusive-front.jobvritta.com/lead-pool")
    page.wait_for_timeout(2000)
    search_b = page.get_by_placeholder("Search", exact=False)
    if search_b.count() > 0:
        search_b.first.fill(company_name)
        page.wait_for_timeout(1000)

    try:
        table = DynamicTable(page)
        row = table.find_row(column="COMPANY", value=company_name, match_partial=True)
        print("FOUND IN ADMIN LEAD POOL!")
        print("Row data:", row.get_all_values())
    except Exception as e:
        print("NOT in Admin Lead Pool:", e)

    # 4. Check TeamLead view
    _logout(page)
    login_page.login("TeamLead1@mailinator.com", "123456")
    login_page.wait_for_dashboard()
    print("\n=== TEAMLEAD VIEW ===")
    page.goto("https://infusive-front.jobvritta.com/my-leads")
    page.wait_for_timeout(2000)
    search_b = page.get_by_placeholder("Search", exact=False)
    if search_b.count() > 0:
        search_b.first.fill(company_name)
        page.wait_for_timeout(1000)

    try:
        table = DynamicTable(page)
        row = table.find_row(column="COMPANY", value=company_name, match_partial=True)
        print("FOUND IN TEAMLEAD MY LEADS!")
        print("Row data:", row.get_all_values())
    except Exception as e:
        print("NOT in TeamLead My Leads:", e)
