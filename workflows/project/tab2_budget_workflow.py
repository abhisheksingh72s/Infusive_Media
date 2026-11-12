"""
Service Budget Workflow (Tab 2)
===============================
Encapsulates configuring Service Budgeting breakdown rows, durations, amounts,
and service types (Recurring vs OneTime).
"""

import logging
from datetime import datetime
from playwright.sync_api import Page
from pages.project_page import ProjectPage

logger = logging.getLogger(__name__)


class ServiceBudgetWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.project_page = ProjectPage(page)

    def configure_service_budget(
        self,
        service_name: str = "",
        service_type: str = "Recurring",
        amount: int = 500,
        duration: int = 3,
        duration_unit: str = "Months",
        start_date: str = None,
        status: str = "Active",
    ):
        """Switch to Tab 2 and configure the service budget row."""
        logger.info(f"Opening Tab 2 (Budget) and configuring service '{service_name or 'first'}'...")
        self.project_page.open_budget_tab()
        self.page.wait_for_timeout(1000)

        # Check for warning banner
        warning_banner = self.page.locator(".chakra-alert, [role='alert'], div:has-text('Project Details Incomplete')").first
        if warning_banner.count() > 0 and warning_banner.is_visible():
            banner_text = warning_banner.inner_text().strip()
            logger.error(f"Tab 2 Warning Banner Visible: {banner_text}")
            raise AssertionError(f"Project details incomplete banner present in Tab 2: {banner_text}")

        # Check services exist
        budgets = self.project_page.get_all_service_budgets()
        logger.info(f"Tab 2 Services found: {[b['service_name'] for b in budgets]}")
        assert len(budgets) > 0, "No service rows found in Tab 2 Service Budget table!"

        target_service = service_name or budgets[0]["service_name"]
        effective_date = start_date or datetime.now().strftime("%Y-%m-%d")

        result = self.project_page.configure_service_budget(
            service_name=target_service,
            service_type=service_type,
            amount=amount,
            duration=duration,
            duration_unit=duration_unit,
            start_date=effective_date,
            status=status,
        )
        self.page.wait_for_timeout(1500)
        logger.info(f"Service Budget row for '{target_service}' configured successfully.")
        return result
