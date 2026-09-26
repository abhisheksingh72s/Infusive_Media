import logging
import os
from typing import Any, Dict, List, Optional
import requests
from utilities.api import base_api

logger = logging.getLogger(__name__)


class LeadAssignmentReportApiClient:
    """API Client for Lead Assignment Report Endpoints."""

    def __init__(self, user: str = "admin"):
        self.user = user
        self.base_url = (
            os.getenv("BASE_API_URL")
            or os.getenv("BASE_API_URL_STG")
            or "https://infusive-back.jobvritta.com/api/"
        ).rstrip("/")

    def _get_headers(self) -> Dict[str, str]:
        token = base_api.get_token(user=self.user)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def fetch_filter_options(self) -> Dict[str, Any]:
        """
        Fetch filter dropdown options from /api/Dropdown/LeadReportFilter.
        Contains the official list of users displayed in the Lead Assignment Report ('Assign To').
        """
        endpoint = f"{self.base_url}/Dropdown/LeadReportFilter"
        logger.info("Fetching filter options from API: %s", endpoint)
        resp = requests.get(endpoint, headers=self._get_headers(), timeout=15)
        if resp.status_code != 200:
            logger.error("Failed to fetch LeadReportFilter: %d - %s", resp.status_code, resp.text)
            resp.raise_for_status()
        return resp.json()

    def fetch_lead_report_summary(self) -> List[Dict[str, Any]]:
        """
        Fetch lead distribution by executive from /api/Lead/LeadReport.
        Returns list of {'executive': name, 'totalLeads': count}.
        """
        endpoint = f"{self.base_url}/Lead/LeadReport"
        logger.info("Fetching lead distribution summary from API: %s", endpoint)
        resp = requests.get(endpoint, headers=self._get_headers(), timeout=15)
        if resp.status_code != 200:
            logger.error("Failed to fetch Lead/LeadReport: %d - %s", resp.status_code, resp.text)
            resp.raise_for_status()
        return resp.json()

    def get_expected_assign_to_users(self) -> List[str]:
        """
        Extract the sorted list of 'Assign To' user names from the filter endpoint.
        These are the exact users expected to appear in the Lead Assignment Report table.
        """
        data = self.fetch_filter_options()
        assign_to_list = data.get("filterOptions", {}).get("Assign To", [])
        user_names = [item["name"] for item in assign_to_list if "name" in item]
        logger.info("Retrieved %d expected 'Assign To' users from API: %s", len(user_names), user_names)
        return user_names

    def get_lead_count_map(self) -> Dict[str, int]:
        """
        Build a dictionary of {executive_name: totalLeads} from /api/Lead/LeadReport.
        """
        summary_list = self.fetch_lead_report_summary()
        count_map = {item["executive"]: item["totalLeads"] for item in summary_list if "executive" in item}
        logger.info("API Executive Lead Counts: %s", count_map)
        return count_map

    def fetch_user_wise_lead_report(self) -> List[Dict[str, Any]]:
        """
        Fetch the full cell-by-cell matrix from /api/LeadReport/UserWiseLeadReport.
        Returns the list of user records with all 13 metric counts.
        """
        params = {
            "lazyParams": '{"first":0,"rows":50,"page":0,"sortField":"","sortOrder":1}',
            "search": "",
            "filter": "{}",
            "timezone": "Asia/Calcutta"
        }
        endpoint = f"{self.base_url}/LeadReport/UserWiseLeadReport"
        logger.info("Fetching full cell-by-cell matrix from API: %s", endpoint)
        resp = requests.get(endpoint, params=params, headers=self._get_headers(), timeout=15)
        if resp.status_code != 200:
            logger.error("Failed to fetch UserWiseLeadReport: %d - %s", resp.status_code, resp.text)
            resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return data.get("data", [])
        elif isinstance(data, list):
            return data
        return []
