import logging
import pytest
from pages.source_wise_report_page import SourceWiseReportPage
from utilities.datepicker_helper import DatePickerHelper
from utilities.custom_logger import FormattedQALogger

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.login_as("Admin@infusive.com")
def test_global_datepicker_range_selection(logged_in_page):
    """
    Test Case:
    Validate Global DatePickerHelper react-datepicker range selection (From Date -> To Date).
    Verifies that selecting Start Date (e.g. 1st) and End Date (e.g. 29th) updates the input field range.
    """
    qa = FormattedQALogger()
    qa.print_header(
        test_case="Validate Global DatePickerHelper Range Selection (From -> To)",
        module="Global DatePicker Helper",
        browser="Chromium",
        env="STAGE"
    )

    report_page = SourceWiseReportPage(logged_in_page)
    report_page.navigate()

    total_steps = 3

    # Step 1: Select date range (01/09/2026 to 29/09/2026)
    qa.log_step(1, total_steps, "Selecting Date Range (2026-09-01 -> 2026-09-29) using DatePickerHelper...", "PASS")
    result_val = report_page.select_date_range("2026-09-01", "2026-09-29")
    qa.log_step(1, total_steps, f"Date Range Selected: '{result_val}'", "PASS")

    # Step 2: Validate formatted range input value
    qa.log_step(2, total_steps, "Validating formatted range in input field...", "PASS")
    assert "01/09/2026" in result_val and "29/09/2026" in result_val, (
        f"Unexpected datepicker input value format! Got '{result_val}'"
    )
    qa.log_step(2, total_steps, "Input field range format validated successfully!", "PASS")

    # Step 3: Test single date selection
    qa.log_step(3, total_steps, "Selecting Single Date (2026-09-15) using DatePickerHelper...", "PASS")
    single_val = DatePickerHelper.select_single_date(
        page=logged_in_page,
        input_element=report_page.date_range_input,
        target_date="2026-09-15"
    )
    qa.log_step(3, total_steps, f"Single Date Selected: '{single_val}'", "PASS")
    assert "15/09/2026" in single_val, f"Unexpected single date value! Got '{single_val}'"

    logger.info("==================================================================")
    logger.info("PASSED: Global DatePickerHelper Range & Single Date Selection 100% Successful!")
    logger.info("==================================================================")
