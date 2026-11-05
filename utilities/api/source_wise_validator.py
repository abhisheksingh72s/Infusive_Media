import logging
from typing import Any, Dict, List
from pages.source_wise_report_page import EXPECTED_SOURCE_WISE_HEADERS

logger = logging.getLogger(__name__)


class SourceWiseValidator:
    """
    Strict Hard Assertion Validator for Source Wise Report (Source Lead Allocation): API vs DOM UI.
    NEVER uses soft assertions — any mismatch raises an immediate AssertionError.
    """

    @staticmethod
    def validate_headers(dom_headers: List[str]):
        """Validate that all DOM table headers strictly match expected schema (16 headers)."""
        logger.info("=" * 60)
        logger.info("1. Validating Table Column Headers (Expected vs DOM)")
        logger.info("=" * 60)

        assert len(dom_headers) == len(EXPECTED_SOURCE_WISE_HEADERS), (
            f"Header count mismatch! Expected {len(EXPECTED_SOURCE_WISE_HEADERS)}, got {len(dom_headers)}"
        )

        for idx, (exp, actual) in enumerate(zip(EXPECTED_SOURCE_WISE_HEADERS, dom_headers)):
            assert exp.strip().lower() == actual.strip().lower(), (
                f"Header mismatch at column index {idx}! Expected '{exp}', got '{actual}'"
            )

        logger.info("[PASS] All %d Column Headers Strictly Matched! : HARD ASSERTION PASSED", len(dom_headers))

    @staticmethod
    def validate_sources_list(dom_rows: List[Dict[str, Any]], expected_api_sources: List[str]):
        """Validate that DOM rows match the expected sources list from API filter options."""
        logger.info("=" * 60)
        logger.info("2. Validating Source List (API 'Source Filter' vs DOM Table Rows)")
        logger.info("=" * 60)

        dom_source_names = [row.get("sourceName", "").strip() for row in dom_rows]

        assert len(dom_source_names) == len(expected_api_sources), (
            f"Source row count mismatch! Expected {len(expected_api_sources)} sources, got {len(dom_source_names)} rows."
        )

        for idx, expected_source in enumerate(expected_api_sources):
            actual_source = dom_source_names[idx]
            assert actual_source.casefold() == expected_source.casefold(), (
                f"Row {idx + 1} source mismatch! Expected '{expected_source}', got '{actual_source}'"
            )

        logger.info("[PASS] All %d Source Rows strictly match API Source Filter List! : HARD ASSERTION PASSED", len(dom_source_names))

    METRIC_MAPPING = [
        ("Created Leads", "createdLeads", ["totalLeads", "createdLeads", "totalCount", "total"]),
        ("Accepted", "accepted", ["accepted", "acceptedLeads", "acceptedCount"]),
        ("Not Accepted", "notAccepted", ["pending", "pendingLeads", "notAccepted", "notAcceptedLeads"]),
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
        ("Duplicate", "duplicate", ["duplicate", "duplicateLeads", "duplicateCount"]),
        ("Unassigned", "unassigned", ["unassigned", "unassignedLeads", "unassignedCount"])
    ]

    MODAL_METRIC_MAPPING = [
        ("Created Leads", "createdLeads", ["totalLeads", "createdLeads"]),
        ("Accepted", "accepted", ["accepted"]),
        ("Not Accepted", "notAccepted", ["pending", "notAccepted"]),
        ("Pending", "pending", ["pending"]),
        ("Rejected", "rejected", ["rejected"]),
        ("Assigned", "assigned", ["assigned"]),
        ("Contacted", "contacted", ["contacted"]),
        ("Requirement Gathering", "requirementGathering", ["requirementGathering"]),
        ("Won", "won", ["won"]),
        ("Lost", "lost", ["lost"]),
        ("Duplicate", "duplicate", ["duplicate"]),
        ("Unassigned", "unassigned", ["unassigned"])
    ]

    @classmethod
    def validate_cell_by_cell_api_vs_dom(
        cls,
        dom_rows: List[Dict[str, Any]],
        api_rows: List[Dict[str, Any]]
    ):
        """
        Validate ALL 15 metrics across ALL source rows cell-by-cell between API and DOM UI.
        Total assertions = len(dom_rows) x 15 metrics.
        """
        logger.info("=" * 60)
        logger.info("3. Complete Cell-by-Cell Hard Validation: API vs DOM (%d Sources x 15 Metrics)", len(dom_rows))
        logger.info("=" * 60)

        api_source_map: Dict[str, Dict[str, Any]] = {}
        for row in api_rows:
            sname = (row.get("sourceName") or row.get("name") or row.get("source") or "").strip()
            if sname:
                api_source_map[sname.casefold()] = row

        table_lines = []
        table_lines.append("=" * 77)
        table_lines.append("SOURCE-WISE VALIDATION (API vs UI)")
        table_lines.append("=" * 77)
        table_lines.append(f"| {'Source':<18} | {'Metric':<22} | {'Actual(UI)':<10} | {'API Record':<10} | {'M/F':<3} |")
        table_lines.append(f"|{'-'*20}|{'-'*24}|{'-'*12}|{'-'*12}|{'-'*5}|")

        total_assertions = 0

        for dom_row in dom_rows:
            source_name = dom_row.get("sourceName", "").strip()
            api_row = api_source_map.get(source_name.casefold(), {})

            has_data = any(dom_row.get(k, 0) > 0 for _, k, _ in cls.METRIC_MAPPING)

            for display_name, dom_key, api_aliases in cls.METRIC_MAPPING:
                dom_val = dom_row.get(dom_key, 0)

                api_val = 0
                for alias in api_aliases:
                    if alias in api_row and api_row[alias] is not None:
                        try:
                            api_val = int(str(api_row[alias]).replace(",", "").strip())
                            break
                        except (ValueError, TypeError):
                            api_val = 0

                status = "M" if dom_val == api_val else "F"

                assert dom_val == api_val, (
                    f"CELL MISMATCH: Source '{source_name}' -> Column '{display_name}'! "
                    f"API: {api_val} != UI: {dom_val}"
                )
                total_assertions += 1

                if dom_val > 0 or api_val > 0 or (has_data and display_name in ["Created Leads", "Accepted", "Not Accepted", "Rejected", "Assigned"]):
                    table_lines.append(f"| {source_name:<18} | {display_name:<22} | {dom_val:<10} | {api_val:<10} | {status:<3} |")

        table_lines.append("=" * 77)
        table_block = "\n" + "\n".join(table_lines) + "\n"
        print(table_block)

        logger.info("[PASS] ALL %d Cell-by-Cell Hard Assertions PASSED!", total_assertions)

    @classmethod
    def validate_grand_totals(cls, dom_rows: List[Dict[str, Any]], dom_grand_total: Dict[str, Any]):
        """
        Validate that the Grand Total row correctly sums every numeric column across all source rows.
        """
        logger.info("=" * 60)
        logger.info("4. Validating Grand Total Column-by-Column Aggregation")
        logger.info("=" * 60)

        metric_columns = [
            "createdLeads", "accepted", "notAccepted", "rejected",
            "assigned", "contacted", "requirementGathering", "proposalShared",
            "negotiation", "decisionPending", "won", "lost", "notInterested",
            "duplicate", "unassigned"
        ]

        for col in metric_columns:
            computed_sum = sum(row.get(col, 0) for row in dom_rows)
            grand_total_val = dom_grand_total.get(col, 0)

            assert computed_sum == grand_total_val, (
                f"Grand Total mismatch for column '{col}'! "
                f"Sum of rows: {computed_sum} != Grand Total row: {grand_total_val}"
            )

        logger.info("[PASS] ALL 15 Metric Columns in Grand Total match sum of rows! : HARD ASSERTION PASSED")

    @classmethod
    def validate_modal_user_wise_details(
        cls,
        dom_modal_rows: List[Dict[str, Any]],
        api_modal_rows: List[Dict[str, Any]],
        source_name: str
    ):
        """
        Validate user-wise lead breakdown rows in the drilldown modal against UserWiseLeadDetails API response.
        """
        logger.info("=" * 60)
        logger.info("Validating Modal User-Wise Lead Details for Source: %s", source_name)
        logger.info("=" * 60)

        api_user_map: Dict[str, Dict[str, Any]] = {}
        for row in api_modal_rows:
            uname = (row.get("userName") or row.get("name") or "").strip()
            if uname:
                api_user_map[uname.casefold()] = row

        total_modal_assertions = 0

        for dom_row in dom_modal_rows:
            user_name = dom_row.get("userName", "").strip()
            if not user_name:
                continue
            api_row = api_user_map.get(user_name.casefold(), {})

            for display_name, dom_key, api_aliases in cls.MODAL_METRIC_MAPPING:
                dom_val = dom_row.get(dom_key, 0)

                api_val = 0
                for alias in api_aliases:
                    if alias in api_row and api_row[alias] is not None:
                        try:
                            api_val = int(str(api_row[alias]).replace(",", "").strip())
                            break
                        except (ValueError, TypeError):
                            api_val = 0

                assert dom_val == api_val, (
                    f"MODAL CELL MISMATCH: Source '{source_name}' -> User '{user_name}' -> Column '{display_name}'! "
                    f"API: {api_val} != UI: {dom_val}"
                )
                total_modal_assertions += 1

        logger.info("[PASS] ALL %d Modal User-Wise Cell Assertions Passed for '%s'!", total_modal_assertions, source_name)
