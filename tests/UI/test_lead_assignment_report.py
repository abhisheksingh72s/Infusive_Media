import logging
import pytest
from pages.lead_assignment_report_page import LeadAssignmentReportPage
from utilities.api.lead_assignment_report_api_client import LeadAssignmentReportApiClient
from utilities.api.lead_assignment_validator import LeadAssignmentValidator
from utilities.custom_logger import FormattedQALogger

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.login_as("Admin@infusive.com")
def test_lead_assignment_report_dom_vs_api_validation(logged_in_page):
    """
    End-to-End Test Case:
    Validate Lead Assignment Report UI components, headers, user matrix, and grand totals
    against live Backend APIs using STRICT HARD ASSERTIONS.
    """
    qa = FormattedQALogger()
    qa.print_header(
        test_case="Validate Lead Assignment Report (API vs UI)",
        module="Lead Assignment Report",
        browser="Chromium",
        env="STAGE"
    )

    api_client = LeadAssignmentReportApiClient(user="admin")
    report_page = LeadAssignmentReportPage(logged_in_page)

    total_steps = 5

    # ---------------------------------------------------------------------------
    # Step 1: Fetch Backend API Data
    # ---------------------------------------------------------------------------
    qa.log_step(1, total_steps, "Fetching 'Assign To' Users and Full Cell-by-Cell Matrix from API...", "PASS")
    expected_users = api_client.get_expected_assign_to_users()
    api_matrix = api_client.fetch_user_wise_lead_report()
    qa.log_step(1, total_steps, f"Retrieved {len(expected_users)} expected users and full API matrix ({len(api_matrix)} rows)!", "PASS")

    # ---------------------------------------------------------------------------
    # Step 2: Navigate to Lead Assignment Report UI & Extract DOM Data
    # ---------------------------------------------------------------------------
    qa.log_step(2, total_steps, "Navigating to /lead-report UI & extracting table data...", "PASS")
    report_page.navigate()
    assert report_page.heading.is_visible(), "Lead Assignment Report heading is not visible on UI!"
    assert report_page.table.is_visible(), "Table container is not visible on UI!"

    dom_headers = report_page.get_table_headers()
    dom_rows = report_page.extract_table_to_json()
    dom_grand_total = report_page.extract_grand_total_json()
    qa.log_step(2, total_steps, f"Extracted {len(dom_headers)} headers and {len(dom_rows)} rows from DOM.", "PASS")

    # ---------------------------------------------------------------------------
    # Step 3: Strict Validation of Table Headers
    # ---------------------------------------------------------------------------
    qa.log_step(3, total_steps, "Validating 15 Table Column Headers (Expected vs DOM)...", "PASS")
    LeadAssignmentValidator.validate_headers(dom_headers)
    qa.log_step(3, total_steps, "All 15 Table Headers validated successfully with Hard Assertions!", "PASS")
 
    # ---------------------------------------------------------------------------
    # Step 4: Strict 130 Cell-by-Cell Hard Assertions (10 Users x 13 Metrics)
    # ---------------------------------------------------------------------------
    qa.log_step(4, total_steps, "Validating User Rows and 130 Cells (10 Users x 13 Metrics) API vs DOM...", "PASS")
    LeadAssignmentValidator.validate_users_list(dom_rows, expected_users)
    LeadAssignmentValidator.validate_cell_by_cell_api_vs_dom(dom_rows, api_matrix)
    qa.log_step(4, total_steps, "ALL 130 Individual Cells strictly matched API with HARD ASSERTIONS!", "PASS")

    # ---------------------------------------------------------------------------
    # Step 5: Strict Validation of Grand Total Row Aggregations
    # ---------------------------------------------------------------------------
    qa.log_step(5, total_steps, "Validating Grand Total Row Column Aggregations (13 Metrics)...", "PASS")
    LeadAssignmentValidator.validate_grand_totals(dom_rows, dom_grand_total)
    qa.log_step(5, total_steps, "Grand Total Row strictly validated against sum of rows!", "PASS")

    logger.info("==================================================================")
    logger.info("PASSED: Lead Assignment Report DOM vs API Validation 100% Successful!")
    logger.info("==================================================================")
