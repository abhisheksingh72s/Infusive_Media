import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    print("1. Logging in as Admin...")
    page.goto("https://infusive-front.jobvritta.com/login", wait_until="domcontentloaded")
    page.get_by_role("textbox", name="Email").fill("Admin@infusive.com")
    page.get_by_role("textbox", name="Password").fill("123456")
    page.get_by_role("button", name="Login").click()
    page.wait_for_url("**/dashboard**", timeout=20000)

    print("2. Navigating to /projects...")
    page.goto("https://infusive-front.jobvritta.com/projects", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # 3. Click Project Name
    print("3. Clicking Project Name...")
    xunit_row = page.locator("tbody tr:has-text('xUnit') td:nth-child(2)").first
    if xunit_row.count() > 0:
        proj_name = xunit_row.inner_text().strip()
        print("Project selected (with active resources):", proj_name)
        xunit_row.click()
    else:
        proj_link = page.locator("tbody tr td:nth-child(2)").first
        proj_name = proj_link.inner_text().strip()
        print("Project selected:", proj_name)
        proj_link.click()
    page.wait_for_timeout(2000)

    # 4. Click Task Management tab
    print("4. Clicking Task Management tab: button.project-tab[role='tab']...")
    task_tab = page.locator("button.project-tab[role='tab']:has-text('Task Management'), button[role='tab'][data-index='3']").first
    task_tab.click()
    page.wait_for_timeout(2000)

    # 5. Click Add Task
    print("5. Clicking Add Task button...")
    add_btn = page.locator("button.chakra-button").filter(has_text="Add Task").first
    add_btn.click()
    page.wait_for_timeout(2000)

    modal = page.locator("[role='dialog'], .chakra-modal__content").first
    task_name = f"LiveTrigger_{int(time.time())}"
    print("6. Filling Create Task modal with title:", task_name)

    # 1. Fill Task Name
    title_inp = modal.locator("input[name='title'], input[placeholder='Enter task name'], input.chakra-input").first
    title_inp.fill(task_name)
    print("Filled Task Name:", task_name)

    # 2. Select dropdown options
    def select_dropdown(ph, opt_index=0):
        print(f"Selecting dropdown: '{ph}'...")
        inp = modal.locator(f"input[placeholder='{ph}']").first
        if inp.count() == 0 or not inp.is_visible():
            print(f"  Field '{ph}' not found or not visible!")
            return False
        
        inp.scroll_into_view_if_needed()
        inp.click()
        page.wait_for_timeout(600)
        
        # Look for li elements inside this form control or modal
        menu_lis = inp.locator("xpath=following-sibling::div//li | xpath=..//li")
        try:
            menu_lis.first.wait_for(state="visible", timeout=3000)
            options = menu_lis.all()
        except Exception:
            options = page.locator("li.css-wnxomm").locator("visible=true").all()
        
        opt_texts = [o.inner_text().strip() for o in options]
        print(f"  Found {len(options)} options for '{ph}': {opt_texts}")
        
        if options:
            idx = min(opt_index, len(options) - 1)
            target = options[idx]
            chosen_txt = target.inner_text().strip()
            target.click()
            print(f"  Selected '{chosen_txt}' for '{ph}'")
            page.wait_for_timeout(500)
            return True
        else:
            print(f"  Fallback: pressing ArrowDown + Enter for '{ph}'")
            inp.press("ArrowDown")
            page.keyboard.press("Enter")
            page.wait_for_timeout(400)
            return False

    select_dropdown("Select Service", 0)
    select_dropdown("Select Milestone", 0)
    select_dropdown("Select Task Type", 0)
    select_dropdown("Select Employee", 0)
    select_dropdown("Select Reviewer", 0)

    # 3. Fill Date with an unassigned date within project timeframe
    # Check already assigned dates to prevent 'This resource already has a task assigned'
    import datetime
    import random
    
    # Pick a random date between 12 and 50 days from today (between Nov 10 and Dec 15, 2026)
    # Ensure it's not 2026-11-05 or 2026-12-30
    used_dates = ["2026-11-05", "2026-12-30"]
    candidate = datetime.date(2026, 11, 10)
    for offset in range(10, 50):
        test_d = (datetime.date(2026, 10, 28) + datetime.timedelta(days=offset)).strftime("%Y-%m-%d")
        if test_d not in used_dates:
            candidate_str = test_d
            break
    else:
        candidate_str = "2026-11-15"

    date_inp = modal.locator("input[type='date'], input[name='startDate']").first
    if date_inp.count() > 0 and date_inp.is_visible():
        print(f"Assigning dynamic unconflicted date: '{candidate_str}'...")
        date_inp.fill(candidate_str)

    # 4. Fill Description
    desc = modal.locator("textarea[placeholder='Add task description'], textarea").first
    if desc.count() > 0 and desc.is_visible():
        desc.fill("Automated task creation for notification event")

    # Log console and network
    page.on("console", lambda msg: print(f"[BROWSER CONSOLE] {msg.type}: {msg.text}"))
    page.on("request", lambda req: print(f"[NET REQ] {req.method} {req.url}") if "api" in req.url or "task" in req.url.lower() else None)
    page.on("response", lambda res: print(f"[NET RES] {res.status} {res.url} - {res.text()[:200] if 'api' in res.url else ''}") if "api" in res.url or "task" in res.url.lower() else None)

    # 5. Click Save Task
    print("7. Clicking Save Task...")
    save_btn = modal.locator("button").filter(has_text="Save Task").first
    print("Save btn enabled:", save_btn.is_enabled(), "visible:", save_btn.is_visible())
    save_btn.scroll_into_view_if_needed()
    save_btn.click()
    page.wait_for_timeout(4000)

    # Take screenshot of modal
    page.screenshot(path="scratch/after_save_task.png")
    print("Screenshot saved to scratch/after_save_task.png")

    # Check if modal is still open and if there are validation errors
    if modal.is_visible():
        errors = modal.locator(".chakra-form__error-message, [class*='error'], p[color*='red'], span[color*='red']").all()
        err_texts = [e.inner_text().strip() for e in errors if e.is_visible()]
        print("MODAL STILL OPEN! Validation errors found:", err_texts)
        # Also check all red or invalid elements
        invalid_inputs = modal.locator("[aria-invalid='true']").all()
        print("Aria-invalid inputs:", [inp.get_attribute("placeholder") or inp.get_attribute("name") for inp in invalid_inputs])
    else:
        print("MODAL CLOSED SUCCESSFULLY!")

    # Capture toast
    toast = page.locator("div[role='status'], div[role='alert'], .toast, [class*='toast']").first
    toast_txt = toast.inner_text().strip() if toast.is_visible() else "None"
    print("RESULT TOAST:", toast_txt)

    # Check task listing table
    page.wait_for_timeout(2000)
    for r in page.locator("tbody tr").all():
        txt = r.inner_text().strip().replace("\n", " ")
        if task_name in txt or "LiveTrigger" in txt:
            print("FOUND CREATED TASK IN TABLE:", txt)

    browser.close()
