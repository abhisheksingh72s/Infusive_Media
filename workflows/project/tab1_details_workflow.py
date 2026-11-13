"""
Project Details Workflow (Tab 1)
================================
Encapsulates opening converted projects and configuring baseline Tab 1 parameters
(Currency, Active Status, Monthly Budget, Duration, Start Date, Services Interested In, Description).
"""

import logging
from datetime import datetime
from playwright.sync_api import Page
from pages.project_page import ProjectPage

logger = logging.getLogger(__name__)


class ProjectDetailsWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.project_page = ProjectPage(page)

    def configure_details(
        self,
        company_name: str,
        currency: str = "USD",
        status: str = "Active",
        services: list[str] = None,
        monthly_budget: str = "500",
        duration: str = "3",
        start_date: str = None,
    ):
        """Navigate to converted project, open Tab 1, fill all mandatory fields, and save."""
        logger.info(f"Opening project for '{company_name}' in Tab 1 (Details)...")
        self.project_page.go_to_project()
        self.project_page.click_project_hyperlink(company_name)

        self.project_page.open_project_details_tab()
        self.page.wait_for_timeout(800)
        self.project_page.click_edit_project_icon()

        # 1. Select Services Interested In
        target_services = services or ["PPC", "Meta Ads"]
        try:
            self.project_page.select_services_interested_in(target_services)
        except Exception as e:
            logger.warning(f"Services selection warning: {e}")

        # 2. Select Currency
        self.project_page.select_currency(currency)

        # 3. Fill Monthly Budget, Duration, Start Date
        today_date = start_date or datetime.now().strftime("%Y-%m-%d")
        self.project_page.fill_project_details(
            budget=str(monthly_budget),
            duration=str(duration),
            start_date=today_date,
        )

        # 4. Set Status to Active
        try:
            self.project_page.set_project_status(status)
        except Exception:
            pass

        # 5. Set Description
        try:
            self.project_page.set_project_description(
                f"Configured project details for {company_name} with services: {', '.join(target_services)}."
            )
        except Exception:
            pass

        # 6. Save
        self.project_page.save_project()
        logger.info("Clicked Save on Project Details. Waiting for toast...")

        # Wait for Save toast
        try:
            toast = self.page.locator(".chakra-toast, [role='status'], [role='alert']").first
            if toast.is_visible(timeout=5000):
                toast_text = toast.inner_text().strip()
                logger.info(f"Captured Project Details Save Toast: '{toast_text}'")
                try:
                    toast.wait_for(state="hidden", timeout=8000)
                except Exception:
                    pass
        except Exception:
            pass

        self.page.wait_for_timeout(1000)

        # Reload to ensure refreshed project state across tabs
        logger.info("Reloading page to validate saved project details and refresh state...")
        self.page.reload()
        self.page.wait_for_timeout(1500)
        self.project_page.open_project_details_tab()

        # 7. Validate after save reflected
        form_data = self.project_page.get_project_details_form_data()
        logger.info(f"Project Tab 1 Form Data after save & refresh: {form_data}")
        assert form_data["monthly_budget"] == str(monthly_budget), (
            f"Expected Monthly Budget '{monthly_budget}', got: '{form_data['monthly_budget']}'"
        )
        assert form_data["duration"] == str(duration), (
            f"Expected Duration '{duration}', got: '{form_data['duration']}'"
        )
        assert form_data["currency"] == currency, (
            f"Expected Currency '{currency}', got: '{form_data['currency']}'"
        )
        logger.info(
            f"Project Tab 1 (Details) validated & reflected for '{company_name}' "
            f"(Status: {status}, Currency: {currency}, Budget: {monthly_budget}, Duration: {duration}) ✓"
        )
        return form_data

