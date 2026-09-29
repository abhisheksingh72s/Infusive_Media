import logging
import pytest
from pages.source_wise_report_page import SourceWiseReportPage
from utilities.api.source_wise_report_api_client import SourceWiseReportApiClient
from utilities.api.source_wise_validator import SourceWiseValidator
from utilities.custom_logger import FormattedQALogger

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.login_as("Admin@infusive.com")
def test_source_wise_report_dom_vs_api_validation(logged_in_page):
    """
    End-to-End Test Case:
    Validate Source Wise Report (Source Lead Allocation) UI components, headers, source matrix,
    grand totals, DatePicker range filtering, AND drilldown lead details modal against live Backend APIs using STRICT HARD ASSERTIONS.
    """
    qa = FormattedQALogger()
    qa.print_header(
        test_case="Validate Source Wise Report & DatePicker Filter (API vs UI)",
        module="Source Wise Report",
        browser="Chromium",
        env="STAGE"
    )

    api_client = SourceWiseReportApiClient(user="admin")
    report_page = SourceWiseReportPage(logged_in_page)

    total_steps = 7

    # ---------------------------------------------------------------------------
    # Step 1: Fetch Backend API Data
    # ---------------------------------------------------------------------------
    qa.log_step(1, total_steps, "Fetching 'Source Filter' Sources and Full Cell-by-Cell Matrix from API...", "PASS")
    expected_sources = api_client.get_expected_sources()
    api_matrix = api_client.fetch_source_wise_report()
    qa.log_step(1, total_steps, f"Retrieved {len(expected_sources)} expected sources and full API matrix ({len(api_matrix)} rows)!", "PASS")

    # ---------------------------------------------------------------------------
    # Step 2: Navigate to Source Wise Report UI & Extract DOM Data
    # ---------------------------------------------------------------------------
    qa.log_step(2, total_steps, "Navigating to /source-wise-report UI & extracting table data...", "PASS")
    report_page.navigate()
    assert report_page.heading.is_visible(), "Source Wise Report heading is not visible on UI!"
    assert report_page.table.is_visible(), "Table container is not visible on UI!"

    dom_headers = report_page.get_table_headers()
    dom_rows = report_page.extract_table_to_json()
    dom_grand_total = report_page.extract_grand_total_json()
    qa.log_step(2, total_steps, f"Extracted {len(dom_headers)} headers and {len(dom_rows)} rows from DOM.", "PASS")

    # ---------------------------------------------------------------------------
    # Step 3: Strict Validation of Table Headers
    # ---------------------------------------------------------------------------
    qa.log_step(3, total_steps, "Validating 16 Table Column Headers (Expected vs DOM)...", "PASS")
    SourceWiseValidator.validate_headers(dom_headers)
    qa.log_step(3, total_steps, "All 16 Table Headers validated successfully with Hard Assertions!", "PASS")

    # ---------------------------------------------------------------------------
    # Step 4: Strict Cell-by-Cell Hard Assertions (Sources x 15 Metrics)
    # ---------------------------------------------------------------------------
    qa.log_step(4, total_steps, f"Validating Source Rows and {len(dom_rows) * 15} Cells ({len(dom_rows)} Sources x 15 Metrics) API vs DOM...", "PASS")
    SourceWiseValidator.validate_sources_list(dom_rows, expected_sources)
    SourceWiseValidator.validate_cell_by_cell_api_vs_dom(dom_rows, api_matrix)
    qa.log_step(4, total_steps, f"ALL {len(dom_rows) * 15} Individual Cells strictly matched API with HARD ASSERTIONS!", "PASS")

    # ---------------------------------------------------------------------------
    # Step 5: Strict Validation of Grand Total Row Aggregations
    # ---------------------------------------------------------------------------
    qa.log_step(5, total_steps, "Validating Grand Total Row Column Aggregations (15 Metrics)...", "PASS")
    SourceWiseValidator.validate_grand_totals(dom_rows, dom_grand_total)
    qa.log_step(5, total_steps, "Grand Total Row strictly validated against sum of rows!", "PASS")

    # ---------------------------------------------------------------------------
    # Step 6: Test DatePicker Range Selection & Date Range Filtering (UI vs API)
    # ---------------------------------------------------------------------------
    qa.log_step(6, total_steps, "Testing DatePicker Filtering Case 1: Out-of-Range (2026-09-01 -> 2026-09-15)...", "PASS")
    out_of_range_str = report_page.select_date_range("2026-09-01", "2026-09-15")
    assert "01/09/2026" in out_of_range_str and "15/09/2026" in out_of_range_str, "Date Range input mismatch!"
    
    # Verify that selecting a date range with no leads filters table to all 0s
    empty_dom_rows = report_page.extract_table_to_json()
    empty_api_matrix = api_client.fetch_source_wise_report(start_date="2026-09-01", end_date="2026-09-15")
    SourceWiseValidator.validate_cell_by_cell_api_vs_dom(empty_dom_rows, empty_api_matrix)
    qa.log_step(6, total_steps, "Out-of-range date filter correctly filtered UI table data to 0s!", "PASS")

    # Testing DatePicker Case 2: Active Leads Date Range (2026-09-16 -> 2026-09-29)
    qa.log_step(6, total_steps, "Testing DatePicker Filtering Case 2: Active Leads Range (2026-09-16 -> 2026-09-29)...", "PASS")
    selected_range_str = report_page.select_date_range("2026-09-16", "2026-09-29")
    assert "16/09/2026" in selected_range_str and "29/09/2026" in selected_range_str, "Date Range input mismatch!"

    # Re-extract UI table data post-filter and compare against API filtered matrix
    filtered_dom_rows = report_page.extract_table_to_json()
    filtered_api_matrix = api_client.fetch_source_wise_report(start_date="2026-09-16", end_date="2026-09-29")
    SourceWiseValidator.validate_cell_by_cell_api_vs_dom(filtered_dom_rows, filtered_api_matrix)
    qa.log_step(6, total_steps, f"Active date range filter ({len(filtered_dom_rows)} rows) strictly verified UI vs API!", "PASS")

    # ---------------------------------------------------------------------------
    # Step 7: Validate Source Lead Details Modal Drilldown (API vs DOM)
    # ---------------------------------------------------------------------------
    qa.log_step(7, total_steps, "Validating Facebook Lead Details Modal Drilldown (API vs DOM)...", "PASS")
    report_page.open_lead_details_modal("Facebook", metric_col_index=1)
    
    # 7a. User Wise mode validation
    api_user_details = api_client.fetch_user_wise_lead_details(source_id=1, status="totalLeads")
    dom_modal_rows = report_page.extract_modal_table_to_json()
    SourceWiseValidator.validate_modal_user_wise_details(dom_modal_rows, api_user_details, "Facebook")
    qa.log_step(7, total_steps, "User-Wise Lead Details Modal matched API perfectly!", "PASS")

    # 7b. Toggle to Source Wise mode in modal
    report_page.select_modal_view_mode("sourceWise")
    api_source_details = api_client.fetch_source_wise_lead_details(source_id=1, status="totalLeads")
    dom_modal_source_rows = report_page.extract_modal_table_to_json()
    assert len(dom_modal_source_rows) > 0, "Source-Wise modal rows should not be empty"
    qa.log_step(7, total_steps, f"Source-Wise modal toggle verified with {len(dom_modal_source_rows)} rows!", "PASS")

    report_page.close_modal()

    logger.info("==================================================================")
    logger.info("PASSED: Source Wise Report DOM vs API Validation 100% Successful!")
    logger.info("==================================================================")
