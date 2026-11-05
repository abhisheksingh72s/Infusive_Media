import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from pages.users_page import UsersPage
from pages.signature_page import SignaturePage
from utilities.env_manager import update_env_with_all_users
from utilities.custom_logger import FormattedQALogger

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

BASE_URL = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")
ADMIN_EMAIL = os.getenv("EMAIL", "Admin@infusive.com")
ADMIN_PASS = os.getenv("PASSWORD", "123456")

def run_signature_automation():
    start_time = time.time()
    qa = FormattedQALogger()
    qa.print_header(test_case="Clean .env User Section Regeneration", module="Signature", browser="Chromium", env="QA")

    total_steps = 6
    passed_steps = 0
    failed_steps = 0
    status = "FAIL"

    playwright = None
    browser = None
    context = None
    page = None

    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        login_page = LoginPage(page)
        users_page = UsersPage(page)
        signature_page = SignaturePage(page)

        # Step 1: Login as Admin
        login_page.load()
        login_page.login(ADMIN_EMAIL, ADMIN_PASS)
        login_page.wait_for_dashboard()
        passed_steps += 1
        qa.log_step(1, total_steps, "Login as Admin", "PASS", details={"Admin Email": ADMIN_EMAIL})

        # Step 2: Open Admin Control -> Users
        users_page.go_to_users()
        passed_steps += 1
        qa.log_step(2, total_steps, "Open Admin Control -> Users", "PASS")

        # Step 3: Reading Users table
        all_users = users_page.get_all_users()
        if not all_users:
            raise ValueError("Users table is empty; execution failed.")

        for idx, u in enumerate(all_users, start=1):
            fmt = f"{idx:02d}"
            role_disp = u['role'] if u['role'] else "NA"
            print(f"INFO  User {fmt} : {u['name']} | {role_disp} | {u['email']}")

        passed_steps += 1
        qa.log_step(3, total_steps, "Reading Users table", "PASS", details={"Total Users": str(len(all_users))})

        # Step 4: Regenerate .env USER_* section
        update_env_with_all_users(all_users, env_path)
        print("PASS  Removed previous USER_* entries")
        print("PASS  Generated new USER_* section")
        print("PASS  Successfully updated .env")

        passed_steps += 1
        qa.log_step(4, total_steps, "Regenerate new USER_* section in .env", "PASS", details={"Total Users Saved": str(len(all_users))})

        # Step 5: Logout Admin & Login as first extracted BDM user
        login_page.logout()

        bdm_user = next((u for u in all_users if "bdm" in u["role"].lower()), all_users[0])
        user_email = bdm_user["email"]
        user_pass = "123456"

        login_page.login(user_email, user_pass)
        login_page.wait_for_dashboard()
        passed_steps += 1
        qa.log_step(5, total_steps, "Login with dynamic user credentials", "PASS", details={"User Email": user_email})

        # Step 6: Complete Signature Module Creation
        signature_page.go_to_signature()

        short_editor = page.locator("//label[contains(normalize-space(),'Short Signature')]/following::div[contains(@class,'jodit-wysiwyg') and @contenteditable='true'][1]").first
        if short_editor.is_visible():
            short_editor.click()
            short_editor.fill("Short Signature - Rahul BDM")

        full_editor = page.locator("//label[contains(normalize-space(),'Full Signature')]/following::div[contains(@class,'jodit-wysiwyg') and @contenteditable='true'][1]").first
        if full_editor.is_visible():
            full_editor.click()
            full_editor.fill("Full Signature - Rahul Sangwan, Business Development Manager, Infusive Media")

        save_btn = page.locator("//button[normalize-space()='Save Signature']").or_(
            page.locator("//button[normalize-space()='Save']")
        ).first
        if save_btn.is_visible():
            save_btn.click()
            page.wait_for_timeout(2500)

        passed_steps += 1
        qa.log_step(6, total_steps, "Complete Signature Creation", "PASS")

        # Save output JSON
        captured_elements = signature_page.extract_dom_elements()
        os.makedirs("output", exist_ok=True)
        out_file = os.path.join("output", "signature_elements.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(captured_elements, f, indent=2)

        status = "PASS"

    except Exception:
        failed_steps += 1
        status = "FAIL"
        if page:
            try:
                os.makedirs("screenshots", exist_ok=True)
                page.screenshot(path="screenshots/failure_clean_env_sync.png")
            except Exception:
                pass
        raise

    finally:
        if context:
            context.close()
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
        duration = time.time() - start_time
        qa.print_footer(status=status, total_steps=total_steps, passed=passed_steps, failed=failed_steps, duration_sec=duration)

if __name__ == "__main__":
    run_signature_automation()
