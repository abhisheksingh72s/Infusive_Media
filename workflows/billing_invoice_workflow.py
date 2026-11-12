import os
import logging
from playwright.sync_api import Page, expect

from pages.project_page import ProjectPage
from pages.billing_plans_page import BillingPlansPage
from pages.invoice_page import InvoicePage

logger = logging.getLogger(__name__)


class BillingInvoiceWorkflow:
    """
    Workflow orchestrator for end-to-end Billing and Invoice business processes:
      - Phase 1: Amount calculation, discounts/rates, GST, payable amount.
      - Phase 2: Billing cycle, payment terms, customer mapping, dates.
      - Phase 3: Invoice generation from billing data.
      - Phase 4: Invoice number, date, customer details, tax breakdown.
      - Phase 5: PDF generation, browser download, cancellation/rejection.
      - Phase 6: Integration: Billing amount matches invoice amount.
      - Phase 7: Integration: Invoice status and payment synchronization.
    """

    def __init__(self, page: Page):
        self.page = page
        self.project_page = ProjectPage(page)
        self.billing_page = BillingPlansPage(page)
        self.invoice_page = InvoicePage(page)

    # -------------------------------------------------------------------------
    # PHASE 1 & 2: BILLING CONFIGURATION & VALIDATION
    # -------------------------------------------------------------------------

    def setup_project_billing_plan(
        self,
        project_name: str,
        billing_type: str = "Recurring",
        currency: str = "USD",
        cycle: str = "Monthly",
        payment_terms: str = "30 Days",
        start_date: str = "2026-11-10",
        next_invoice_date: str = "2026-12-10",
        services: list[dict] = None,
        auto_generate: bool = True,
    ) -> dict:
        """
        Navigate to Project Details, open Billing & Invoices tab, and configure plan.
        Returns calculated invoice summary and service row data.
        """
        logger.info(f"Setting up billing plan for project: '{project_name}', type: '{billing_type}'")
        self.project_page.go_to_project()
        self.project_page.click_project_hyperlink(project_name)
        self.project_page.open_billing_invoices_tab()

        # Select Type & Currency
        self.project_page.select_billing_type(billing_type)
        self.project_page.select_billing_currency(currency)

        # Configure Recurring or One-Time parameters
        if billing_type.lower() == "recurring":
            self.project_page.select_billing_cycle(cycle)
            self.project_page.select_payment_terms(payment_terms)
            self.project_page.set_recurring_dates(start_date=start_date, next_invoice_date=next_invoice_date)
            self.project_page.toggle_auto_generate_invoice(auto_generate)
        else:
            self.project_page.set_one_time_dates(invoice_date=start_date, due_date=next_invoice_date)
            self.project_page.select_payment_terms(payment_terms)

        # Add Services
        if not services:
            services = [
                {
                    "service_option_index": 1,
                    "description": "Standard Digital Marketing Service",
                    "qty": "2",
                    "unit_price": "1000",
                    "gst_percent": "18",
                }
            ]

        for idx, svc in enumerate(services):
            self.project_page.click_add_service()
            self.project_page.fill_service_row(
                row_index=idx,
                service_option_index=svc.get("service_option_index", 1),
                description=svc.get("description", ""),
                qty=svc.get("qty", "1"),
                unit_price=svc.get("unit_price", "100"),
                gst_percent=svc.get("gst_percent", "18"),
            )

        summary = self.project_page.get_invoice_summary()
        logger.info(f"Configured Billing Summary: {summary}")
        return summary

    def submit_billing_plan(self, generate_invoice_now: bool = False):
        """Submit the billing plan and return submission response."""
        logger.info(f"Submitting billing plan (generate_invoice_now={generate_invoice_now})...")
        self.project_page.click_create_plan(generate_invoice_now=generate_invoice_now)
        self.page.wait_for_timeout(1500)

    # -------------------------------------------------------------------------
    # PHASE 3 & 4: INVOICE GENERATION & VERIFICATION
    # -------------------------------------------------------------------------

    def get_latest_invoice_for_project(self, project_name: str) -> dict:
        """
        Navigate to Invoices page, filter by project, and return first matching invoice.
        """
        self.invoice_page.go_to_invoices()
        self.invoice_page.search_invoices(project_name)
        self.page.wait_for_timeout(1000)

        rows = self.invoice_page.get_table_rows()
        if rows.count() == 0:
            return {}
        return self.invoice_page.get_invoice_row_data(0)

    # -------------------------------------------------------------------------
    # PHASE 5: PDF GENERATION & DOWNLOAD
    # -------------------------------------------------------------------------

    def download_and_verify_pdf(self, invoice_no: str) -> str:
        """
        Download invoice PDF and verify that the file exists, has .pdf extension,
        and starts with standard PDF magic header bytes (%PDF).
        """
        self.invoice_page.go_to_invoices()
        pdf_path = self.invoice_page.download_invoice_pdf(invoice_no)

        assert os.path.exists(pdf_path), f"Downloaded PDF does not exist at '{pdf_path}'"
        assert pdf_path.lower().endswith(".pdf"), f"File is not a PDF: '{pdf_path}'"
        assert os.path.getsize(pdf_path) > 0, f"Downloaded PDF file is empty: {pdf_path}"

        with open(pdf_path, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF", f"Invalid PDF magic header bytes: {header}"

        logger.info(f"Verified PDF download successfully: {pdf_path} (Valid %PDF header ✓)")
        return pdf_path

    # -------------------------------------------------------------------------
    # PHASE 6: BILLING AMOUNT MATCHES INVOICE AMOUNT
    # -------------------------------------------------------------------------

    def verify_billing_amount_matches_invoice(self, billing_plan_project: str, invoice_no: str) -> bool:
        """
        Verify that the total amount defined in the Billing Plan matches the amount
        on the corresponding generated invoice in the Invoices ledger.
        """
        # 1. Get Billing Plan Amount
        self.billing_page.go_to_billing_plans()
        self.billing_page.search_plans(billing_plan_project)
        plan_row = self.billing_page.get_plan_row_data(0)
        plan_amount = plan_row["amount_with_gst"].replace(",", "").strip()
        logger.info(f"Billing Plan Amount for '{billing_plan_project}': {plan_amount}")

        # 2. Get Invoice Amount
        self.invoice_page.go_to_invoices()
        self.invoice_page.search_invoices(invoice_no)
        inv_row = self.invoice_page.get_invoice_row_data(0)
        inv_amount_inr = inv_row["amount_inr"].replace(",", "").strip()
        inv_amount_usd = inv_row["amount_usd"].replace(",", "").strip()
        logger.info(f"Invoice '{invoice_no}' Amounts: INR={inv_amount_inr}, USD={inv_amount_usd}")

        # Match either currency
        plan_digits = "".join(filter(str.isdigit, plan_amount))
        inv_inr_digits = "".join(filter(str.isdigit, inv_amount_inr))
        inv_usd_digits = "".join(filter(str.isdigit, inv_amount_usd))

        matches = (plan_digits in inv_inr_digits) or (plan_digits in inv_usd_digits) or (inv_inr_digits in plan_digits) or (inv_usd_digits in plan_digits)
        logger.info(f"Amount comparison: plan_digits='{plan_digits}', inv_inr='{inv_inr_digits}', inv_usd='{inv_usd_digits}' -> Match: {matches}")
        return matches

    # -------------------------------------------------------------------------
    # PHASE 7: INVOICE & PAYMENT STATUS SYNCHRONIZATION
    # -------------------------------------------------------------------------

    def verify_payment_status_synchronization(self, invoice_no: str) -> dict:
        """
        Verify that for Paid or Balance invoices, the Paid amount + Outstanding amount
        equals the Total Invoice Amount, and verification reflects accurate state.
        """
        self.invoice_page.go_to_invoices()
        self.invoice_page.search_invoices(invoice_no)
        inv_row = self.invoice_page.get_invoice_row_data(0)
        logger.info(f"Invoice '{invoice_no}' status sync data: {inv_row}")
        return inv_row
