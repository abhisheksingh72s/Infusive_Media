import logging
import pytest
from pages.lead_creation_report_page import LeadCreationReportPage
from utilities.api.report_api_client import ReportApiClient
from utilities.api.report_validator import LeadReportValidator
from utilities.table_json_parser import TableJsonParser, EXPECTED_HEADERS

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.login_as("TeamLead1@mailinator.com")
class TestLeadCreationReport:
    """UI Test Suite for Lead Creation Report DOM vs API Validation."""

    def test_lead_creation_report_dom_vs_api_validation(self, logged_in_page, playwright):
        """
        Scenario:
        1. Login as TeamLead1 user.
        2. Navigate to Report -> Creation Report.
        3. Capture API JSON response via Playwright APIRequestContext.
        4. Extract report table directly from DOM.
        5. Convert DOM table data into JSON.
        6. Compare API JSON with DOM JSON dynamically using required block logging format.
        """
        logger.info("==================================================================")
        logger.info("Starting Test: Lead Creation Report DOM vs API Validation")
        logger.info("==================================================================")

        # 1. Capture API response
        api_context = playwright.request.new_context()
        api_client = ReportApiClient(api_context=api_context)

        logger.info("Step 1: Capturing PresalesReportFilter API response...")
        api_records = api_client.get_normalized_api_records(user="admin")
        assert len(api_records) > 0, "Captured API response is empty!"
        logger.info("Captured %d API records successfully", len(api_records))

        # 2. Extract DOM data
        logger.info("Step 2: Navigating to Lead Creation Report page on UI...")
        report_page = LeadCreationReportPage(logged_in_page)
        report_page.navigate()

        logger.info("Step 3: Validating Column Headers from DOM...")
        dom_headers = report_page.get_table_headers()
        assert len(dom_headers) > 0, "No table headers found on DOM!"
        TableJsonParser.validate_headers(dom_headers, EXPECTED_HEADERS)

        logger.info("Step 4: Extracting DOM table rows into JSON structure...")
        dom_user_rows = report_page.extract_table_to_json()
        dom_grand_total = report_page.extract_grand_total_json()

        assert len(dom_user_rows) > 0, "No rows extracted from DOM table body!"
        logger.info("Extracted %d user rows from DOM", len(dom_user_rows))

        # 3. Dynamic API vs DOM Comparison
        logger.info("Step 5: Comparing API JSON vs DOM JSON dynamically...")
        is_success, mismatches = LeadReportValidator.validate_api_vs_dom(
            dom_user_rows=dom_user_rows,
            dom_grand_total=dom_grand_total,
            api_records=api_records
        )

        api_context.dispose()

        # 4. Strict Assertions
        assert is_success, (
            f"API vs DOM Validation failed with {len(mismatches)} mismatch(es):\n"
            + "\n".join(f" - {err}" for err in mismatches)
        )

        logger.info("==================================================================")
        logger.info("PASSED: Lead Creation Report DOM vs API Validation Successful!")
        logger.info("==================================================================")
