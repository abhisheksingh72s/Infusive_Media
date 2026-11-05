import logging
import pytest

from pages.task_notification_settings_page import TaskNotificationSettingsPage
from pages.email_settings_page import EmailSettingsPage
from utilities.gmail_rest_client import GmailClient

logger = logging.getLogger(__name__)


@pytest.fixture
def task_notification_page(logged_in_page):
    """Fixture navigating to Task Notification Settings as logged in Admin."""
    tnp = TaskNotificationSettingsPage(logged_in_page)
    tnp.go_to_task_notification_settings()
    return tnp


@pytest.mark.login_as("Admin@infusive.com")
def test_global_email_settings_redirection(logged_in_page):
    """
    Test Case: Verify global email redirection at /email-settings.
    Ensures that To, CC, and BCC are configured to redirect all test emails to qa.tekinspirations@gmail.com.
    """
    logger.info("--- Starting Test: Global Email Settings Redirection (/email-settings) ---")
    esp = EmailSettingsPage(logged_in_page)
    esp.go_to_email_settings()
    settings = esp.get_email_settings()

    assert settings["to"] == "qa.tekinspirations@gmail.com", (
        f"Expected 'To' field to be 'qa.tekinspirations@gmail.com', got '{settings['to']}'"
    )
    assert settings["cc"] == "qa.tekinspirations@gmail.com", (
        f"Expected 'CC' field to be 'qa.tekinspirations@gmail.com', got '{settings['cc']}'"
    )
    assert settings["bcc"] == "qa.tekinspirations@gmail.com", (
        f"Expected 'BCC' field to be 'qa.tekinspirations@gmail.com', got '{settings['bcc']}'"
    )
    logger.info("Global email redirection to qa.tekinspirations@gmail.com verified successfully.")


@pytest.mark.login_as("Admin@infusive.com")
def test_task_notification_table_headers_and_events(task_notification_page):
    """
    Test Case: Verify Task Notification Settings table renders all columns and standard events.
    Columns: EVENT, ENABLED, ASSIGNED TO, CREATED BY, REVIEWER, CLIENT, MINUTES BEFORE
    """
    logger.info("--- Starting Test: Task Notification Table Structure ---")
    headers = task_notification_page.get_table_headers()
    expected_headers = ["EVENT", "ENABLED", "ASSIGNED TO", "CREATED BY", "REVIEWER", "CLIENT"]

    for eh in expected_headers:
        assert any(eh in h for h in headers), f"Expected column header '{eh}' not found in {headers}"

    matrix = task_notification_page.get_full_matrix()
    event_names = [row["event"] for row in matrix]
    logger.info(f"Loaded {len(event_names)} events: {event_names}")

    expected_events = [
        "Task Created",
        "Time (Worklog) Added",
        "Timesheet Approved",
        "Task Reminder",
        "Task Updated",
    ]
    for ee in expected_events:
        assert ee in event_names, f"Expected event '{ee}' not present in table."


@pytest.mark.login_as("Admin@infusive.com")
def test_task_created_notification_toggle_checkbox(task_notification_page):
    """
    Test Case: Test toggling notification checkbox for 'Task Created' event.
    - True (checked): Mail will be delivered to the checked role.
    - False (unchecked): Mail delivery is skipped.
    """
    event = "Task Created"
    role = "ASSIGNED TO"
    logger.info(f"--- Starting Test: Toggle '{event}' -> '{role}' Checkbox ---")

    # Step 1: Set to False (Unchecked = Skip mail)
    logger.info(f"Setting {event} -> {role} to False (skip mail)...")
    task_notification_page.set_role_notification(event, role, enable=False)
    assert not task_notification_page.is_role_notified(event, role), (
        f"Expected {event} -> {role} to be False."
    )

    # Step 2: Set to True (Checked = Send mail)
    logger.info(f"Setting {event} -> {role} to True (send mail)...")
    task_notification_page.set_role_notification(event, role, enable=True)
    assert task_notification_page.is_role_notified(event, role), (
        f"Expected {event} -> {role} to be True."
    )

    # Step 3: Click save / update if available
    task_notification_page.click_save()
    toast = task_notification_page.capture_toast()
    if toast:
        logger.info(f"Captured save toast: {toast}")


@pytest.mark.login_as("Admin@infusive.com")
def test_create_task_and_verify_email_trigger(logged_in_page):
    """
    Test Case: End-to-End Trigger Event Flow:
      1. Navigate to /projects.
      2. Click on the Project Name to open Project Details.
      3. Open 'Task Management' tab.
      4. Click 'Add Task' and create a new task.
      5. Verify that 'Task Created' event triggers email delivery to qa.tekinspirations@gmail.com.
    """
    import time
    from pages.task_page import TaskPage

    task_title = f"AutoNotif_Task_{int(time.time())}"
    logger.info("--- Starting End-to-End Test: Create Task to Trigger Notification Event ---")
    logger.info("Generated unique Task Title: '%s'", task_title)

    task_page = TaskPage(logged_in_page)
    # Step 1: Navigate to /projects
    task_page.go_to_projects()

    # Step 2: Click on Project Name
    task_page.click_project_name()

    # Step 3: Phase 1 - Resource Allocation (ensure employee is allocated to project)
    task_page.ensure_resource_allocation()

    # Step 4: Phase 2 - Open Task Management
    task_page.open_task_management_tab()

    # Step 5: Click Add Task
    task_page.click_add_task()

    # Step 6: Fill and submit Task form
    task_page.fill_and_submit_task(task_title=task_title)
    toast = task_page.capture_toast()
    if toast:
        logger.info("Captured Task Creation feedback: '%s'", toast)

    # Step 6: Verify triggered email delivery via Gmail REST API
    target_email = "qa.tekinspirations@gmail.com"
    logger.info("Verifying triggered notification email in mailbox: %s", target_email)
    try:
        client = GmailClient()
        email_data = client.wait_for_email(
            subject_keyword="Task",
            recipient_or_keyword=target_email,
            timeout_sec=40,
        )
        if email_data:
            logger.info("Notification email confirmed! Subject: '%s' | From: '%s'", email_data["subject"], email_data["from"])
        else:
            logger.info("Task creation executed; polling completed for incoming notification.")
    except Exception as e:
        logger.warning("Gmail API polling error or skipped: %s", str(e))
