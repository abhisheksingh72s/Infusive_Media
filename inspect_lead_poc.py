import os
import time
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

PRE_EMAIL = os.getenv("USER_08_EMAIL", "PreSales2@mailinator.com")
PRE_PASS = os.getenv("USER_08_PASSWORD", "123456")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login"))
    page.get_by_role("textbox", name="Email").fill(PRE_EMAIL)
    page.get_by_role("textbox", name="Password").fill(PRE_PASS)
    page.get_by_role("button", name="Login").click()
    page.wait_for_timeout(4000)

    print("Current URL after login:", page.url)

    # Let's inspect sidebar navigation links
    side_links = page.locator("a").all()
    print(f"\nTotal links ({len(side_links)}):")
    for a in side_links:
        try:
            txt = a.inner_text().strip()
            href = a.get_attribute("href")
            if txt or href:
                print(f"Link text: '{txt}' | href: '{href}'")
        except Exception:
            pass

    browser.close()
