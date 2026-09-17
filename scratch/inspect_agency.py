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
        print("Logged in successfully! URL:", page.url)
        
        # 2. Click Master module
        print("\nSearching for Master module in sidebar...")
        master_elements = page.locator("//*[contains(text(), 'Master')]").all()
        print(f"Found {len(master_elements)} elements with text 'Master':")
        for i, el in enumerate(master_elements):
            try:
                print(f"  [{i}] tag={el.evaluate('e => e.tagName')}, text='{el.inner_text().strip()}', visible={el.is_visible()}")
            except Exception as e:
                pass
                
        # Click Master module
        master_lnk = page.get_by_text("Master", exact=True)
        if master_lnk.is_visible():
            master_lnk.click()
            print("Clicked Master link.")
            page.wait_for_timeout(1000)
        else:
            print("Master link (exact) not visible, trying containing 'Master'")
            page.locator("//*[text()='Master']").first.click()
            page.wait_for_timeout(1000)
            
        # 3. Check Agency sub-module
        print("\nSearching for Agency sub-module...")
        agency_elements = page.locator("//*[contains(text(), 'Agency')]").all()
        print(f"Found {len(agency_elements)} elements with text 'Agency':")
        for i, el in enumerate(agency_elements):
            try:
                print(f"  [{i}] tag={el.evaluate('e => e.tagName')}, text='{el.inner_text().strip()}', visible={el.is_visible()}")
            except Exception as e:
                pass

        # Click Agency
        agency_lnk = page.get_by_text("Agency", exact=True)
        if agency_lnk.is_visible():
            agency_lnk.click()
            print("Clicked Agency sub-module.")
        else:
            print("Agency link (exact) not visible, navigating directly to /agency")
            page.goto("https://infusive-front.jobvritta.com/agency")
            
        page.wait_for_timeout(3000)
        print("Current URL:", page.url)
        
        # Save screenshot of Agency listing
        os.makedirs("scratch", exist_ok=True)
        page.screenshot(path="scratch/agency_listing.png")
        print("Saved scratch/agency_listing.png")
        
        # 4. Find all buttons / clickable options on Agency page
        print("\nButtons on Agency page:")
        buttons = page.locator("button, [role='button'], a.btn, div.btn").all()
        for idx, btn in enumerate(buttons):
            try:
                if btn.is_visible():
                    txt = btn.inner_text().strip().replace("\n", " ")
                    print(f"  Button {idx}: text='{txt}', tag={btn.evaluate('e => e.tagName')}, html='{btn.evaluate('e => e.outerHTML[:100]')}'")
            except Exception:
                pass

        # Find element for 'Add Options' or 'Add' or '+'
        add_opts = page.get_by_role("button", name="Add Options")
        if not add_opts.is_visible():
            add_opts = page.locator("//button[contains(.,'Add Options')]")
        if not add_opts.is_visible():
            add_opts = page.locator("//button[contains(.,'Add')]")
            
        print(f"\nAdd Options button visible: {add_opts.first.is_visible() if add_opts.count() > 0 else False}")
        if add_opts.count() > 0 and add_opts.first.is_visible():
            add_opts.first.click()
            print("Clicked Add Options button!")
            page.wait_for_timeout(1000)
            page.screenshot(path="scratch/add_options_clicked.png")
            print("Saved scratch/add_options_clicked.png")
            
            # Print menu items or visible text after clicking Add Options
            print("\nVisible menu items or options after clicking Add Options:")
            menu_items = page.locator("li, [role='menuitem'], p, span, button, a").all()
            for i, mi in enumerate(menu_items):
                try:
                    if mi.is_visible():
                        txt = mi.inner_text().strip().replace("\n", " ")
                        if "Agency" in txt or "Add" in txt:
                            print(f"  Item {i}: text='{txt}', tag={mi.evaluate('e => e.tagName')}, html='{mi.evaluate('e => e.outerHTML[:120]')}'")
                except Exception:
                    pass
                    
            # Try clicking 'Add New Agency'
            add_new_agency = page.get_by_text("Add New Agency")
            if add_new_agency.first.is_visible():
                add_new_agency.first.click()
                print("Clicked 'Add New Agency' menu item!")
                page.wait_for_timeout(2000)
                page.screenshot(path="scratch/add_agency_form.png")
                print("Saved scratch/add_agency_form.png")
                
                # Inspect form elements
                print("\nInspecting inputs/labels/headings on Add New Agency form:")
                labels = page.locator("label, h1, h2, h3, h4, h5, h6, form, input, select, button").all()
                for l in labels:
                    try:
                        if l.is_visible():
                            txt = l.inner_text().strip().replace("\n", " ")
                            placeholder = l.get_attribute("placeholder") or ""
                            name_attr = l.get_attribute("name") or ""
                            if txt or placeholder or name_attr:
                                print(f"  Element tag={l.evaluate('e => e.tagName')}: text='{txt}', placeholder='{placeholder}', name='{name_attr}'")
                    except Exception:
                        pass
            else:
                print("'Add New Agency' text NOT visible!")
        
        browser.close()

if __name__ == "__main__":
    inspect()
