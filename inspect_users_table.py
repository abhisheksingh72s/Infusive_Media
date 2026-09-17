import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

BASE_URL = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")
ADMIN_EMAIL = os.getenv("EMAIL", "Admin@infusive.com")
ADMIN_PASS = os.getenv("PASSWORD", "123456")

print(f"Logging in as Admin: {ADMIN_EMAIL}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(BASE_URL)
    page.wait_for_timeout(2000)

    # Login Admin
    page.get_by_role("textbox", name="Email").fill(ADMIN_EMAIL)
    page.get_by_role("textbox", name="Password").fill(ADMIN_PASS)
    page.get_by_role("button", name="Login").click()
    page.wait_for_timeout(3000)

    # Go to Admin Controller -> Users
    admin_link = page.get_by_role("link", name="Admin Controller").first
    if admin_link.is_visible():
        admin_link.click()
        page.wait_for_timeout(500)
    
    users_link = page.get_by_role("link", name="• Users").first
    if users_link.is_visible():
        users_link.click()
    else:
        page.goto(f"{BASE_URL.replace('/login', '')}/users")

    page.wait_for_selector("table", timeout=15000)
    page.wait_for_timeout(2000)
    print("Users page URL:", page.url)

    # Headers
    headers = page.locator("thead th").all()
    header_texts = [h.inner_text().strip() for h in headers]
    print("Table Headers:", header_texts)

    # Search for BDM
    search_inp = page.locator("input[placeholder*='Search']").first
    if search_inp.is_visible():
        search_inp.fill("BDM")
        search_inp.press("Enter")
        page.wait_for_timeout(2000)

    # Rows
    rows = page.locator("tbody tr").all()
    print(f"Found {len(rows)} matching rows:")
    for idx, row in enumerate(rows):
        cells = [c.inner_text().strip() for c in row.locator("td").all()]
        print(f" Row {idx+1}: {cells}")

    browser.close()
