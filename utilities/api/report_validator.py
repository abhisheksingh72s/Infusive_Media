import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple
from utilities.api.report_api_client import UI_COLUMNS

logger = logging.getLogger(__name__)


class LeadReportValidator:
    """Helper class for validating API vs DOM UI data with formatted block logging."""

    @staticmethod
    def normalize_ui_row(ui_row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize DOM UI row keys to match standard UI_COLUMNS."""
        normalized = {}
        clean_row = {re.sub(r"[\s_]+", "", str(k).lower()): v for k, v in ui_row.items()}

        # 1. User Name Extraction Logic (handles userName, name, user, assigned to, poc name)
        user_name_val = "Unknown"
        for candidate_key in ["username", "user", "name", "assignedto", "pocname"]:
            if candidate_key in clean_row and clean_row[candidate_key]:
                user_name_val = str(clean_row[candidate_key]).strip()
                break

        # Strip emojis / icons from username if present (e.g. "📊 GRAND TOTAL" -> "GRAND TOTAL")
        cleaned_user = re.sub(r"[^\w\s-]", "", user_name_val).strip()
        normalized["User Name"] = cleaned_user or user_name_val

        # 2. Metric Columns Normalization
        for target_col in UI_COLUMNS:
            if target_col == "User Name":
                continue

            col_key = re.sub(r"[\s_]+", "", target_col.lower())
            if col_key in clean_row:
                val = clean_row[col_key]
                try:
                    normalized[target_col] = int(str(val).replace(",", "").strip())
                except (ValueError, TypeError):
                    normalized[target_col] = 0
            else:
                normalized[target_col] = 0

        return normalized

    @classmethod
    def calculate_grand_totals(cls, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate Grand Totals dynamically across all user records."""
        totals = {"User Name": "GRAND TOTAL"}
        for col in UI_COLUMNS:
            if col == "User Name":
                continue
            sum_val = 0
            for rec in records:
                norm = cls.normalize_ui_row(rec)
                val = norm.get(col, 0)
                try:
                    sum_val += int(val)
                except (ValueError, TypeError):
                    pass
            totals[col] = sum_val
        return totals

    @classmethod
    def log_and_compare_field(cls, user_name: str, field_name: str, api_val: Any, dom_val: Any) -> Tuple[bool, str]:
        """Compare API Value against DOM Value and log using required block format."""
        is_pass = (api_val == dom_val)
        result_str = "PASS" if is_pass else "FAIL"

        log_msg = (
            f"\n==================================================\n"
            f"User: {user_name}\n"
            f"Field: {field_name}\n"
            f"API Value: {api_val}\n"
            f"DOM Value: {dom_val}\n"
            f"Result: {result_str}\n"
            f"=================================================="
        )

        if is_pass:
            logger.info(log_msg)
            err_summary = ""
        else:
            logger.error(log_msg)
            err_summary = f"Field: User '{user_name}' - {field_name} | API Value: {api_val} | UI Value: {dom_val}"

        return is_pass, err_summary

    @classmethod
    def print_summary_report(
        cls,
        module_name: str,
        api_endpoint: str,
        api_records_count: int,
        ui_records_count: int,
        headers_status: str,
        user_val_status: str,
        grand_total_status: str,
        fields_compared: int,
        pass_count: int,
        fail_count: int,
        final_result: str,
        start_time: str,
        end_time: str,
        duration: str,
        failed_fields_details: List[str] = None
    ):
        """Print execution summary report in logger.info format."""
        summary = (
            f"\n============================================================\n"
            f"LEAD CREATION REPORT API VS UI VALIDATION SUMMARY\n"
            f"============================================================\n"
            f"Module            : {module_name}\n"
            f"API Endpoint      : {api_endpoint}\n"
            f"API Records       : {api_records_count}\n"
            f"UI Records        : {ui_records_count}\n"
            f"Headers           : {headers_status}\n"
            f"User Validation   : {user_val_status}\n"
            f"Grand Total       : {grand_total_status}\n"
            f"Fields Compared   : {fields_compared}\n"
            f"Pass Count        : {pass_count}\n"
            f"Fail Count        : {fail_count}\n"
            f"Final Result      : {final_result}\n"
            f"------------------------------------------------------------\n"
            f"Execution Start   : {start_time}\n"
            f"Execution End     : {end_time}\n"
            f"Duration          : {duration}\n"
            f"============================================================"
        )

        if fail_count > 0 and failed_fields_details:
            summary += f"\nFAILED FIELDS DETAILS ({len(failed_fields_details)}):\n" + "\n".join(f" - {err}" for err in failed_fields_details if err) + "\n============================================================"

        logger.info(summary)

    @classmethod
    def validate_api_vs_dom(
        cls,
        dom_user_rows: List[Dict[str, Any]],
        dom_grand_total: Dict[str, Any],
        api_records: List[Dict[str, Any]],
        target_user: str = "Admin"
    ) -> Tuple[bool, List[str]]:
        """
        Perform dynamic API vs DOM validation targeting target_user (default "Admin").
        Returns tuple of (is_success, failed_mismatches_list).
        """
        mismatches = []
        norm_dom_user_rows = [cls.normalize_ui_row(r) for r in dom_user_rows]

        # Index API records by case-insensitive normalized User Name
        api_user_map = {}
        for rec in api_records:
            u_name = rec.get("User Name", rec.get("name", rec.get("userName", rec.get("createdByName", ""))))
            key = str(u_name).strip().lower()
            api_user_map[key] = rec

        rows_to_validate = norm_dom_user_rows
        if target_user:
            target_key = target_user.strip().lower()
            rows_to_validate = [r for r in norm_dom_user_rows if r["User Name"].strip().lower() == target_key]

        for norm_dom in rows_to_validate:
            dom_user = norm_dom["User Name"].strip()
            user_key = dom_user.lower()

            matched_api_rec = api_user_map.get(user_key)
            matched_api_user = (
                matched_api_rec.get("User Name", matched_api_rec.get("name", matched_api_rec.get("userName", matched_api_rec.get("createdByName", ""))))
                if matched_api_rec else "NONE"
            )

            logger.info("==================================================")
            logger.info("Matched User API Object: %s", matched_api_rec)
            logger.info("Normalized Username: %s", dom_user)
            logger.info("==================================================")

            if not matched_api_rec:
                err = f"DOM User '{dom_user}' not found in API records!"
                logger.error(err)
                mismatches.append(err)
                continue

            for col in UI_COLUMNS:
                if col == "User Name":
                    continue
                api_val = matched_api_rec.get(col, matched_api_rec.get(re.sub(r"[\s_]+", "", col.lower()), 0))
                dom_val = norm_dom.get(col, 0)

                is_pass, err_msg = cls.log_and_compare_field(dom_user, col, api_val, dom_val)
                if not is_pass:
                    mismatches.append(err_msg)

        # Grand Total Validation
        calculated_api_gt = cls.calculate_grand_totals(dom_user_rows)
        norm_dom_gt = cls.normalize_ui_row(dom_grand_total) if dom_grand_total else {}

        logger.info(
            f"\n==================================================\n"
            f"Calculated API Grand Total: {calculated_api_gt}\n"
            f"DOM Grand Total: {norm_dom_gt}\n"
            f"=================================================="
        )

        for col in UI_COLUMNS:
            if col == "User Name":
                continue
            api_gt_val = calculated_api_gt.get(col, 0)
            dom_gt_val = norm_dom_gt.get(col, 0)

            is_pass, err_msg = cls.log_and_compare_field("Grand Total", col, api_gt_val, dom_gt_val)
            if not is_pass:
                mismatches.append(err_msg)

        return len(mismatches) == 0, mismatches
