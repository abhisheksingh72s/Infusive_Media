import os
import pytest
import logging
from pages.dashboard_page import DashboardPage
from utilities.api.dashboard_api_client import DashboardApiClient
from utilities.api.dashboard_validator import DashboardValidator
from utilities.custom_logger import FormattedQALogger

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_full_dashboard_cards_charts_tables_api_validation(logged_in_page):
    """
    Comprehensive End-to-End Test Case:
    Validate ALL Summary Stat Cards, ALL Recharts Bar Charts (Monthly Trends & Lead Generation),
    and ALL Tables (Weekly Breakdown) from Backend APIs against live DOM rendering.
    """
    qa = FormattedQALogger()
    qa.print_header(
        test_case="Validate ALL Dashboard Cards, Charts, & Tables (API vs UI)",
        module="Admin Dashboard",
        browser="Chromium",
        env="STAGE"
    )

    api_client = DashboardApiClient(user="admin")
    dashboard_page = DashboardPage(logged_in_page)

    total_steps = 6

    # ---------------------------------------------------------------------------
    # Step 1: Fetch All Backend Dashboard APIs
    # ---------------------------------------------------------------------------
    qa.log_step(1, total_steps, "Fetching ALL Dashboard Backend API payloads...", "PASS")
    
    monthly_api_data = api_client.fetch_monthly_leads_data(year=2026)
    summary_api_data = api_client.fetch_dashboard_summary()
    lead_gen_api_data = api_client.fetch_lead_generation_dashboard(year=2026, month=9)
    today_activities_api = api_client.fetch_today_activities()

    qa.log_step(1, total_steps, "Successfully fetched data from 4 Dashboard Backend APIs!", "PASS")

    # ---------------------------------------------------------------------------
    # Step 2: Navigate to Dashboard UI & Extract DOM Data
    # ---------------------------------------------------------------------------
    qa.log_step(2, total_steps, "Navigating to live UI Dashboard & extracting DOM components...", "PASS")
    dashboard_page.go_to_dashboard()
    assert dashboard_page.is_chart_visible(), "Dashboard chart container is not visible on UI"

    ui_summary_cards = dashboard_page.get_all_summary_cards()
    ui_monthly_months = dashboard_page.get_x_axis_labels()
    
    dashboard_page.hover_bar_by_month("Sep")
    tooltip_text = dashboard_page.get_tooltip_text()

    ui_weekly_table = dashboard_page.get_weekly_breakdown_table()
    ui_lead_gen_users = dashboard_page.get_lead_gen_user_ticks()
    ui_activities_status = dashboard_page.get_todays_activities_status()

    qa.log_step(2, total_steps, f"Extracted {len(ui_summary_cards)} Summary Cards & {len(ui_weekly_table.get('rows', []))} Table Rows from DOM", "PASS")

    # ---------------------------------------------------------------------------
    # Step 3: Validate ALL 7 Summary Cards (Hard Assertion)
    # ---------------------------------------------------------------------------
    qa.log_step(3, total_steps, "Validating ALL 7 Summary Cards (API vs DOM)...", "PASS")
    DashboardValidator.validate_summary_metrics(
        api_summary=summary_api_data,
        ui_summary=ui_summary_cards
    )
    qa.log_step(3, total_steps, "ALL Summary Cards validated with HARD ASSERTIONS! PASS", "PASS")

    # ---------------------------------------------------------------------------
    # Step 4: Validate Monthly Lead Trends Chart (Hard Assertion)
    # ---------------------------------------------------------------------------
    qa.log_step(4, total_steps, "Validating Monthly Lead Trends Chart 1 (API vs DOM)...", "PASS")
    DashboardValidator.validate_monthly_leads_matrix(
        api_monthly_data=monthly_api_data,
        ui_x_labels=ui_monthly_months,
        active_tooltip=tooltip_text
    )
    qa.log_step(4, total_steps, "Monthly Lead Trends Chart validated with HARD ASSERTIONS! PASS", "PASS")

    # ---------------------------------------------------------------------------
    # Step 5: Validate Weekly Breakdown Table (Hard Assertion)
    # ---------------------------------------------------------------------------
    qa.log_step(5, total_steps, "Validating Weekly Breakdown Table 1 (API vs DOM)...", "PASS")
    DashboardValidator.validate_weekly_breakdown_table(
        api_lead_gen_data=lead_gen_api_data,
        ui_table_data=ui_weekly_table
    )
    qa.log_step(5, total_steps, "Weekly Breakdown Table validated with HARD ASSERTIONS! PASS", "PASS")

    # ---------------------------------------------------------------------------
    # Step 6: Validate Today's Activities Status (Hard Assertion)
    # ---------------------------------------------------------------------------
    qa.log_step(6, total_steps, "Validating Today's Activities & Meetings Cards (API vs DOM)...", "PASS")
    DashboardValidator.validate_today_activities(
        api_today_activities=today_activities_api,
        ui_activities_status=ui_activities_status
    )
    qa.log_step(6, total_steps, "ALL Dashboard Cards, Charts, & Tables validated successfully! PASS", "PASS")
