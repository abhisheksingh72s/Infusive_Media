import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    page.goto("https://infusive-front.jobvritta.com/login", wait_until="domcontentloaded")
    page.get_by_role("textbox", name="Email").fill("Admin@infusive.com")
    page.get_by_role("textbox", name="Password").fill("123456")
    page.get_by_role("button", name="Login").click()
    page.wait_for_url("**/dashboard**", timeout=20000)

    page.goto("https://infusive-front.jobvritta.com/projects", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    page.locator("tbody tr td:nth-child(2)").first.click()
    page.wait_for_timeout(2000)

    page.locator("button.project-tab[role='tab']:has-text('Task Management'), button[role='tab'][data-index='3']").first.click()
    page.wait_for_timeout(2000)

    page.locator("button.chakra-button").filter(has_text="Add Task").first.click()
    page.wait_for_timeout(2000)

    modal = page.locator("[role='dialog'], .chakra-modal__content").first
    task_name = f"AutoTask_{int(time.time())}"
    modal.locator("input[name='title']").fill(task_name)

    for ph in ["Select Service", "Select Milestone", "Select Task Type", "Select Employee", "Select Reviewer"]:
        inp = modal.locator(f"input[placeholder='{ph}']")
        inp.click()
        page.wait_for_timeout(300)
        opts = inp.locator("..").locator("ul li").all()
        if opts:
            opts[0].click()
            page.wait_for_timeout(200)

    # Let's inspect React props on input[name='startDate'] and call onChange directly
    props_info = page.evaluate("""() => {
        const inp = document.querySelector("input[name='startDate']");
        const propKey = Object.keys(inp).find(k => k.startsWith('__reactProps'));
        if (propKey && inp[propKey] && inp[propKey].onChange) {
            inp[propKey].onChange({ target: { name: 'startDate', value: '2026-12-15' } });
            return 'Called onChange directly!';
        }
        return 'No onChange found: ' + propKey;
    }""")
    print("Props info:", props_info)
    page.wait_for_timeout(500)

    # Also test what happens if we select Date Range or Recurring
    print("Input value is now:", modal.locator("input[name='startDate']").input_value())

    save_btn = modal.locator("button:has-text('Save Task')").first
    save_btn.click()
    page.wait_for_timeout(3000)

    toast = page.locator("div[role='status'], div[role='alert'], .toast, [class*='toast']").first
    if toast.is_visible():
        print("TOAST:", toast.inner_text())

    browser.close()
