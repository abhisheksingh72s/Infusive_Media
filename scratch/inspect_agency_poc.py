import os
import sys
import time
from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        # 1. Login via Admin
        print("Logging in as Admin...")
        page.goto("https://infusive-front.jobvritta.com/login")
        page.get_by_role("textbox", name="Email").fill("Admin@infusive.com")
        page.get_by_role("textbox", name="Password").fill("123456")
        page.get_by_role("button", name="Sign In").click()
        page.wait_for_url("**/dashboard**", timeout=15000)
        
        # 2. Go to Agency
        page.goto("https://infusive-front.jobvritta.com/agency")
        page.wait_for_timeout(3000)
        print("On Agency page. URL:", page.url)
        
        # 3. Find table rows
        rows = page.locator("tbody tr").all()
        print(f"Found {len(rows)} table rows.")
        if rows:
            first_row = rows[0]
            print("First row text:", first_row.inner_text().strip().replace("\n", " "))
            
            # Find action column buttons in the first row
            action_btns = first_row.locator("button, a, svg").all()
            print(f"Found {len(action_btns)} action elements in first row.")
            for i, btn in enumerate(action_btns):
                try:
                    if btn.is_visible():
                        txt = btn.inner_text().strip()
                        html = btn.evaluate("e => e.outerHTML[:120]")
                        print(f"  Action el [{i}]: text='{txt}', html='{html}'")
                except Exception:
                    pass
            
            # Try clicking the '+' button in the row
            plus_btn = first_row.locator("//button[contains(.,'+')] | //a[contains(.,'+')] | //*[name()='svg' and contains(@class,'plus')] | //button[last()]").first
            if not plus_btn.is_visible():
                plus_btn = first_row.locator("td:last-child button, td:last-child a, td:last-child svg").last
            
            if plus_btn.is_visible():
                print("Clicking Plus (+) button on first row...")
                plus_btn.click()
                page.wait_for_timeout(2000)
                
                os.makedirs("scratch", exist_ok=True)
                page.screenshot(path="scratch/after_plus_clicked.png")
                print("Saved scratch/after_plus_clicked.png")
                
                # Print all visible buttons, links, text after clicking '+'
                print("\nVisible elements after clicking '+' button:")
                elements = page.locator("button, a, p, h1, h2, h3, h4, span, div.btn").all()
                for i, el in enumerate(elements):
                    try:
                        if el.is_visible():
                            txt = el.inner_text().strip().replace("\n", " ")
                            if txt and len(txt) < 80:
                                print(f"  [{i}] tag={el.evaluate('e => e.tagName')}, text='{txt}'")
                    except Exception:
                        pass
                        
                # Look for 'Add Agency POC' or 'Add POC' or '+' button in modal/drawer
                add_poc_btn = page.get_by_role("button", name="Add Agency POC")
                if not add_poc_btn.is_visible():
                    add_poc_btn = page.get_by_text("Add Agency POC", exact=False)
                if not add_poc_btn.is_visible():
                    add_poc_btn = page.locator("//button[contains(.,'POC') or contains(.,'Poc') or contains(.,'Add')]")
                    
                print("\nAdd Agency POC button visible:", add_poc_btn.first.is_visible() if add_poc_btn.count() > 0 else False)
                if add_poc_btn.count() > 0 and add_poc_btn.first.is_visible():
                    add_poc_btn.first.click()
                    print("Clicked 'Add Agency POC' button!")
                    page.wait_for_timeout(2000)
                    page.screenshot(path="scratch/add_poc_form.png")
                    print("Saved scratch/add_poc_form.png")
                    
                    # Print form fields
                    print("\nInspecting inputs/labels on Add Agency POC form:")
                    form_elements = page.locator("label, input, select, textarea, button").all()
                    for fe in form_elements:
                        try:
                            if fe.is_visible():
                                txt = fe.inner_text().strip().replace("\n", " ")
                                placeholder = fe.get_attribute("placeholder") or ""
                                name_attr = fe.get_attribute("name") or ""
                                type_attr = fe.get_attribute("type") or ""
                                print(f"  Field tag={fe.evaluate('e => e.tagName')}: text='{txt}', placeholder='{placeholder}', name='{name_attr}', type='{type_attr}'")
                        except Exception:
                            pass
        
        browser.close()

if __name__ == "__main__":
    inspect()
