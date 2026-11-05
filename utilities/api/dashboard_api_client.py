import logging
import requests
from typing import Any, Dict, List, Optional
from utilities.api import base_api

logger = logging.getLogger(__name__)


class DashboardApiClient:
    """API Client for fetching Admin Dashboard analytics metrics, cards, charts, and tables."""

    def __init__(self, user: str = "admin"):
        self.user = user

    @staticmethod
    def get_headers() -> Dict[str, str]:
        token = base_api.get_token(user="admin")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def fetch_monthly_leads_data(self, year: int = 2026) -> List[Dict[str, Any]]:
        """Fetch monthly lead matrix data from /api/Dashboard/leadByMonth?year={year}."""
        base_url = base_api.BASE_URL.rstrip("/")
        url = f"{base_url}/Dashboard/leadByMonth?year={year}"
        headers = self.get_headers()
        
        logger.info(f"Fetching monthly leads matrix from API: {url}")
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()
        logger.info(f"Successfully fetched {len(data)} month data entries from API")
        return data

    def fetch_dashboard_summary(self, time_zone: str = "Asia/Calcutta") -> Dict[str, Any]:
        """Fetch dashboard summary cards and status counts from /api/Dashboard/dashboard-summary."""
        base_url = base_api.BASE_URL.rstrip("/")
        url = f"{base_url}/Dashboard/dashboard-summary?timeZone={time_zone}"
        headers = self.get_headers()
        
        logger.info(f"Fetching dashboard summary metrics from API: {url}")
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()
        logger.info("Successfully fetched dashboard summary from API")
        return data

    def fetch_lead_generation_dashboard(self, year: int = 2026, month: int = 9) -> Dict[str, Any]:
        """Fetch weekly breakdown matrix from /api/Dashboard/LeadGenerationDashboard?year={year}&month={month}."""
        base_url = base_api.BASE_URL.rstrip("/")
        url = f"{base_url}/Dashboard/LeadGenerationDashboard?year={year}&month={month}"
        headers = self.get_headers()
        
        logger.info(f"Fetching lead generation weekly matrix from API: {url}")
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()
        logger.info("Successfully fetched LeadGenerationDashboard matrix from API")
        return data

    def fetch_today_activities(self, time_zone: str = "Asia/Calcutta") -> Dict[str, Any]:
        """Fetch today's meetings and follow-ups from /api/Dashboard/TodayActivities."""
        base_url = base_api.BASE_URL.rstrip("/")
        url = f"{base_url}/Dashboard/TodayActivities?timeZone={time_zone}"
        headers = self.get_headers()
        
        logger.info(f"Fetching TodayActivities from API: {url}")
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()
        logger.info("Successfully fetched TodayActivities from API")
        return data
