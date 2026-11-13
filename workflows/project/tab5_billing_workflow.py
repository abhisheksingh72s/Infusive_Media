"""
Project Billing Workflow (Tab 5)
================================
Encapsulates configuring billing schedules (Recurring / One-Time), line items,
taxes, auto-generate toggles, and saving the plan.
"""

import logging
from datetime import datetime
from playwright.sync_api import Page
from pages.project_page import ProjectPage

logger = logging.getLogger(__name__)


class ProjectBillingWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.project_page = ProjectPage(page)

    def setup_recurring_billing_plan(
        self,
        cycle: str = "Weekly",
        currency: str = "USD",
        unit_price: str = "500",
        qty: str = "1",
        start_date: str = None,
        next_invoice_date: str = None,
        auto_generate: bool = True,
        generate_invoice_now: bool = True,
    ) -> dict:
        """
        Open Tab 5, configure recurring plan, add service, and save via 'Create Plan'
        or 'Create Plan & Generate Invoice Now'.
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        effective_start = start_date or today_str
        effective_next = next_invoice_date or today_str

        logger.info(f"Setting up Tab 5 Recurring Plan (Cycle: {cycle}, Currency: {currency}, Next Date: {effective_next}, GenerateNow: {generate_invoice_now})...")
        # Ensure fresh project data and budget state from Tab 1 & Tab 2 saves
        logger.info("Reloading page to synchronize project duration and service budget into Tab 5...")
        self.page.reload()
        self.page.wait_for_timeout(1500)
        self.project_page.open_billing_invoices_tab()
        self.page.wait_for_timeout(1000)

        self.project_page.select_billing_type("Recurring")
        self.project_page.select_billing_currency(currency)
        self.project_page.select_billing_cycle(cycle)
        self.project_page.set_recurring_dates(start_date=effective_start, next_invoice_date=effective_next)
        self.project_page.toggle_auto_generate_invoice(enable=auto_generate)

        # Add Service Row
        self.project_page.click_add_service()
        self.project_page.fill_service_row(
            row_index=0,
            service_name="Meta Ads",
            service_option_index=1,
            description=f"{cycle} Retainer Service",
            qty=qty,
            unit_price=unit_price,
            gst_percent="18",
        )

        captured_config_id = None
        captured_project_id = None

        def on_response(response):
            nonlocal captured_config_id, captured_project_id
            if response.request.method in ("POST", "PUT"):
                try:
                    import re
                    match = re.search(r"/api/projects/(\d+)/billing", response.url)
                    if match:
                        captured_project_id = int(match.group(1))
                        logger.info(f"Captured Project ID: {captured_project_id}")

                    b = response.json()
                    logger.info(f"API Response [{response.status}] from {response.url}: {b}")
                    if isinstance(b, dict):
                        cfg_id = (
                            b.get("id")
                            or b.get("configId")
                            or b.get("billingConfigurationId")
                            or (b.get("data") if isinstance(b.get("data"), int) else None)
                            or (b.get("data", {}).get("id") if isinstance(b.get("data"), dict) else None)
                        )
                        if cfg_id:
                            captured_config_id = cfg_id
                            logger.info(f"Captured Billing Configuration ID: {captured_config_id}")
                except Exception:
                    pass

        self.page.on("response", on_response)

        # Click Create Plan
        logger.info(f"Submitting plan (generate_invoice_now={generate_invoice_now})...")
        self.project_page.click_create_plan(generate_invoice_now=generate_invoice_now)

        # Capture toast notification
        try:
            toast = self.page.locator(".chakra-toast, [role='status'], [role='alert']").first
            if toast.is_visible(timeout=5000):
                toast_msg = toast.inner_text().strip()
                logger.info(f"Captured Tab 5 Plan Submission Toast: '{toast_msg}'")
        except Exception:
            pass

        self.page.wait_for_timeout(2000)

        return {
            "config_id": captured_config_id,
            "project_id": captured_project_id,
            "today_str": today_str,
            "cycle": cycle,
            "currency": currency,
            "amount": str(float(unit_price) * float(qty)),
            "generate_invoice_now": generate_invoice_now,
        }
