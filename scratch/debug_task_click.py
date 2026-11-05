import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    page.goto("https://infusive-front.jobvritta.com/login", wait_until="domcontentloaded")
    page.get_by_role("textbox", name="Email").fill("Admin@infusive.com")
    page.get_by_role("textbox", name="Password").fill("123456")
    page.get_by_role("button", name="Login").click()
    page.wait_for_url("**/dashboard**", timeout=20000)

    page.goto("https://infusive-front.jobvritta.com/projects", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    page.locator("tbody tr td:nth-child(2)").first.click()
    page.wait_for_timeout(2000)

    # Click Task Management
    task_tab = page.locator("button, [role='tab'], p, div").filter(has_text="Task Management").first
    task_tab.click()
    page.wait_for_timeout(2000)

    # Click Add Task
    add_btn = page.locator("button, [role='button'], a, span, div").filter(has_text="Add Task").locator("visible=true").first
    print("Clicking Add Task...")
    add_btn.click()
    page.wait_for_timeout(3000)

    print("Current URL after clicking Add Task:", page.url)

    # List all visible inputs on the page
    inputs = page.locator("input, select, textarea, [role='dialog'], form").all()
    print(f"Total form/input elements found: {len(inputs)}")
    for i, inp in enumerate(inputs):
        try:
            if inp.is_visible():
                tag = inp.evaluate("e => e.tagName.toLowerCase()")
                name = inp.get_attribute("name") or inp.get_attribute("placeholder") or inp.get_attribute("aria-label") or ""
                inp_type = inp.get_attribute("type") or ""
                print(f"  Visible [{i}]: tag={tag}, type={inp_type}, name/placeholder='{name}'")
        except Exception:
            pass

    browser.close()
