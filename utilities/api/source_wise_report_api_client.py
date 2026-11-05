import logging
import os
from typing import Any, Dict, List, Optional
import requests
from utilities.api import base_api

logger = logging.getLogger(__name__)


class SourceWiseReportApiClient:
    """API Client for Source Wise Report (Source Lead Allocation) Endpoints."""

    def __init__(self, user: str = "admin", base_url: Optional[str] = None):
        self.user = user
        self.base_url = (
            base_url
            or os.getenv("BASE_API_URL")
            or os.getenv("BASE_API_URL_STG")
            or "https://infusive-back.jobvritta.com/api/"
        ).rstrip("/")

    def _get_headers(self) -> Dict[str, str]:
        token = base_api.get_token(user=self.user, base_url=self.base_url)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def fetch_filter_options(self) -> Dict[str, Any]:
        """
        Fetch filter dropdown options from /dropdown/sourceWiseReportFilter.
        Contains the official list of sources displayed in the Source Wise Report ('Source Filter').
        """
        endpoint = f"{self.base_url}/dropdown/sourceWiseReportFilter"
        logger.info("Fetching filter options from API: %s", endpoint)
        resp = requests.get(endpoint, headers=self._get_headers(), timeout=15)
        if resp.status_code != 200:
            logger.error("Failed to fetch sourceWiseReportFilter: %d - %s", resp.status_code, resp.text)
            resp.raise_for_status()
        return resp.json()

    def get_expected_sources(self) -> List[str]:
        """
        Extract the sorted list of 'Source Filter' names from the filter endpoint.
        These are the exact sources expected to appear in the Source Wise Report table.
        """
        data = self.fetch_filter_options()
        source_filter_list = data.get("filterOptions", {}).get("Source Filter", [])
        source_names = [item["name"] for item in source_filter_list if "name" in item]
        logger.info("Retrieved %d expected 'Source Filter' sources from API: %s", len(source_names), source_names)
        return source_names

    def fetch_source_wise_report(self, search: str = "", rows: int = 50, start_date: str = "", end_date: str = "") -> List[Dict[str, Any]]:
        """
        Fetch full cell-by-cell matrix from /SourceWiseReport.
        Returns the list of source records with all metric counts.
        Optionally supports start_date and end_date filtering.
        """
        filter_dict = {}
        if start_date and end_date:
            filter_dict["startDate"] = start_date
            filter_dict["endDate"] = end_date
        
        import json
        params = {
            "lazyParams": f'{{"first":0,"rows":{rows},"page":0,"sortField":"","sortOrder":1}}',
            "search": search,
            "filter": json.dumps(filter_dict),
            "timezone": "Asia/Calcutta"
        }
        if start_date and end_date:
            params["startDate"] = start_date
            params["endDate"] = end_date

        endpoint = f"{self.base_url}/SourceWiseReport"
        logger.info("Fetching Source Wise Report cell-by-cell matrix from API (filter=%s)...", json.dumps(filter_dict))
        resp = requests.get(endpoint, params=params, headers=self._get_headers(), timeout=15)
        if resp.status_code != 200:
            logger.error("Failed to fetch SourceWiseReport: %d - %s", resp.status_code, resp.text)
            resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return data.get("data", [])
        elif isinstance(data, list):
            return data
        return []

    def fetch_user_wise_lead_details(self, source_id: int = 1, status: str = "totalLeads") -> List[Dict[str, Any]]:
        """
        Fetch user-wise lead drilldown details modal data from /SourceWiseReport/UserWiseLeadDetails.
        """
        endpoint = f"{self.base_url}/SourceWiseReport/UserWiseLeadDetails"
        params = {
            "sourceId": source_id,
            "status": status,
            "search": "",
            "filter": "{}",
            "type": "userWise"
        }
        logger.info("Fetching UserWiseLeadDetails from API: %s | Params: %s", endpoint, params)
        resp = requests.get(endpoint, params=params, headers=self._get_headers(), timeout=15)
        if resp.status_code != 200:
            logger.error("Failed to fetch UserWiseLeadDetails: %d - %s", resp.status_code, resp.text)
            resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return data.get("data", [])
        elif isinstance(data, list):
            return data
        return []

    def fetch_source_wise_lead_details(self, source_id: int = 1, status: str = "totalLeads") -> List[Dict[str, Any]]:
        """
        Fetch source-wise lead drilldown details modal data from /SourceWiseReport/getsourceWiseDetail.
        """
        endpoint = f"{self.base_url}/SourceWiseReport/getsourceWiseDetail"
        params = {
            "sourceId": source_id,
            "status": status,
            "search": "",
            "filter": "{}",
            "type": "sourceWise"
        }
        logger.info("Fetching getsourceWiseDetail from API: %s | Params: %s", endpoint, params)
        resp = requests.get(endpoint, params=params, headers=self._get_headers(), timeout=15)
        if resp.status_code != 200:
            logger.error("Failed to fetch getsourceWiseDetail: %d - %s", resp.status_code, resp.text)
            resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return data.get("data", [])
        elif isinstance(data, list):
            return data
        return []
