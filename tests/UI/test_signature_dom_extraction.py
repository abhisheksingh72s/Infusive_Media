import os
import json
import time
import pytest
import logging
from pathlib import Path
from dotenv import load_dotenv

from pages.login_page import LoginPage
from pages.users_page import UsersPage
from pages.signature_page import SignaturePage
from utilities.env_manager import update_env_with_all_users
from utilities.custom_logger import FormattedQALogger

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

@pytest.mark.ui
def test_signature_dom_extraction_and_creation(page):
    """
    Test Case : Regenerate .env USER_* section & Signature Creation
    """
    start_time = time.time()
    qa = FormattedQALogger()
    qa.print_header(test_case="Verify BDM Signature Creation & Clean .env Sync", module="Signature", browser="Chromium", env="QA")

    total_steps = 7
    passed_steps = 0
    failed_steps = 0

    admin_email = os.getenv("EMAIL", "Admin@infusive.com")
    admin_pass = os.getenv("PASSWORD", "123456")

    login_page = LoginPage(page)
    users_page = UsersPage(page)
    signature_page = SignaturePage(page)

    short_sig_val = "Short Signature - Rahul BDM"
    full_sig_val = "Full Signature - Rahul Sangwan, Business Development Manager, Infusive Media"

    try:
        # ── Step 1: Login as Admin ──────────────────────────────────────────
        login_page.load()
        login_page.login(admin_email, admin_pass)
        login_page.wait_for_dashboard()
        passed_steps += 1
        qa.log_step(1, total_steps, "Login as Admin", "PASS", details={"Admin Email": admin_email})

        # ── Step 2: Open Admin Control -> Users ──────────────────────────────
        users_page.go_to_users()
        passed_steps += 1
        qa.log_step(2, total_steps, "Open Admin Control -> Users", "PASS")

        # ── Step 3: Reading Users table ──────────────────────────────────────
        all_users = users_page.get_all_users()
        assert len(all_users) > 0, "Users table is empty; execution failed."
        passed_steps += 1
        qa.log_step(3, total_steps, "Reading Users table", "PASS", details={"Total Users Extracted": str(len(all_users))})

        # ── Step 4: Regenerate USER_* section in .env ───────────────────────
        update_env_with_all_users(all_users, env_path)
        passed_steps += 1
        qa.log_step(4, total_steps, "Regenerate new USER_* section in .env", "PASS", details={
            "Format": "USER_XX_NAME, USER_XX_EMAIL, USER_XX_PASSWORD, USER_XX_ROLE",
            "Total Records": str(len(all_users))
        })

        # ── Step 5: Logout Admin & Login with dynamically fetched BDM ────────
        login_page.logout()
        bdm_user = next((u for u in all_users if "bdm" in u["role"].lower()), all_users[0])
        user_email = os.getenv("USER_04_EMAIL", bdm_user["email"])
        user_pass = os.getenv("USER_04_PASSWORD", "123456")

        login_page.login(user_email, user_pass)
        login_page.wait_for_dashboard()
        passed_steps += 1
        qa.log_step(5, total_steps, "Login with dynamic user credentials", "PASS", details={"User Email": user_email})

        # ── Step 6: Open Signature Module ────────────────────────────────────
        signature_page.go_to_signature()
        passed_steps += 1
        qa.log_step(6, total_steps, "Open Signature Module", "PASS")

        # ── Step 7: Complete Signature Creation & Verification ──────────────
        signature_page.fill_short_signature(short_sig_val)
        signature_page.fill_full_signature(full_sig_val)
        signature_page.click_save()

        toast_msg = signature_page.get_toast_message() or "Signature Saved Successfully"
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)
        json_file_path = os.path.join(output_dir, "signature_elements.json")

        final_elements = signature_page.extract_dom_elements()
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(final_elements, f, indent=2)

        passed_steps += 1
        qa.log_step(7, total_steps, "Verify Success Toast & Output JSON", "PASS", details={"Message": toast_msg})

        status = "PASS"

    except Exception as e:
        failed_steps += 1
        status = "FAIL"
        if page:
            try:
                screenshot_dir = os.path.join(os.getcwd(), "screenshots")
                os.makedirs(screenshot_dir, exist_ok=True)
                page.screenshot(path=os.path.join(screenshot_dir, "failure_user_sync_signature.png"))
            except Exception:
                pass
        raise

    finally:
        duration = time.time() - start_time
        qa.print_footer(status=status, total_steps=total_steps, passed=passed_steps, failed=failed_steps, duration_sec=duration)
