import logging
from typing import Any, Dict, List
from pages.lead_assignment_report_page import EXPECTED_ASSIGNMENT_HEADERS

logger = logging.getLogger(__name__)


class LeadAssignmentValidator:
    """
    Strict Hard Assertion Validator for Lead Assignment Report: API vs DOM.
    NEVER uses soft assertions — any mismatch raises an immediate AssertionError.
    """

    @staticmethod
    def validate_headers(dom_headers: List[str]):
        """Validate that all DOM table headers strictly match expected schema."""
        logger.info("=" * 60)
        logger.info("1. Validating Table Column Headers (Expected vs DOM)")
        logger.info("=" * 60)
        logger.info("Expected Headers (%d): %s", len(EXPECTED_ASSIGNMENT_HEADERS), EXPECTED_ASSIGNMENT_HEADERS)
        logger.info("Actual DOM Headers (%d): %s", len(dom_headers), dom_headers)

        assert len(dom_headers) == len(EXPECTED_ASSIGNMENT_HEADERS), (
            f"Header count mismatch! Expected {len(EXPECTED_ASSIGNMENT_HEADERS)}, got {len(dom_headers)}"
        )

        for idx, (exp, actual) in enumerate(zip(EXPECTED_ASSIGNMENT_HEADERS, dom_headers)):
            assert exp.strip().lower() == actual.strip().lower(), (
                f"Header mismatch at column index {idx}! Expected '{exp}', got '{actual}'"
            )
            logger.info("  [PASS] Column %d: '%s' matches '%s'", idx + 1, actual, exp)

        logger.info("[PASS] All %d Column Headers Strictly Matched! : HARD ASSERTION PASSED", len(dom_headers))

    @staticmethod
    def validate_users_list(dom_rows: List[Dict[str, Any]], expected_api_users: List[str]):
        """Validate that DOM rows match the expected users list from API."""
        logger.info("=" * 60)
        logger.info("2. Validating User List (API 'Assign To' vs DOM Table Rows)")
        logger.info("=" * 60)

        dom_user_names = [row.get("userName", "").strip() for row in dom_rows]
        logger.info("API Expected Users (%d): %s", len(expected_api_users), expected_api_users)
        logger.info("DOM Table Users    (%d): %s", len(dom_user_names), dom_user_names)

        assert len(dom_user_names) == len(expected_api_users), (
            f"User row count mismatch! Expected {len(expected_api_users)} users, got {len(dom_user_names)} rows."
        )

        for idx, expected_user in enumerate(expected_api_users):
            actual_user = dom_user_names[idx]
            assert actual_user.casefold() == expected_user.casefold(), (
                f"Row {idx + 1} user mismatch! Expected '{expected_user}', got '{actual_user}'"
            )
            logger.info("  [PASS] Row %d User: '%s' matches API user '%s'", idx + 1, actual_user, expected_user)

        logger.info("[PASS] All %d User Rows strictly match API User List! : HARD ASSERTION PASSED", len(dom_user_names))

    METRIC_MAPPING = [
        ("Created Leads", "createdLeads", ["createdLeads", "totalLeads", "totalCount", "total"]),
        ("Accepted", "accepted", ["accepted", "acceptedLeads", "acceptedCount"]),
        ("Not Accepted", "notAccepted", ["notAccepted", "notAcceptedLeads", "pending", "pendingLeads"]),
        ("Rejected", "rejected", ["rejected", "rejectedLeads", "rejectedCount"]),
        ("Assigned", "assigned", ["assigned", "assignedLeads", "assignedCount"]),
        ("Contacted", "contacted", ["contacted", "contactedLeads", "contactedCount"]),
        ("Requirement Gathering", "requirementGathering", ["requirementGathering", "reqGathering", "requirement_gathering"]),
        ("Proposal Shared", "proposalShared", ["proposalShared", "proposal_shared"]),
        ("Negotiation", "negotiation", ["negotiation"]),
        ("Decision Pending", "decisionPending", ["decisionPending", "decision_pending"]),
        ("Won", "won", ["won", "wonLeads", "wonCount"]),
        ("Lost", "lost", ["lost", "lostLeads", "lostCount"]),
        ("Not Interested", "notInterested", ["notInterested", "not_interested"]),
    ]

    @classmethod
    def validate_cell_by_cell_api_vs_dom(
        cls,
        dom_rows: List[Dict[str, Any]],
        api_rows: List[Dict[str, Any]]
    ):
        """
        Validate ALL 13 metrics for ALL 10 users cell-by-cell between API and DOM UI.
        Total: 10 users x 13 metrics = 130 HARD ASSERTIONS.
        """
        logger.info("=" * 60)
        logger.info("3. Complete Cell-by-Cell Hard Validation: API vs DOM (130 Assertions)")
        logger.info("=" * 60)

        # Index API rows by user name
        api_user_map: Dict[str, Dict[str, Any]] = {}
        for row in api_rows:
            uname = (row.get("userName") or row.get("executive") or row.get("name") or "").strip()
            if uname:
                api_user_map[uname.casefold()] = row

        total_assertions = 0

        for dom_row in dom_rows:
            user_name = dom_row.get("userName", "").strip()
            api_row = api_user_map.get(user_name.casefold(), {})

            logger.info("--- Validating 13 Metrics for User: %s ---", user_name)

            for display_name, dom_key, api_aliases in cls.METRIC_MAPPING:
                dom_val = dom_row.get(dom_key, 0)

                # Extract value from API row using aliases
                api_val = 0
                for alias in api_aliases:
                    if alias in api_row and api_row[alias] is not None:
                        try:
                            api_val = int(str(api_row[alias]).replace(",", "").strip())
                            break
                        except (ValueError, TypeError):
                            api_val = 0

                assert dom_val == api_val, (
                    f"CELL MISMATCH: User '{user_name}' -> Column '{display_name}'! "
                    f"API: {api_val} != UI: {dom_val}"
                )
                logger.info("  [PASS] User '%s' -> Column '%s' API: %d | UI: %d : CELL HARD ASSERTION PASSED",
                            user_name, display_name, api_val, dom_val)
                total_assertions += 1

        logger.info("=" * 60)
        logger.info("[PASS] ALL %d Cell-by-Cell (10 Users x 13 Metrics) Hard Assertions PASSED!", total_assertions)
        logger.info("=" * 60)

    @classmethod
    def validate_grand_totals(cls, dom_rows: List[Dict[str, Any]], dom_grand_total: Dict[str, Any]):
        """
        Validate that the Grand Total row correctly sums every numeric column across all user rows.
        """
        logger.info("=" * 60)
        logger.info("4. Validating Grand Total Column-by-Column Aggregation")
        logger.info("=" * 60)

        metric_columns = [
            "createdLeads", "accepted", "notAccepted", "rejected",
            "assigned", "contacted", "requirementGathering", "proposalShared",
            "negotiation", "decisionPending", "won", "lost", "notInterested"
        ]

        for col in metric_columns:
            computed_sum = sum(row.get(col, 0) for row in dom_rows)
            grand_total_val = dom_grand_total.get(col, 0)

            assert computed_sum == grand_total_val, (
                f"Grand Total mismatch for column '{col}'! "
                f"Sum of rows: {computed_sum} != Grand Total row: {grand_total_val}"
            )
            logger.info("  [PASS] Column '%s' -> Computed Sum: %d | Grand Total: %d : HARD ASSERTION PASSED",
                        col, computed_sum, grand_total_val)

        logger.info("[PASS] ALL 13 Metric Columns in Grand Total match sum of rows! : HARD ASSERTION PASSED")
