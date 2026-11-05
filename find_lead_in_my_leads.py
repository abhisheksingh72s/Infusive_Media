import os
import time
import pytest
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from pages.login_page import LoginPage
from pages.company_page import CompanyPage

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

accounts = [
    ("Admin@infusive.com", "123456"),
    ("PreSales2@mailinator.com", "123456"),
    ("rahulsang2118@gmail.com", "123456"),
    ("abhisheksingh7266833285@gmail.com", "1234567"),
    ("bdm3@mailinator.com", "123456"),
    ("TeamLead1@mailinator.com", "123456"),
]

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        login_page = LoginPage(page)
        company_page = CompanyPage(page)

        # 1. Login PreSales & Create unique Quick Lead
        login_page.load()
        login_page.login("PreSales2@mailinator.com", "123456")
        login_page.wait_for_dashboard()

        ts = str(int(time.time()))
        co_name = f"FindCo{ts}"
        phone = f"9{ts[-9:]}"

        company_page.go_to_company()
        company_page.click_add_quick_lead()
        company_page.fill_quick_lead_form(
            name=co_name,
            email=f"{co_name.lower()}@mailinator.com",
            phone=phone,
            country="United States",
            country_code="+1"
        )
        page.get_by_role("button", name="Save").click()
        page.wait_for_timeout(2000)

        print(f"Created Quick Lead: '{co_name}'")

        # 2. Check every account's /my-leads page
        for email, passw in accounts:
            try:
                page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
                page.context.clear_cookies()
            except Exception:
                pass

            page.goto("https://infusive-front.jobvritta.com/login")
            login_page.login(email, passw)
            try:
                login_page.wait_for_dashboard()
            except Exception:
                print(f"Login failed for {email}")
                continue

            page.goto("https://infusive-front.jobvritta.com/my-leads")
            page.wait_for_timeout(2000)

            search_box = page.get_by_placeholder("Search", exact=False)
            if search_box.count() > 0:
                search_box.first.fill(co_name)
                page.wait_for_timeout(1000)

            rows = page.locator("tbody tr")
            if rows.count() > 0 and co_name in rows.first.inner_text():
                print(f"🎉 FOUND '{co_name}' IN MY LEADS FOR ACCOUNT: {email}!")
                print("Row text:", rows.first.inner_text())
                break
            else:
                print(f"Not in /my-leads for {email} (rows count: {rows.count()})")

        browser.close()

if __name__ == "__main__":
    run()
