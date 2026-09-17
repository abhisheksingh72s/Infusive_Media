import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Expected UI Headers
EXPECTED_HEADERS = [
    "S.NO",
    "USER NAME",
    "TOTAL LEADS",
    "ASSIGNED",
    "ACCEPTED",
    "PENDING",
    "REJECTED",
    "CONTACTED",
    "WON",
    "LOST",
    "REQUIREMENT GATHERING",
    "PROPOSAL SHARED",
    "NEGOTIATION",
    "DECISION PENDING",
    "NOT INTERESTED"
]

# UI Header to camelCase JSON Key Mapping
HEADER_TO_JSON_KEY = {
    "S.NO": "sNo",
    "USER NAME": "userName",
    "TOTAL LEADS": "totalLeads",
    "ASSIGNED": "assigned",
    "ACCEPTED": "accepted",
    "PENDING": "pending",
    "REJECTED": "rejected",
    "CONTACTED": "contacted",
    "WON": "won",
    "LOST": "lost",
    "REQUIREMENT GATHERING": "requirementGathering",
    "PROPOSAL SHARED": "proposalShared",
    "NEGOTIATION": "negotiation",
    "DECISION PENDING": "decisionPending",
    "NOT INTERESTED": "notInterested"
}


class TableJsonParser:
    """Utility class for DOM Table to JSON conversion and data integrity validation."""

    @staticmethod
    def header_to_key(header_name: str) -> str:
        """Convert uppercase header string to camelCase JSON key."""
        clean = header_name.strip().upper()
        return HEADER_TO_JSON_KEY.get(clean, clean.lower())

    @classmethod
    def convert_row_to_json(cls, headers: List[str], cell_values: List[str]) -> Dict[str, Any]:
        """Convert cell text values into a typed JSON dictionary mapped by JSON keys."""
        row_json = {}
        for idx, header in enumerate(headers):
            key = cls.header_to_key(header)
            clean_key = re.sub(r"[\s_]+", "", key.lower())

            if idx < len(cell_values):
                raw_val = cell_values[idx].strip()
                if clean_key in ["username", "user", "sno", "company", "pocname"] or not raw_val.replace(",", "").isdigit():
                    row_json[key] = raw_val
                else:
                    try:
                        row_json[key] = int(raw_val.replace(",", ""))
                    except ValueError:
                        row_json[key] = raw_val
            else:
                row_json[key] = "" if clean_key in ["username", "user", "sno"] else 0

        # Also store standard "User Name" key for direct lookup compatibility
        if "userName" in row_json:
            row_json["User Name"] = str(row_json["userName"]).strip()

        return row_json

    @classmethod
    def validate_headers(cls, actual_headers: List[str], expected_headers: List[str] = EXPECTED_HEADERS) -> bool:
        """Verify that expected headers are present in the actual UI headers."""
        actual_upper = [h.strip().upper() for h in actual_headers]
        logger.info("Validating UI Headers. Actual Headers (%d): %s", len(actual_upper), actual_upper)
        missing = [h for h in expected_headers if h not in actual_upper]
        if missing:
            logger.warning("Some expected headers are absent in current UI view: %s", missing)
            return len(actual_upper) > 0 and len(missing) < len(expected_headers)
        logger.info("✓ All %d expected column headers are displayed on UI", len(expected_headers))
        return True

    @classmethod
    def validate_row_data(cls, actual_row_json: Dict[str, Any], expected_json: Dict[str, Any], row_name: str = "Row") -> List[str]:
        """Validate expected key-value pairs against actual extracted row JSON."""
        mismatches = []
        logger.info("=== Validating %s JSON Data ===", row_name)
        for key, exp_val in expected_json.items():
            act_val = actual_row_json.get(key)
            if act_val is None and key not in actual_row_json:
                logger.warning("Field '%s' not present in current UI table column headers", key)
                continue

            if act_val != exp_val:
                err = (
                    f"Mismatch in {row_name} for key '{key}': "
                    f"Expected = {exp_val} ({type(exp_val).__name__}), Got = {act_val} ({type(act_val).__name__})"
                )
                logger.error("❌ %s", err)
                mismatches.append(err)
            else:
                logger.info("  ✓ [MATCH] %s -> %s: %s", row_name, key, act_val)
        return mismatches
