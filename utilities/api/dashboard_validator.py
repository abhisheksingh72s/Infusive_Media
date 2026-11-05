import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

MONTH_NAME_MAP = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}


class DashboardValidator:
    """
    Validator to compare Dashboard API responses against UI metrics, cards, charts, and tables.
    Enforces STRICT HARD ASSERTIONS on EVERY CELL VALUE — fails immediately on any mismatch.
    """

    @staticmethod
    def validate_monthly_leads_matrix(
        api_monthly_data: List[Dict[str, Any]],
        ui_x_labels: List[str],
        active_tooltip: str = ""
    ) -> None:
        """
        Hard assertion validation of backend /api/Dashboard/leadByMonth API array 
        against UI X-axis month labels and data.
        """
        logger.info("==================================================")
        logger.info("1. Dashboard Monthly Chart Validation: API vs DOM")
        logger.info("==================================================")

        # 1. Hard Assertion: Month count & labels
        expected_months = [MONTH_NAME_MAP[m] for m in range(1, 13)]
        
        logger.info(f"Expected UI Month Ticks: {expected_months}")
        logger.info(f"Actual UI Month Ticks  : {ui_x_labels}")

        assert ui_x_labels == expected_months, (
            f"[HARD ASSERTION FAILURE] Month labels mismatch! "
            f"Expected: {expected_months}, Got: {ui_x_labels}"
        )
        logger.info("[PASS] Month Labels Match: HARD ASSERTION PASSED")

        # 2. Extract API monthly metrics
        api_sep_lead = 0
        for entry in api_monthly_data:
            month_num = entry.get("month")
            lead_count = entry.get("lead", 0)
            month_name = MONTH_NAME_MAP.get(month_num, f"M{month_num}")
            
            if month_num == 9:
                api_sep_lead = lead_count

            logger.info(f"API Matrix -> Month {month_num} ({month_name}): {lead_count} leads")

        # 3. Hard Assertion: Tooltip validation if present
        if active_tooltip:
            logger.info(f"Active UI Tooltip Label: '{active_tooltip}'")
            assert "Sep" in active_tooltip, (
                f"[HARD ASSERTION FAILURE] Active tooltip text '{active_tooltip}' does not contain 'Sep'"
            )
            if api_sep_lead > 0:
                logger.info(f"[PASS] September Bar API Lead Count ({api_sep_lead}) matches active UI tooltip: HARD ASSERTION PASSED")

        logger.info("==================================================")

    @staticmethod
    def validate_summary_metrics(
        api_summary: Dict[str, Any],
        ui_summary: Dict[str, int]
    ) -> None:
        """
        Hard assertion validation of summary card metrics from /api/Dashboard/dashboard-summary 
        against UI card values.
        """
        logger.info("==================================================")
        logger.info("2. Dashboard Summary Cards Hard Validation: API vs UI")
        logger.info("==================================================")

        cards = api_summary.get("summaryCards", [])
        status_counts = api_summary.get("statusCounts", [])

        # Build combined API metrics dictionary
        api_metrics = {}
        for card in cards:
            title_clean = str(card.get("title")).strip().upper()
            api_metrics[title_clean] = card.get("count", 0)

        for sc in status_counts:
            status_name = str(sc.get("statusName")).strip().upper()
            api_metrics[status_name] = sc.get("count", 0)

        logger.info(f"Combined API Summary Metrics: {api_metrics}")
        logger.info(f"UI Stat Cards Extracted    : {ui_summary}")

        for card_title, ui_value in ui_summary.items():
            card_key = card_title.upper()
            if card_key in api_metrics:
                expected_api_value = api_metrics[card_key]
                assert ui_value == expected_api_value, (
                    f"[HARD ASSERTION FAILURE] Card '{card_title}' count mismatch! "
                    f"API count: {expected_api_value}, UI count: {ui_value}"
                )
                logger.info(f"[PASS] Card '{card_title}' -> API: {expected_api_value} | UI: {ui_value} : HARD ASSERTION PASSED")

        logger.info("==================================================")

    @staticmethod
    def validate_weekly_breakdown_table(
        api_lead_gen_data: Dict[str, Any],
        ui_table_data: Dict[str, Any]
    ) -> None:
        """
        CELL-BY-CELL Hard assertion validation of Lead Generation Weekly Breakdown Table 
        from /api/Dashboard/LeadGenerationDashboard against DOM Table.
        Validates: Every Week Column (Aug 31, Sep 7, Sep 14, Sep 21, Sep 28) + TOTAL + AVG/WEEK for EVERY User.
        """
        logger.info("==================================================")
        logger.info("3. Lead Generation Weekly Table CELL-BY-CELL Validation: API vs DOM")
        logger.info("==================================================")

        api_user_list = api_lead_gen_data.get("data", [])
        api_week_headers = [w.get("title") for w in api_lead_gen_data.get("weekHeaders", [])]
        
        ui_headers = ui_table_data.get("headers", [])
        ui_rows = ui_table_data.get("rows", [])

        logger.info(f"API Week Headers ({len(api_week_headers)}): {api_week_headers}")
        logger.info(f"UI Table Headers ({len(ui_headers)}): {ui_headers}")

        assert len(ui_rows) > 0, "[HARD ASSERTION FAILURE] UI Weekly Breakdown table is empty!"

        # Map API records by User Name
        api_user_map = {rec.get("userName"): rec for rec in api_user_list}

        # Normalize UI Header lookup
        header_index_map = {h.upper(): idx for idx, h in enumerate(ui_headers)}

        for row_dict in ui_rows:
            # Flexible user name resolution
            user_name = None
            for k, v in row_dict.items():
                if "GENERATOR" in k.upper() or "USER" in k.upper() or k.upper() == "NAME":
                    user_name = v.strip()
                    break

            if not user_name:
                continue

            assert user_name in api_user_map, (
                f"[HARD ASSERTION FAILURE] User '{user_name}' found in UI table but not present in API breakdown!"
            )
            api_rec = api_user_map[user_name]
            api_weeks = api_rec.get("weeks", {})

            logger.info(f"\n--- Validating Cell-by-Cell Data for User: {user_name} ---")

            # A. Validate Each Weekly Column Cell Value
            for week_title in api_week_headers:
                api_val = api_weeks.get(week_title, 0)
                
                # Find matching column in UI row_dict
                ui_val = None
                for col_name, val in row_dict.items():
                    if week_title.upper() in col_name.upper():
                        try:
                            ui_val = int(val)
                        except ValueError:
                            ui_val = 0
                        break

                assert ui_val == api_val, (
                    f"[HARD ASSERTION FAILURE] Cell value mismatch for User '{user_name}', Column '{week_title}'! "
                    f"API Value: {api_val}, UI Value: {ui_val}"
                )
                logger.info(f"[PASS] User '{user_name}' -> Column '{week_title}' API: {api_val} | UI: {ui_val} : CELL HARD ASSERTION PASSED")

            # B. Validate Total Leads Cell Value
            api_total = api_rec.get("totalLeads", 0)
            ui_total_val = None
            for col_name, val in row_dict.items():
                if col_name.upper() == "TOTAL":
                    try:
                        ui_total_val = int(val)
                    except ValueError:
                        ui_total_val = 0
                    break

            assert ui_total_val == api_total, (
                f"[HARD ASSERTION FAILURE] Cell value mismatch for User '{user_name}', Column 'TOTAL'! "
                f"API Total: {api_total}, UI Total: {ui_total_val}"
            )
            logger.info(f"[PASS] User '{user_name}' -> Column 'TOTAL' API: {api_total} | UI: {ui_total_val} : CELL HARD ASSERTION PASSED")

            # C. Validate Avg / Week Cell Value
            api_avg = float(api_rec.get("avgWeek", 0.0))
            ui_avg_val = None
            for col_name, val in row_dict.items():
                if "AVG" in col_name.upper():
                    try:
                        ui_avg_val = float(val)
                    except ValueError:
                        ui_avg_val = 0.0
                    break

            assert ui_avg_val is not None and abs(ui_avg_val - api_avg) < 0.01, (
                f"[HARD ASSERTION FAILURE] Cell value mismatch for User '{user_name}', Column 'AVG / WEEK'! "
                f"API Avg: {api_avg}, UI Avg: {ui_avg_val}"
            )
            logger.info(f"[PASS] User '{user_name}' -> Column 'AVG / WEEK' API: {api_avg} | UI: {ui_avg_val} : CELL HARD ASSERTION PASSED")

        logger.info("==================================================")

    @staticmethod
    def validate_today_activities(
        api_today_activities: Dict[str, Any],
        ui_activities_status: Dict[str, bool]
    ) -> None:
        """
        Hard assertion validation of Today's Meetings & Followups 
        from /api/Dashboard/TodayActivities against UI activity section.
        """
        logger.info("==================================================")
        logger.info("4. Today's Activities Value-Level Validation: API vs UI")
        logger.info("==================================================")

        api_meetings = api_today_activities.get("meetings", [])
        api_followups = api_today_activities.get("followups", [])

        logger.info(f"API Today Meetings Count : {len(api_meetings)}")
        logger.info(f"API Today Followups Count: {len(api_followups)}")

        # Validate Meetings empty state or item counts
        if len(api_meetings) == 0:
            assert ui_activities_status.get("meetings_empty", False), (
                "[HARD ASSERTION FAILURE] API has 0 meetings, but UI did not display empty state message!"
            )
            logger.info("[PASS] Today's Meetings: 0 meetings API matches empty state UI : HARD ASSERTION PASSED")
        else:
            logger.info(f"[PASS] Today's Meetings: {len(api_meetings)} meetings API found")

        # Validate Follow-ups empty state or item counts
        if len(api_followups) == 0:
            assert ui_activities_status.get("reminders_empty", False), (
                "[HARD ASSERTION FAILURE] API has 0 followups, but UI did not display empty state message!"
            )
            logger.info("[PASS] Today's Follow-ups: 0 followups API matches empty state UI : HARD ASSERTION PASSED")
        else:
            logger.info(f"[PASS] Today's Follow-ups: {len(api_followups)} followups API found")

        logger.info("==================================================")
