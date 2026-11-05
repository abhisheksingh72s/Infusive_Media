import sys
import shutil
import os
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    
    print("1. Logging in as Admin...")
    page.goto("https://infusive-front.jobvritta.com/login", wait_until="domcontentloaded")
    page.get_by_role("textbox", name="Email").fill("Admin@infusive.com")
    page.get_by_role("textbox", name="Password").fill("123456")
    page.get_by_role("button", name="Login").click()
    page.wait_for_url("**/dashboard**", timeout=20000)
    
    print("2. Navigating to /projects...")
    page.goto("https://infusive-front.jobvritta.com/projects", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    
    print("3. Opening 'xUnit Test Project'...")
    xunit = page.locator("tbody tr:has-text('xUnit') td:nth-child(2)").first
    xunit.click()
    page.wait_for_timeout(2000)
    
    print("4. Opening 'Task Management' tab...")
    task_tab = page.locator("button.project-tab[role='tab']").filter(has_text="Task Management").first
    task_tab.click()
    page.wait_for_timeout(3000)
    
    # Locate all rows in Task Management table
    rows = page.locator("tbody tr").all()
    print(f"Total task rows found: {len(rows)}")
    
    matched_row = None
    task_details = []
    for r in rows:
        txt = r.inner_text().strip().replace("\n", " | ")
        print("Row:", txt)
        if "LiveTrigger" in txt:
            matched_row = r
            task_details.append(txt)
            
    if matched_row:
        print("\n--- CONFIRMED CREATED TASK IN DATABASE / UI ---")
        for td in task_details:
            print("EVIDENCE ROW:", td)
            
        matched_row.scroll_into_view_if_needed()
        matched_row.evaluate("el => { el.style.border = '4px solid #10B981'; el.style.backgroundColor = '#ECFDF5'; }")
        page.wait_for_timeout(500)
        
        artifact_dir = r"C:\Users\User\.gemini\antigravity-ide\brain\b4caa5aa-f3dc-4d03-bcc8-be991e671103"
        screenshot_path = os.path.join(artifact_dir, "evidence_task_created.png")
        page.screenshot(path=screenshot_path)
        print(f"Evidence screenshot saved to: {screenshot_path}")
    else:
        print("WARNING: Could not find LiveTrigger task in rows.")
        
    browser.close()
