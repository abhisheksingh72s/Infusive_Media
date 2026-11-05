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

    # Click xUnit project
    xunit = page.locator("tbody tr:has-text('xUnit') td:nth-child(2)").first
    if xunit.count() > 0:
        print("Clicking xUnit project:", xunit.inner_text().strip())
        xunit.click()
    else:
        print("Clicking first project")
        page.locator("tbody tr td:nth-child(2)").first.click()
    page.wait_for_timeout(2000)

    # 1. Inspect Project Details Tab (Tab 0)
    print("\n================ INSPECTING PROJECT DETAILS TAB ================")
    tab0 = page.locator("button.project-tab[role='tab']").first
    print("Tab 0 text:", tab0.inner_text().strip())
    tab0.click()
    page.wait_for_timeout(1500)
    
    # Check for warning banners
    warnings = page.locator(".chakra-alert, [role='alert'], .chakra-card:has-text('Incomplete')").all()
    print("Warnings on Project Details:", [w.inner_text().strip() for w in warnings if w.is_visible()])

    # Print all key-value pairs or text in Project Details
    panel0 = page.locator("[role='tabpanel']").first
    with open("scratch/project_details_dump.html", "w", encoding="utf-8") as f:
        f.write(panel0.inner_html())
    print("Project Details HTML dumped. Searching for labels and values...")
    
    # Check Edit Project button
    edit_btn = panel0.locator("button").filter(has_text="Edit Project").first
    print("Edit Project button exists:", edit_btn.count() > 0, "visible:", edit_btn.is_visible())

    # 2. Check Resource Allocation Tab (Tab 2)
    print("\n================ INSPECTING RESOURCE ALLOCATION TAB ================")
    res_tab = page.locator("button.project-tab[role='tab']").filter(has_text="Resource Allocation").first
    if res_tab.count() > 0:
        res_tab.click()
        page.wait_for_timeout(2000)
        panel = page.locator("[role='tabpanel']").filter(has_text="Resource").first
        with open("scratch/resource_alloc_dump.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        rows = page.locator("tbody tr").all()
        print(f"Allocated resources rows: {len(rows)}")
        for r in rows:
            print("  Allocated:", r.inner_text().strip().replace("\n", " | "))

    browser.close()
