import os
import time
import logging
import pytest
from playwright.sync_api import Page, expect

from pages.login_page import LoginPage
from pages.project_page import ProjectPage
from utilities.custom_logger import FormattedQALogger

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_phase_4_project_setup_execution(page: Page):
    """
    Phase 4: Project Setup Execution Test:
      1. Login as Admin
      2. Navigate to Projects (/projects)
      3. Open Project Details
      4. Phase 4.1: Project Details (Negative validations + Happy path Save)
      5. Phase 4.2: Resource Allocation (Negative checks + Dynamic Allocation + Save)
      6. Phase 4.3: Task Management (Negative checks + Dynamic Task Create + Save & Persistence)
    """
    start_time = time.time()
    log_file_path = "logs/phase4_project_setup.log"
    qa_logger = FormattedQALogger(log_file=log_file_path)
    qa_logger.print_header("Phase 4 Project Setup Execution", module="Projects", env="STG")

    login_page = LoginPage(page)
    project_page = ProjectPage(page)

    # Step 1: Login as Admin
    admin_email = os.getenv("EMAIL", "Admin@infusive.com")
    admin_pass = os.getenv("PASSWORD", "123456")
    qa_logger.log_step(1, 4, "Login as Admin Role", status="IN_PROGRESS")
    login_page.load()
    login_page.login(admin_email, admin_pass)
    login_page.wait_for_dashboard()
    qa_logger.log_step(1, 4, "Login as Admin Role", status="PASS", details={"Email": admin_email})

    # Step 2: Navigate to Projects & Select Target Project
    qa_logger.log_step(2, 4, "Navigate to Projects Module", status="IN_PROGRESS")
    project_page.go_to_project()

    # Capture first project name from table
    page.locator("tbody tr").first.wait_for(state="visible", timeout=15000)
    first_row = page.locator("tbody tr").first
    proj_name = first_row.locator("td:nth-child(2)").inner_text().strip()
    qa_logger.log_step(2, 4, "Navigate to Projects Module", status="PASS", details={"Selected Project": proj_name})

    # Step 3: Open Project & Complete Project Details (Phase 4.1)
    qa_logger.log_step(3, 4, "Phase 4.1: Project Details Validations & Save", status="IN_PROGRESS")
    project_page.click_project_hyperlink(proj_name)
    project_page.click_edit_project_icon()
    neg_res = project_page.verify_and_trigger_field_validations(qa_logger=qa_logger)
    project_page.fill_project_details(budget="50000", duration="6", start_date="2026-11-01")
    project_page.save_project()
    qa_logger.log_step(
        3,
        4,
        "Phase 4.1: Project Details Validations & Save",
        status="PASS",
        details={
            "Validations Captured": str(neg_res.get("validations_captured", False)),
            "Budget": "50000",
            "Duration": "6 Months",
        },
    )

    # Step 4: Complete Resource Allocation & Task Management (Phase 4.2 & 4.3)
    qa_logger.log_step(4, 4, "Phase 4.2 & 4.3: Resource Allocation & Task Creation", status="IN_PROGRESS")
    # Resource Allocation
    project_page.open_resource_allocation_tab()
    project_page.verify_resource_allocation_negative_validations(qa_logger=qa_logger)
    alloc_data = project_page.allocate_resource_dynamic(start_date="2026-11-01")
    project_page.verify_resource_allocated()

    # Task Management
    project_page.open_task_management_tab()
    project_page.click_add_task()
    project_page.verify_add_task_negative_validations(qa_logger=qa_logger)
    task_title = f"Phase4_LiveTask_{int(time.time())}"
    project_page.create_task_dynamic(task_name=task_title)
    task_persisted = project_page.verify_task_exists(task_title)

    qa_logger.log_step(
        4,
        4,
        "Phase 4.2 & 4.3: Resource Allocation & Task Creation",
        status="PASS",
        details={
            "Employee Allocated": alloc_data.get("employee", "Dynamic"),
            "Task Created": task_title,
            "Task Persisted": str(task_persisted),
        },
    )

    duration = time.time() - start_time
    qa_logger.print_footer(status="PASSED", total_steps=4, passed=4, failed=0, duration_sec=duration)
    logger.info("PHASE 4 COMPLETE SETUP VERIFIED SUCCESSFULLY ✓")
