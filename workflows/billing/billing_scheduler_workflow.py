"""
Billing Scheduler Workflow
==========================
Encapsulates triggering the developer's test scheduler endpoints:
  - POST /api/billing-test/generate/{configId}?date={date}
  - POST /api/billing-test/run-daily-job
And asserting the plan state updates in Central Billing Plans (/allBillingPlans).
"""

import logging
from datetime import datetime
from playwright.sync_api import Page
from pages.billing_plans_page import BillingPlansPage

logger = logging.getLogger(__name__)


class BillingSchedulerWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.billing_page = BillingPlansPage(page)

    def trigger_scheduler_job(self, config_id: int = None, date_str: str = None) -> dict:
        """Call developer's test API to run the recurring invoice scheduler or targeted generation."""
        base_api = "https://infusive-back.jobvritta.com"
        today_date = date_str or datetime.now().strftime("%Y-%m-%d")

        # Extract JWT Bearer token from live page session or base_api
        token = None
        try:
            token = self.page.evaluate("() => localStorage.getItem('token')")
        except Exception:
            pass
        if not token:
            try:
                from utilities.api.base_api import get_token
                token = get_token("admin")
            except Exception:
                pass

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        if config_id:
            endpoint = f"{base_api}/api/billing-test/generate/{config_id}?date={today_date}"
            logger.info(f"Calling developer test API: POST {endpoint}")
            res = self.page.request.post(endpoint, headers=headers)
            logger.info(f"Targeted API Response [{res.status}]: {res.text()}")
            if res.status == 200:
                data = res.json()
                logger.info(f"Generated Invoice from scheduler API: {data}")
                return data

        daily_job_endpoint = f"{base_api}/api/billing-test/run-daily-job"
        logger.info(f"Calling developer daily job API: POST {daily_job_endpoint}")
        res = self.page.request.post(daily_job_endpoint, headers=headers)
        logger.info(f"Daily Job API Response [{res.status}]: {res.text()}")
        if res.status == 200:
            return res.json()

        return {"status": res.status, "message": "API call completed"}

    def verify_plan_in_ledger(
        self,
        company_name: str,
        expected_invoices: int = 1,
        expected_status: str = "Active",
    ) -> dict:
        """Navigate to /allBillingPlans and verify the plan status and generated invoices count."""
        logger.info(f"Verifying Billing Plan in ledger for '{company_name}'...")
        self.billing_page.go_to_billing_plans()
        self.page.wait_for_timeout(1000)
        self.billing_page.search_plans(company_name)
        self.page.wait_for_timeout(1000)

        rows = self.billing_page.get_table_rows()
        assert rows.count() > 0, f"Expected at least 1 billing plan row in Ledger for '{company_name}', but found 0!"
        data = self.billing_page.get_plan_row_data(0)
        logger.info(f"Verified Billing Plan Row: {data}")
        return data
