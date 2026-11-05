import os
import time
from pathlib import Path
import pytest
from dotenv import load_dotenv

from pages.login_page import LoginPage
from pages.lead_page import MyLeadsPage
from pages.follow_up_page import FollowUpPage
from test_data.dynamic import DynamicDataGenerator
from utilities import QALogger


@pytest.mark.ui
def test_create_follow_up_and_validate(page):
    """
    Test Case: Create Follow Up and Validate
    Enterprise QA CI/CD execution output using utilities.custom_logger.QALogger.
    """
    start_time = time.time()
    qa_logger = QALogger()

    qa_logger.print_test_header("Create Follow Up and Validate")

    # Load environment
    load_dotenv(dotenv_path=Path(".env"), override=True)
    email = os.getenv("USER_13_EMAIL")
    password = os.getenv("USER_13_PASSWORD")

    if not email or not password:
        qa_logger.report_failure(
            page=page,
            step_num=0,
            action_name="Load Environment Credentials",
            reason_str="USER_13_EMAIL and USER_13_PASSWORD missing from .env",
            exc=ValueError("USER_13_EMAIL and USER_13_PASSWORD must be defined in .env"),
            elapsed_seconds=time.time() - start_time,
        )

    login_page = LoginPage(page)
    my_leads_page = MyLeadsPage(page)
    follow_up_page = FollowUpPage(page)

    # Dynamic Indian data payload from test_data/dynamic
    follow_up_payload = DynamicDataGenerator.generate_follow_up_data()
    follow_up_date = follow_up_payload["date"]
    follow_up_time = follow_up_payload["time"]
    follow_up_channel = follow_up_payload["channel"]
    description = follow_up_payload["description"]

    # ── [1/7] Login as BDM2 ────────────────────────────────────────────────
    current_step = 1
    current_action = "Login as BDM2"
    try:
        login_page.load()
        login_page.enter_email(email)
        login_page.enter_password(password)
        login_page.click_login()
        login_page.wait_for_dashboard()
        qa_logger.log_step_pass(current_step, 7, current_action)
    except Exception as e:
        qa_logger.report_failure(
            page=page,
            step_num=1,
            action_name=current_action,
            reason_str=str(e),
            exc=e,
            elapsed_seconds=time.time() - start_time,
        )

    # ── [2/7] Navigate -> My Leads ──────────────────────────────────────────
    current_step = 2
    current_action = "Navigate -> My Leads"
    try:
        my_leads_page.go_to_my_leads()
        qa_logger.log_step_pass(current_step, 7, current_action)
    except Exception as e:
        qa_logger.report_failure(
            page=page,
            step_num=2,
            action_name=current_action,
            reason_str=str(e),
            exc=e,
            elapsed_seconds=time.time() - start_time,
        )

    # ── [3/7] Open Action Menu ─────────────────────────────────────────────
    current_step = 3
    current_action = "Open Action Menu"
    try:
        follow_up_page.open_action_menu()
        qa_logger.log_step_pass(current_step, 7, current_action)
    except Exception as e:
        qa_logger.report_failure(
            page=page,
            step_num=3,
            action_name=current_action,
            reason_str=str(e),
            exc=e,
            elapsed_seconds=time.time() - start_time,
        )

    # ── [4/7] Open Follow Up Form ──────────────────────────────────────────
    current_step = 4
    current_action = "Open Follow Up Form"
    try:
        follow_up_page.select_follow_up()
        qa_logger.log_step_pass(current_step, 7, current_action)
    except Exception as e:
        qa_logger.report_failure(
            page=page,
            step_num=4,
            action_name=current_action,
            reason_str=str(e),
            exc=e,
            elapsed_seconds=time.time() - start_time,
        )

    # ── [5/7] Fill Follow Up Form ──────────────────────────────────────────
    current_step = 5
    current_action = "Fill Follow Up Form"
    try:
        follow_up_page.fill_follow_up_form(
            date_val=follow_up_date,
            time_val=follow_up_time,
            channel_val=follow_up_channel,
            description_val=description,
        )
        qa_logger.log_step_pass(current_step, 7, current_action)
    except Exception as e:
        qa_logger.report_failure(
            page=page,
            step_num=5,
            action_name=current_action,
            reason_str=str(e),
            exc=e,
            elapsed_seconds=time.time() - start_time,
        )

    # ── [6/7] Save Follow Up ───────────────────────────────────────────────
    current_step = 6
    current_action = "Save Follow Up"
    try:
        follow_up_page.save_follow_up()
        qa_logger.log_step_pass(current_step, 7, current_action)
    except Exception as e:
        qa_logger.report_failure(
            page=page,
            step_num=6,
            action_name=current_action,
            reason_str=str(e),
            exc=e,
            elapsed_seconds=time.time() - start_time,
        )

    # ── [7/7] Validate Follow Up Record ─────────────────────────────────────
    current_step = 7
    current_action = "Validate Follow Up Record"
    try:
        expected_payload = {
            "date": follow_up_date,
            "time": follow_up_time,
            "channel": follow_up_channel,
            "description": description,
            "status": "Pending",
        }
        results_matrix = follow_up_page.validate_follow_up_record(expected_payload)

        headers_table = ["Field", "Expected", "Actual", "Status"]
        has_failure = any(r[3] == "FAIL" for r in results_matrix)

        if not has_failure:
            qa_logger.log_step_pass(current_step, 7, current_action)
            qa_logger.log_validation_table(headers_table, results_matrix)
        else:
            failed_rows = [r for r in results_matrix if r[3] == "FAIL"]
            qa_logger.log_validation_table(headers_table, failed_rows)
            qa_logger.report_failure(
                page=page,
                step_num=7,
                action_name=current_action,
                reason_str="Field value mismatch in table row",
                exc=AssertionError("Follow Up record field validation failed."),
                elapsed_seconds=time.time() - start_time,
            )

    except Exception as e:
        qa_logger.report_failure(
            page=page,
            step_num=7,
            action_name=current_action,
            reason_str=str(e),
            exc=e,
            elapsed_seconds=time.time() - start_time,
        )

    elapsed_time = time.time() - start_time
    qa_logger.print_test_summary(elapsed_time)
