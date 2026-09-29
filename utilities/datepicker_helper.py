import logging
import re
from datetime import datetime, date
from typing import Union, Optional, Tuple
from playwright.sync_api import Page, Locator

logger = logging.getLogger(__name__)

DateType = Union[str, date, datetime]


class DatePickerHelper:
    """
    Global Reusable Helper for React-DatePicker (`react-datepicker__month-container`).
    Supports selecting date ranges (From Date -> To Date) or single dates across all application pages.
    """

    MONTH_NAMES = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    @classmethod
    def parse_date(cls, input_date: DateType) -> Tuple[int, int, int]:
        """
        Parse input date into tuple of (year, month_1_indexed, day).
        Supports datetime/date objects and multiple date string formats:
          - YYYY-MM-DD (e.g., '2026-09-01')
          - DD/MM/YYYY (e.g., '01/09/2026')
          - MM/DD/YYYY (e.g., '09/01/2026')
          - YYYY/MM/DD (e.g., '2026/09/01')
        """
        if isinstance(input_date, (datetime, date)):
            return input_date.year, input_date.month, input_date.day

        str_date = str(input_date).strip()

        # Format YYYY-MM-DD or YYYY/MM/DD
        match_iso = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", str_date)
        if match_iso:
            y, m, d = int(match_iso.group(1)), int(match_iso.group(2)), int(match_iso.group(3))
            return y, m, d

        # Format DD/MM/YYYY or DD-MM-YYYY
        match_dmy = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", str_date)
        if match_dmy:
            d, m, y = int(match_dmy.group(1)), int(match_dmy.group(2)), int(match_dmy.group(3))
            # Handle potential MM/DD/YYYY if m > 12
            if m > 12:
                d, m = m, d
            return y, m, d

        raise ValueError(f"Unsupported date format: '{input_date}'. Use 'YYYY-MM-DD' or 'DD/MM/YYYY'.")

    @classmethod
    def select_date_range(
        cls,
        page: Page,
        input_element: Union[Locator, str],
        from_date: DateType,
        to_date: DateType,
        timeout_ms: int = 10000
    ) -> str:
        """
        Select a Date Range (From Date -> To Date) on any page using react-datepicker calendar popover.
        
        Steps:
          1. Click the date range input to display the calendar container.
          2. Set Year and Month for From Date, then click the From Date day cell.
          3. Set Year and Month for To Date, then click the To Date day cell.
          4. Returns the resulting text value of the input element.
        """
        if isinstance(input_element, str):
            input_loc = page.locator(input_element).first
        else:
            input_loc = input_element

        from_y, from_m, from_d = cls.parse_date(from_date)
        to_y, to_m, to_d = cls.parse_date(to_date)

        logger.info(
            "Selecting Date Range on UI: From (%04d-%02d-%02d) -> To (%04d-%02d-%02d)...",
            from_y, from_m, from_d, to_y, to_m, to_d
        )

        # Step 1: Open Datepicker Popover (Handle consecutive calls reliably)
        input_loc.scroll_into_view_if_needed()
        calendar_container = page.locator("div.react-datepicker__month-container, div.react-datepicker").first

        page.evaluate("if (document.activeElement) document.activeElement.blur()")
        page.wait_for_timeout(200)

        if not calendar_container.is_visible():
            input_loc.click()
            page.wait_for_timeout(300)

        if not calendar_container.is_visible():
            input_loc.click(force=True)
            page.wait_for_timeout(300)

        calendar_container.wait_for(state="visible", timeout=timeout_ms)

        # Step 2: Select From Date (Year, Month, Day)
        cls._select_year_and_month(page, from_y, from_m)
        cls._click_day(page, from_d)
        page.wait_for_timeout(300)

        # Step 3: Select To Date (Year, Month, Day)
        # Check if month/year selector is still open or needs updating
        cls._select_year_and_month(page, to_y, to_m)
        cls._click_day(page, to_d)
        page.wait_for_timeout(500)

        # Wait for calendar container to close or network to settle
        page.wait_for_load_state("networkidle")
        result_value = (input_loc.input_value() or input_loc.text_content() or "").strip()
        logger.info("Date Range selected successfully! Input value: '%s'", result_value)
        return result_value

    @classmethod
    def select_single_date(
        cls,
        page: Page,
        input_element: Union[Locator, str],
        target_date: DateType,
        timeout_ms: int = 10000
    ) -> str:
        """Select a single date on any page using react-datepicker calendar popover."""
        if isinstance(input_element, str):
            input_loc = page.locator(input_element).first
        else:
            input_loc = input_element

        y, m, d = cls.parse_date(target_date)
        logger.info("Selecting Single Date on UI: %04d-%02d-%02d...", y, m, d)

        input_loc.scroll_into_view_if_needed()
        input_loc.click()
        page.wait_for_timeout(300)

        calendar_container = page.locator("div.react-datepicker__month-container, div.react-datepicker").first
        calendar_container.wait_for(state="visible", timeout=timeout_ms)

        cls._select_year_and_month(page, y, m)
        cls._click_day(page, d)
        page.wait_for_timeout(500)

        page.wait_for_load_state("networkidle")
        result_value = (input_loc.input_value() or input_loc.text_content() or "").strip()
        logger.info("Single Date selected successfully! Input value: '%s'", result_value)
        return result_value

    @classmethod
    def _select_year_and_month(cls, page: Page, year: int, month_1_indexed: int):
        """Helper to set month and year dropdown selects in react-datepicker header."""
        year_select = page.locator("select.react-datepicker__year-select").first
        month_select = page.locator("select.react-datepicker__month-select").first

        if year_select.is_visible():
            year_select.select_option(value=str(year))

        if month_select.is_visible():
            # React-datepicker month dropdown value is 0-indexed (0=January, 11=December)
            month_value = str(month_1_indexed - 1)
            month_select.select_option(value=month_value)

    @classmethod
    def _click_day(cls, page: Page, day: int):
        """Helper to click a specific day cell in react-datepicker table body."""
        formatted_day = f"{day:03d}"  # e.g., '001', '015', '031'
        
        # Priority locator: day cell matching class 'react-datepicker__day--0XX' and not outside month or disabled
        day_cell = page.locator(
            f"div.react-datepicker__day--{formatted_day}:not(.react-datepicker__day--outside-month):not(.react-datepicker__day--disabled)"
        ).first

        if not day_cell.is_visible():
            # Fallback locator by text content exact match
            day_cell = page.locator(
                f"div.react-datepicker__day:not(.react-datepicker__day--outside-month):not(.react-datepicker__day--disabled)"
            ).filter(has_text=re.compile(rf"^{day}$")).first

        assert day_cell.is_visible(), f"Day cell '{day}' is not visible or disabled in react-datepicker!"
        day_cell.click()
