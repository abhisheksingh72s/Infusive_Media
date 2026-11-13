"""
End-to-End Test: Lead -> Won -> Project Configuration -> Billing Plan -> API Trigger -> Invoice Generation
=============================================================================================================
Chain of Modular Workflows:
  - workflows.lead.LeadWorkflow
  - workflows.project.ProjectDetailsWorkflow (Tab 1)
  - workflows.project.ServiceBudgetWorkflow (Tab 2)
  - workflows.project.ProjectBillingWorkflow (Tab 5)
  - workflows.billing.BillingSchedulerWorkflow
  - workflows.invoice.InvoiceWorkflow
"""

import os
import pathlib
import pytest
from playwright.sync_api import Page

from workflows.lead import LeadWorkflow
from workflows.project import (
    ProjectDetailsWorkflow,
    ServiceBudgetWorkflow,
    ProjectBillingWorkflow,
)
from workflows.billing import BillingSchedulerWorkflow
from workflows.invoice import InvoiceWorkflow


@pytest.mark.ui
def test_e2e_lead_won_to_recurring_invoice_chain(page: Page):
    """
    E2E Event Chain:
      Phase 1: Create Quick Lead (Pre-Sales role).
      Phase 2: BDM accepts lead from /my-leads & marks status as 'Won'.
      Phase 3: Login as Admin -> Configure Project Tab 1 (Details: Services, Currency, Budget, Duration, Start Date).
      Phase 4: Configure Project Tab 2 (Budget: Recurring service budget).
      Phase 5: Configure Project Tab 5 (Billing & Invoices) with Today's Date & Save via 'Create Plan'.
      Phase 6: Trigger Developer's Scheduler Test API.
      Phase 7: Validate generated Invoice in Master Invoices ledger (/invoice-list-page) and /allBillingPlans.
    """
    shots_dir = pathlib.Path("screenshots")
    shots_dir.mkdir(exist_ok=True)

    # 1. Instantiate modular workflows
    lead_flow = LeadWorkflow(page)
    tab1_flow = ProjectDetailsWorkflow(page)
    tab2_flow = ServiceBudgetWorkflow(page)
    tab5_flow = ProjectBillingWorkflow(page)
    scheduler_flow = BillingSchedulerWorkflow(page)
    invoice_flow = InvoiceWorkflow(page)

    # -------------------------------------------------------------------------
    # Phase 1: Pre-Sales creates Quick Lead
    # -------------------------------------------------------------------------
    lead = lead_flow.create_quick_lead(country="United States")
    company_name = lead["company_name"]
    assigned_bdm = lead["assigned_to"]
    page.screenshot(path=str(shots_dir / "phase1_lead_created.png"))

    # -------------------------------------------------------------------------
    # Phase 2: BDM accepts lead & converts to Won
    # -------------------------------------------------------------------------
    won_status = lead_flow.mark_lead_won(company_name, assigned_bdm)
    assert won_status == "Won", f"Expected Lead Status 'Won', got '{won_status}'"
    page.screenshot(path=str(shots_dir / "phase2_lead_won.png"))

    # -------------------------------------------------------------------------
    # Switch to Admin
    # -------------------------------------------------------------------------
    admin_email = os.environ.get("EMAIL")
    admin_pass = os.environ.get("PASSWORD")
    if not admin_email or not admin_pass:
        raise ValueError("Admin credentials (EMAIL and PASSWORD) must be defined in .env / environment.")
    lead_flow.login_page.logout()
    lead_flow.login_page.login(admin_email, admin_pass)
    lead_flow.login_page.wait_for_dashboard()

    # -------------------------------------------------------------------------
    # Phase 3: Project Tab 1 (Details)
    # -------------------------------------------------------------------------
    tab1_data = tab1_flow.configure_details(
        company_name=company_name,
        currency="USD",
        status="Active",
        services=["PPC", "Meta Ads"],
        monthly_budget="500",
        duration="3",
    )
    page.screenshot(path=str(shots_dir / "phase3_tab1_details_saved.png"))

    # -------------------------------------------------------------------------
    # Phase 4: Project Tab 2 (Service Budget)
    # -------------------------------------------------------------------------
    tab2_flow.configure_service_budget(service_type="Recurring", amount=500, duration=3)
    page.screenshot(path=str(shots_dir / "phase4_tab2_budget_configured.png"))

    # -------------------------------------------------------------------------
    # Phase 5: Project Tab 5 (Billing & Invoices) Recurring Plan
    # -------------------------------------------------------------------------
    plan = tab5_flow.setup_recurring_billing_plan(
        cycle="Monthly",
        currency="USD",
        unit_price="500",
        generate_invoice_now=True,
    )
    page.screenshot(path=str(shots_dir / "phase5_tab5_plan_created.png"))

    # -------------------------------------------------------------------------
    # Phase 6: Scheduler Trigger
    # -------------------------------------------------------------------------
    api_result = scheduler_flow.trigger_scheduler_job(
        project_id=plan.get("project_id"),
        config_id=plan.get("config_id"),
        date_str=plan.get("today_str"),
    )

    # -------------------------------------------------------------------------
    # Phase 7: Verification in Invoices Ledger & Billing Plans Ledger
    # -------------------------------------------------------------------------
    inv_data = invoice_flow.verify_invoice_in_ledger(company_name, expected_status="Pending")
    page.screenshot(path=str(shots_dir / "phase6_invoice_ledger.png"))

    scheduler_flow.verify_plan_in_ledger(company_name, expected_invoices=1)
    page.screenshot(path=str(shots_dir / "phase7_billing_plans_ledger.png"))

    # Print final verified evidence
    invoice_no = inv_data.get("invoice_number") or api_result.get("invoiceNumber")
    invoice_id = inv_data.get("invoice_id") or api_result.get("invoiceId")
    total_amt = inv_data.get("amount_usd") or inv_data.get("amount_inr") or api_result.get("totalAmount")

    print("\n" + "=" * 60)
    print("E2E LEAD TO RECURRING INVOICE VERIFIED EVIDENCE:")
    print(f"  Company Name:   {company_name}")
    print(f"  Invoice Number: {invoice_no}")
    print(f"  Invoice ID:     {invoice_id}")
    print(f"  Total Amount:   {total_amt}")
    print(f"  Status:         {inv_data.get('status', 'Pending')}")
    print("=" * 60 + "\n")

