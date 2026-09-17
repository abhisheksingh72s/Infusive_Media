import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from playwright.sync_api import APIRequestContext, APIResponse
from utilities.api import base_api

logger = logging.getLogger(__name__)

# Standard UI Column Names expected on the Lead Creation Report UI
UI_COLUMNS = [
    "User Name",
    "Total Leads",
    "Assigned",
    "Accepted",
    "Pending",
    "Rejected",
    "Contacted",
    "Won",
    "Lost",
    "Requirement Gathering",
    "Proposal Shared",
    "Negotiation",
    "Decision Pending",
    "Not Interested"
]

# API key fallback aliases to handle potential key variations from backend
API_KEY_MAPPING = {
    "User Name": ["userName", "name", "user_name", "user", "presalesUser", "createdByName"],
    "Total Leads": ["totalLeads", "total_leads", "totalCount", "total"],
    "Assigned": ["assignedLeads", "assigned_leads", "assignedCount", "assigned"],
    "Accepted": ["acceptedLeads", "accepted_leads", "acceptedCount", "accepted"],
    "Pending": ["pendingLeads", "pending_leads", "pendingCount", "pending"],
    "Rejected": ["rejectedLeads", "rejected_leads", "rejectedCount", "rejected"],
    "Contacted": ["contactedLeads", "contacted_leads", "contactedCount", "contacted"],
    "Won": ["wonLeads", "won_leads", "wonCount", "won"],
    "Lost": ["lostLeads", "lost_leads", "lostCount", "lost"],
    "Requirement Gathering": [
        "requirementGathering", "reqGathering", "requirement_gathering", "req_gathering"
    ],
    "Proposal Shared": ["proposalShared", "proposal_shared", "proposalSharedCount"],
    "Negotiation": ["negotiation", "negotiationCount", "negotiation_count"],
    "Decision Pending": ["decisionPending", "decision_pending", "decisionPendingCount"],
    "Not Interested": ["notInterested", "not_interested", "notInterestedCount"]
}


class ReportApiClient:
    """Consolidated Primary API Client for Lead Creation / Presales Report Endpoints."""

    DEFAULT_ENDPOINT = "https://infusive-back.jobvritta.com/api/LeadReport/PresalesLeadReport"
    ENDPOINT = DEFAULT_ENDPOINT  # Class alias for backward compatibility

    def __init__(self, api_context: Optional[APIRequestContext] = None):
        self.api_context = api_context

    def fetch_presales_report(self, user: str = "admin") -> List[Dict[str, Any]]:
        """Fetch Presales Lead Report data from API using Playwright APIRequestContext."""
        token = base_api.get_token(user=user)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        if self.api_context:
            logger.info("Fetching report via Playwright APIRequestContext from %s", self.DEFAULT_ENDPOINT)
            response = self.api_context.get(self.DEFAULT_ENDPOINT, headers=headers)
            assert response.status == 200, f"API call failed with status {response.status}: {response.text()}"
            raw_data = response.json()
        else:
            logger.info("Fetching report via HTTP client from %s", self.DEFAULT_ENDPOINT)
            raw_data = base_api.get("LeadReport/PresalesLeadReport", user=user)

        logger.info("Successfully fetched %d records from API", len(raw_data) if isinstance(raw_data, list) else 1)
        return raw_data

    def get_presales_report_filter(self) -> Tuple[APIResponse, Dict[str, Any]]:
        """
        Execute GET request to report API endpoint using initialized APIRequestContext.
        Returns tuple of (Playwright APIResponse, parsed JSON dict/list).
        """
        logger.info("Executing GET request to: %s", self.DEFAULT_ENDPOINT)
        try:
            response = self.api_context.get(self.DEFAULT_ENDPOINT)
            logger.info("Received HTTP Status: %d %s", response.status, response.status_text)
            try:
                json_data = response.json()
            except Exception as err:
                logger.error("Failed to parse JSON response: %s", str(err))
                json_data = {}

            return response, json_data
        except Exception as exc:
            logger.error("Exception occurred while calling %s: %s", self.DEFAULT_ENDPOINT, str(exc), exc_info=True)
            raise exc

    def get_unauthenticated(self, unauthenticated_context: APIRequestContext) -> APIResponse:
        """Execute GET request without auth headers to verify 401 Unauthorized handling."""
        logger.info("Executing unauthenticated GET request to: %s", self.DEFAULT_ENDPOINT)
        return unauthenticated_context.get(self.DEFAULT_ENDPOINT)

    @staticmethod
    def validate_schema(json_data: Any) -> List[str]:
        """
        Validate schema and top-level data structure of report response JSON.
        Returns a list of error messages (empty list if valid).
        """
        errors = []
        if json_data is None:
            errors.append("Response JSON payload is None.")
            return errors

        if not isinstance(json_data, (dict, list)):
            errors.append(f"Expected top-level response to be dict or list, got {type(json_data).__name__}")
            return errors

        if isinstance(json_data, list) and len(json_data) == 0:
            errors.append("Report records list is empty.")
        elif isinstance(json_data, dict) and len(json_data) == 0:
            errors.append("Report response dictionary is empty.")

        return errors

    @staticmethod
    def normalize_api_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """Map API record dictionary keys to standard UI column names using API_KEY_MAPPING aliases."""
        normalized = {}
        for ui_col, aliases in API_KEY_MAPPING.items():
            val = None
            for alias in aliases:
                if alias in record:
                    val = record[alias]
                    break

            if val is None:
                val = record.get(ui_col, 0 if ui_col != "User Name" else "Unknown")

            if ui_col == "User Name":
                normalized[ui_col] = str(val).strip()
            else:
                try:
                    normalized[ui_col] = int(val)
                except (ValueError, TypeError):
                    normalized[ui_col] = 0

        return normalized

    def get_normalized_api_records(self, user: str = "admin") -> List[Dict[str, Any]]:
        """Fetch raw API records and return them normalized to standard UI Column keys."""
        raw_records = self.fetch_presales_report(user=user)
        if isinstance(raw_records, dict):
            if "data" in raw_records:
                raw_records = raw_records["data"]
            elif "records" in raw_records:
                raw_records = raw_records["records"]
            elif "filterOptions" in raw_records and isinstance(raw_records["filterOptions"], dict) and "Created By" in raw_records["filterOptions"]:
                raw_records = raw_records["filterOptions"]["Created By"]
            else:
                raw_records = [raw_records]

        if not isinstance(raw_records, list):
            raw_records = [raw_records]

        return [self.normalize_api_record(rec) for rec in raw_records]

    @staticmethod
    def calculate_grand_totals(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate Grand Totals across all user records."""
        totals = {"User Name": "GRAND TOTAL"}
        for col in UI_COLUMNS:
            if col == "User Name":
                continue
            col_clean = re.sub(r"[\s_]+", "", col.lower())
            sum_val = 0
            for rec in records:
                val = 0
                for k, v in rec.items():
                    if re.sub(r"[\s_]+", "", str(k).lower()) == col_clean:
                        val = v
                        break
                try:
                    sum_val += int(str(val).replace(",", "").strip())
                except (ValueError, TypeError):
                    pass
            totals[col] = sum_val
        return totals


# Backwards compatibility alias for single-client API consolidation
PresalesReportApiClient = ReportApiClient
