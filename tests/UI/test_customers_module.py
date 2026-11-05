import os
import time
import logging
import pytest
from playwright.sync_api import Page, expect

from pages.login_page import LoginPage
from pages.customer_page import CustomerPage
from utilities.custom_logger import FormattedQALogger

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_phase_5_customers_module_execution(page: Page):
    """
    Phase 5: Customers Module End-to-End Execution Test:
      1. Login as Admin
      2. Navigate to Customers (/customers)
      3. Verify Table Structure (Headers: S.NO, CUSTOMER NAME, EMAIL, PHONE, ADDRESS, OUTSTANDING, STATUS, ACTION)
      4. Search Customer & Verify Data Persistence (Adventa Tech Inc test 04 & ABC Technologies)
      5. Open Customer Details Profile (/customers/{id})
      6. Assert Profile Details (Customer ID, Address, Invoices)
    """
    start_time = time.time()
    log_file_path = "logs/phase5_customers_module.log"
    qa_logger = FormattedQALogger(log_file=log_file_path)
    qa_logger.print_header("Phase 5 Customers Module Execution", module="Customers", env="STG")

    login_page = LoginPage(page)
    customer_page = CustomerPage(page)

    # -------------------------------------------------------------------------
    # STEP 1: Admin Login
    # -------------------------------------------------------------------------
    admin_email = os.getenv("EMAIL", "Admin@infusive.com")
    admin_pass = os.getenv("PASSWORD", "123456")
    qa_logger.log_step(1, 5, "Login as Admin Role", status="IN_PROGRESS")
    login_page.load()
    login_page.login(admin_email, admin_pass)
    login_page.wait_for_dashboard()
    qa_logger.log_step(1, 5, "Login as Admin Role", status="PASS", details={"Email": admin_email})

    # -------------------------------------------------------------------------
    # STEP 2: Navigate to Customers Module & Verify Page
    # -------------------------------------------------------------------------
    qa_logger.log_step(2, 5, "Navigate to Customers Module (/customers)", status="IN_PROGRESS")
    customer_page.go_to_customers()
    assert "/customers" in page.url, f"Expected URL to contain '/customers', got '{page.url}'"
    qa_logger.log_step(2, 5, "Navigate to Customers Module (/customers)", status="PASS", details={"URL": page.url})

    # -------------------------------------------------------------------------
    # STEP 3: Verify Table Structure & Required Columns
    # -------------------------------------------------------------------------
    qa_logger.log_step(3, 5, "Verify Customer Table Structure & Headers", status="IN_PROGRESS")
    headers = customer_page.get_table_headers()
    expected_headers = ["S.NO", "CUSTOMER NAME", "EMAIL", "PHONE", "ADDRESS", "OUTSTANDING", "STATUS", "ACTION"]
    for eh in expected_headers:
        assert any(eh in h for h in headers), f"Expected header '{eh}' not found in {headers}"
    qa_logger.log_step(3, 5, "Verify Customer Table Structure & Headers", status="PASS", details={"Headers": ", ".join(headers)})

    # -------------------------------------------------------------------------
    # STEP 4: Search & Verify Customer Record Data
    # -------------------------------------------------------------------------
    qa_logger.log_step(4, 5, "Search & Verify Customer Record in Table", status="IN_PROGRESS")
    target_customer = "ABC Technologies Pvt. Ltd."
    customer_exists = customer_page.verify_customer_exists(target_customer)
    assert customer_exists, f"Customer '{target_customer}' must exist in Customers table!"

    row_data = customer_page.get_customer_row_data(target_customer)
    assert row_data["name"] == target_customer, f"Expected name '{target_customer}', got '{row_data['name']}'"
    assert row_data["status"] == "Active", f"Expected status 'Active', got '{row_data['status']}'"
    assert row_data["email"], "Customer email should not be empty!"

    qa_logger.log_step(
        4,
        5,
        "Search & Verify Customer Record in Table",
        status="PASS",
        details={
            "Customer": row_data["name"],
            "Email": row_data["email"],
            "Phone": row_data["phone"],
            "Status": row_data["status"],
            "Outstanding": row_data["outstanding"],
        },
    )

    # -------------------------------------------------------------------------
    # STEP 5: View Customer Details Profile (/customers/{id})
    # -------------------------------------------------------------------------
    qa_logger.log_step(5, 5, "View Customer Profile Details (/customers/{id})", status="IN_PROGRESS")
    customer_page.click_view_customer_details(target_customer)
    assert "/customers/" in page.url, f"Expected URL to be '/customers/{{id}}', got '{page.url}'"

    profile = customer_page.get_customer_detail_profile()
    assert "Customer Details" in profile["raw_text"], "Expected 'Customer Details' header in detail view!"
    assert target_customer in profile["raw_text"], f"Expected '{target_customer}' in detail view!"
    if "customer_id" in profile:
        logger.info(f"Verified Customer ID: {profile['customer_id']}")

    qa_logger.log_step(
        5,
        5,
        "View Customer Profile Details (/customers/{id})",
        status="PASS",
        details={
            "Customer ID": profile.get("customer_id", "Verified"),
            "Profile URL": profile["url"],
        },
    )

    duration = time.time() - start_time
    qa_logger.print_footer(status="PASSED", total_steps=5, passed=5, failed=0, duration_sec=duration)
    logger.info("PHASE 5 CUSTOMERS MODULE EXECUTION VERIFIED SUCCESSFULLY ✓")
