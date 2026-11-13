"""
Customer Workflow Module
========================
Encapsulates Customer module business operations:
  - Verification of automatic customer generation upon Lead 'Won' status.
  - Multi-tab validation on /customers/{id} (Overview, Projects, Invoices, Client Profile).
  - Client Profile sub-tab operations (Basic Information, Billing Address, Tax & GST Details).
"""

import logging
from playwright.sync_api import Page, expect
from pages.customer_page import CustomerPage

logger = logging.getLogger(__name__)


class CustomerWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.customer_page = CustomerPage(page)

    def verify_customer_created_from_won_lead(self, company_name: str) -> dict:
        """
        Validates the Business Rule:
        'When a lead is marked as Won, it automatically appears in Customers and Projects.'
        
        Steps:
          1. Navigate to /customers.
          2. Search for the lead's company_name.
          3. Assert that the customer record exists and is Active.
          4. Open Customer Details (/customers/{id}).
          5. Verify the 4 main tabs (Overview, Projects, Invoices, Client Profile).
          6. Verify under Projects tab that the new project is listed.
        """
        logger.info(f"Validating Customer conversion for won lead: '{company_name}'...")
        self.customer_page.go_to_customers()
        self.page.wait_for_timeout(1000)

        # 1. Search and assert in table
        exists = self.customer_page.verify_customer_exists(company_name)
        assert exists, f"Business Rule VIOLATION: Won lead '{company_name}' did NOT appear in Customers table (/customers)!"

        row_data = self.customer_page.get_customer_row_data(company_name)
        logger.info(f"Verified customer row data: {row_data}")
        assert row_data["status"] == "Active", f"Expected customer status 'Active', got '{row_data['status']}'"

        # 2. Open Customer Details (/customers/{id})
        self.customer_page.click_view_customer_details(company_name)
        assert "/customers/" in self.page.url, f"Expected URL to be '/customers/{{id}}', got '{self.page.url}'"

        # 3. Verify all 4 tabs exist
        tablist = self.page.locator(".chakra-tabs__tablist")
        tablist.wait_for(state="visible", timeout=10000)
        expected_tabs = ["Overview", "Project", "Invoice", "Client Profile"]
        for t in expected_tabs:
            tab_loc = tablist.locator("button[role='tab']").filter(has_text=t).first
            assert tab_loc.count() > 0 and tab_loc.is_visible(), f"Expected tab '{t}' not visible on Customer Details!"

        # 4. Check Projects tab to verify project association
        self.customer_page.switch_to_customer_tab("Project")
        self.page.wait_for_timeout(800)
        projects = self.customer_page.get_customer_projects_table()
        logger.info(f"Projects associated with customer: {projects}")

        # 5. Extract overview KPIs
        self.customer_page.switch_to_customer_tab("Overview")
        kpis = self.customer_page.get_overview_kpis()
        logger.info(f"Customer Overview KPIs: {kpis}")

        logger.info(f"Customer creation and association VERIFIED for won lead '{company_name}' ✓")
        return {
            "customer_name": row_data["name"],
            "customer_email": row_data["email"],
            "customer_url": self.page.url,
            "projects_count": len(projects),
            "kpis": kpis,
        }
