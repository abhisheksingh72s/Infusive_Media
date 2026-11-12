import os
import logging
from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)


class BillingPlansPage:
    """
    Page Object Model for the Billing Plans module (/allBillingPlans).
    Provides methods for:
      - Navigation via sidebar or direct URL.
      - Reading KPI metric cards (Plans, Active, Due for invoice, Recurring).
      - Searching and applying filters (Customer, Billing Type, Status, Due toggle).
      - Reading table rows, headers, and column details.
      - Toggling plan status (Stop / Resume).
      - Opening plan details.
    """

    def __init__(self, page: Page):
        self.page = page

    def get_base_url(self) -> str:
        base_url = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")
        return base_url.replace("/login", "").rstrip("/")

    # -------------------------------------------------------------------------
    # NAVIGATION
    # -------------------------------------------------------------------------

    def go_to_billing_plans(self):
        """Navigate to Billing Plans module via direct URL or sidebar."""
        logger.info("Navigating to Billing Plans module...")
        base_url = self.get_base_url()
        target_url = f"{base_url}/allBillingPlans"
        try:
            self.page.goto(target_url, wait_until="domcontentloaded")
            self.page.wait_for_url("**/allBillingPlans*", timeout=20000)
        except Exception as e:
            logger.warning(f"Direct goto failed: {e}. Trying sidebar link...")
            billing_link = self.page.locator("a[href*='BillingPlans'], a:has-text('Billing')").first
            if billing_link.count() > 0 and billing_link.is_visible():
                billing_link.click()
                self.page.wait_for_url("**/allBillingPlans*", timeout=20000)

        self.page.wait_for_timeout(1500)
        try:
            self.page.locator("table tbody tr, table, div[role='table']").first.wait_for(
                state="visible", timeout=20000
            )
        except Exception:
            pass
        logger.info(f"On Billing Plans page. Current URL: {self.page.url}")

    # -------------------------------------------------------------------------
    # KPI METRICS
    # -------------------------------------------------------------------------

    def get_kpi_summary_metrics(self) -> dict:
        """
        Extract metrics from top KPI cards:
        - plans_filtered
        - active
        - due_for_invoice
        - recurring
        """
        metrics = {}
        labels = [
            ("plans_filtered", "Plans (filtered)"),
            ("active", "Active"),
            ("due_for_invoice", "Due for invoice"),
            ("recurring", "Recurring"),
        ]
        for key, text_label in labels:
            try:
                label_el = self.page.locator(f"p:has-text('{text_label}')").first
                if label_el.is_visible():
                    parent = label_el.locator("..")
                    p_tags = parent.locator("p").all()
                    if len(p_tags) >= 2:
                        val = p_tags[1].inner_text().strip()
                        metrics[key] = val
                    else:
                        for line in parent.inner_text().split("\n"):
                            clean = line.strip()
                            if clean.isdigit():
                                metrics[key] = clean
                                break
            except Exception as e:
                logger.warning(f"Could not extract KPI '{key}': {e}")

        logger.info(f"Billing Plans KPI metrics: {metrics}")
        return metrics

    # -------------------------------------------------------------------------
    # FILTERS & SEARCH
    # -------------------------------------------------------------------------

    def search_plans(self, query: str):
        """Search billing plans by project or customer name."""
        logger.info(f"Searching billing plans for: '{query}'")
        search_box = self.page.locator("input[placeholder*='Project or customer'], input[placeholder*='Search']").first
        search_box.fill(query)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1000)

    def filter_by_customer(self, customer_name: str):
        """Filter table by customer dropdown."""
        logger.info(f"Filtering by customer: '{customer_name}'")
        select = self.page.locator("label:has-text('Customer') + div select, select:has-text('All customers')").first
        select.select_option(label=customer_name)
        self.page.wait_for_timeout(1000)

    def filter_by_billing_type(self, billing_type: str):
        """Filter table by Billing type dropdown (e.g. 'Recurring', 'One-Time', 'All types')."""
        logger.info(f"Filtering by billing type: '{billing_type}'")
        select = self.page.locator("label:has-text('Billing type') + div select, select:has-text('All types')").first
        select.select_option(label=billing_type)
        self.page.wait_for_timeout(1000)

    def filter_by_status(self, status: str):
        """Filter table by Status dropdown (e.g. 'Active', 'Inactive', 'All')."""
        logger.info(f"Filtering by status: '{status}'")
        select = self.page.locator("label:has-text('Status') + div select, select:has-text('All')").first
        select.select_option(label=status)
        self.page.wait_for_timeout(1000)

    def sort_by(self, sort_option: str):
        """Sort billing plans by dropdown (e.g. 'Newest first', 'Next invoice (soonest)', etc.)."""
        logger.info(f"Sorting billing plans by: '{sort_option}'")
        select = self.page.locator("label:has-text('Sort by') + div select").first
        select.select_option(label=sort_option)
        self.page.wait_for_timeout(1000)

    def toggle_due_for_invoice_only(self):
        """Toggle 'Only plans due for invoice' switch."""
        logger.info("Toggling 'Only plans due for invoice' switch...")
        switch = self.page.locator("label.chakra-switch, input[type='checkbox']").first
        switch.click()
        self.page.wait_for_timeout(1000)

    def open_more_filters(self):
        """Expand the 'More filters' collapsible section if not already open."""
        collapse = self.page.locator("div.chakra-collapse").first
        if not collapse.is_visible():
            btn = self.page.locator("button:has-text('More filters')").first
            btn.click()
            self.page.wait_for_timeout(500)

    def filter_by_billing_cycle(self, billing_cycle: str):
        """Filter by billing cycle in More filters (e.g. 'Monthly', 'Weekly', 'Quarterly', 'Yearly')."""
        self.open_more_filters()
        logger.info(f"Filtering by billing cycle: '{billing_cycle}'")
        select = self.page.locator("label:has-text('Billing cycle') + div select").first
        select.select_option(label=billing_cycle)
        self.page.wait_for_timeout(1000)

    def filter_by_currency(self, currency: str):
        """Filter by currency in More filters (e.g. 'INR', 'USD', 'EUR')."""
        self.open_more_filters()
        logger.info(f"Filtering by currency: '{currency}'")
        select = self.page.locator("label:has-text('Currency') + div select").first
        select.select_option(label=currency)
        self.page.wait_for_timeout(1000)

    def filter_by_auto_generate(self, auto_status: str):
        """Filter by auto-generate in More filters (e.g. 'On', 'Off', 'All')."""
        self.open_more_filters()
        logger.info(f"Filtering by auto-generate: '{auto_status}'")
        select = self.page.locator("label:has-text('Auto-generate') + div select").first
        select.select_option(label=auto_status)
        self.page.wait_for_timeout(1000)

    # -------------------------------------------------------------------------
    # PAGINATION
    # -------------------------------------------------------------------------

    def get_pagination_info(self) -> str:
        """Return pagination summary text, e.g. 'Showing 1–10 of 36'."""
        info_el = self.page.locator("p:has-text('Showing')").first
        if info_el.is_visible():
            return info_el.inner_text().strip()
        return ""

    def change_page_size(self, size_option: str = "25 / page"):
        """Change the items per page dropdown (e.g. '10 / page', '25 / page')."""
        logger.info(f"Changing page size to: '{size_option}'")
        select = self.page.locator("select:has-text('/ page')").first
        select.select_option(label=size_option)
        self.page.wait_for_timeout(1000)

    # -------------------------------------------------------------------------
    # TABLE & ROW DATA
    # -------------------------------------------------------------------------

    def get_table_headers(self) -> list[str]:
        """Return table header column names."""
        headers = self.page.locator("table thead th").all()
        return [th.inner_text().strip() for th in headers if th.is_visible()]

    def get_table_rows(self):
        """Return locator for table body rows."""
        return self.page.locator("table tbody tr")

    def get_plan_row_data(self, row_index: int = 0) -> dict:
        """Extract structured data from a specific row."""
        rows = self.get_table_rows()
        row = rows.nth(row_index)
        cells = [td.inner_text().strip().replace("\n", " ") for td in row.locator("td").all()]
        if len(cells) < 11:
            return {}
        has_due = row.locator("td:nth-child(8) span:has-text('Due')").count() > 0
        return {
            "s_no": cells[0],
            "customer": cells[1],
            "project": cells[2],
            "type": cells[3],
            "currency": cells[4],
            "amount_with_gst": cells[5],
            "start": cells[6],
            "next_invoice": cells[7],
            "has_due": has_due,
            "auto": cells[8],
            "status": cells[9],
            "invoices": cells[10],
        }

    def find_plan_row_by_project(self, project_name: str):
        """Find the table row locator matching a specific project name."""
        rows = self.get_table_rows().all()
        for r in rows:
            if project_name.lower() in r.locator("td:nth-child(3)").inner_text().lower():
                return r
        return None

    # -------------------------------------------------------------------------
    # ACTIONS: STOP, RESUME, OPEN
    # -------------------------------------------------------------------------

    def toggle_plan_status(self, project_name: str, target_action: str = "Stop") -> bool:
        """
        Click 'Stop' or 'Resume' on a plan row.
        target_action: 'Stop' (to deactivate) or 'Resume' (to reactivate).
        """
        logger.info(f"Attempting to '{target_action}' plan for project: '{project_name}'")
        row = self.find_plan_row_by_project(project_name)
        if not row:
            raise ValueError(f"Project '{project_name}' not found in Billing Plans table.")

        btn = row.locator(f"button:has-text('{target_action}')").first
        if not btn.is_visible():
            logger.warning(f"Button '{target_action}' not visible on row for project '{project_name}'. Current row text: {row.inner_text()}")
            return False

        btn.click()
        self.page.wait_for_timeout(1500)

        # Confirm any confirmation modal if present
        confirm_btn = self.page.locator("button:has-text('Confirm'), button:has-text('Yes'), button:has-text('Save')").first
        if confirm_btn.count() > 0 and confirm_btn.is_visible():
            confirm_btn.click()
            self.page.wait_for_timeout(1000)

        logger.info(f"Action '{target_action}' executed successfully on '{project_name}'.")
        return True

    def open_plan_details(self, project_name: str):
        """Click the edit icon or link to open the billing plan configuration."""
        logger.info(f"Opening billing plan details for project: '{project_name}'")
        row = self.find_plan_row_by_project(project_name)
        if not row:
            raise ValueError(f"Project '{project_name}' not found in Billing Plans table.")

        open_btn = row.locator("button[aria-label='Edit billing plan'], button:has-text('Open'), a").first
        open_btn.click()
        self.page.wait_for_timeout(1500)

    # -------------------------------------------------------------------------
    # INVOICES COLUMN & UPDATE BILLING PLAN MODAL
    # -------------------------------------------------------------------------

    def get_invoices_cell(self, row_index: int = 0, project_name: str = None):
        """Return the 'Invoices' column cell (column 11) for a row."""
        if project_name:
            row = self.find_plan_row_by_project(project_name)
            if not row:
                raise ValueError(f"Project '{project_name}' not found in Billing Plans table.")
        else:
            rows = self.get_table_rows()
            row = rows.nth(row_index)
        return row.locator("td:nth-child(11)")

    def open_edit_billing_plan_modal(self, row_index: int = 0, project_name: str = None):
        """
        Click the edit icon (aria-label='Edit billing plan') on the billing plan row.
        This opens the 'Update Billing Plan' modal dialog.
        """
        logger.info(f"Opening 'Update Billing Plan' modal (row_index={row_index}, project='{project_name}')...")
        if project_name:
            row = self.find_plan_row_by_project(project_name)
            if not row:
                raise ValueError(f"Project '{project_name}' not found in Billing Plans table.")
        else:
            rows = self.get_table_rows()
            row = rows.nth(row_index)

        # The edit icon button has aria-label="Edit billing plan" (Col 12 adjacent to INVOICES)
        edit_btn = row.locator("button[aria-label='Edit billing plan'], td:nth-child(12) button, button:has(svg)").first
        if not edit_btn.is_visible():
            raise ValueError(f"Edit button not visible on row {row_index}.")

        edit_btn.click()
        self.page.wait_for_timeout(1000)

        modal = self.page.locator("section[role='dialog'], div.chakra-modal__content").first
        modal.wait_for(state="visible", timeout=10000)
        logger.info("Update Billing Plan modal is visible.")
        return modal

    def get_edit_modal_details(self) -> dict:
        """Extract structured details from the open 'Update Billing Plan' modal."""
        modal = self.page.locator("section[role='dialog'], div.chakra-modal__content").first
        if not modal.is_visible():
            raise RuntimeError("Update Billing Plan modal is not open.")

        header = modal.locator("header.chakra-modal__header, [id*='header']").first.inner_text().strip()
        title = modal.locator("h2.chakra-heading").first.inner_text().strip()

        # Billing Type (One-Time / Recurring)
        checked_radio = modal.locator("label.chakra-radio[data-checked] .chakra-radio__label, input[type='radio']:checked + span + span").first
        billing_type = checked_radio.inner_text().strip() if checked_radio.count() > 0 else ""

        # Currency
        currency_select = modal.locator("select[name='currencyCode']").first
        currency = currency_select.input_value() if currency_select.count() > 0 else ""

        # Dates
        start_date = modal.locator("input[name='startDate']").first.input_value()
        next_invoice_date = modal.locator("input[name='nextInvoiceDate']").first.input_value()

        # Services count
        service_rows = modal.locator("table tbody tr").all()
        services = []
        for r in service_rows:
            service_select = r.locator("select").first
            svc_name = service_select.locator("option:checked").inner_text().strip() if service_select.count() > 0 else ""
            desc = r.locator("textarea").first.input_value() if r.locator("textarea").count() > 0 else ""
            qty = r.locator("input[type='number']").nth(0).input_value() if r.locator("input[type='number']").count() > 0 else ""
            unit_price = r.locator("input[type='number']").nth(1).input_value() if r.locator("input[type='number']").count() > 1 else ""
            gst_select = r.locator("select").nth(1) if r.locator("select").count() > 1 else None
            gst_rate = gst_select.locator("option:checked").inner_text().strip() if gst_select else ""
            total_td = r.locator("td[data-is-numeric='true'], td:nth-child(7)").first
            total_amt = total_td.inner_text().strip() if total_td.count() > 0 else ""
            services.append({
                "service": svc_name,
                "description": desc,
                "qty": qty,
                "unit_price": unit_price,
                "gst_rate": gst_rate,
                "total": total_amt,
            })

        # Summary amounts
        subtotal_el = modal.locator("p:has-text('Subtotal') + p").first
        subtotal = subtotal_el.inner_text().strip() if subtotal_el.is_visible() else ""

        total_gst_el = modal.locator("p:has-text('Total GST') + p").first
        total_gst = total_gst_el.inner_text().strip() if total_gst_el.is_visible() else ""

        total_amount_el = modal.locator("p:has-text('Total Amount') + p").first
        total_amount = total_amount_el.inner_text().strip() if total_amount_el.is_visible() else ""

        # Auto-generate switch
        auto_switch = modal.locator("label.chakra-switch input[type='checkbox']").first
        auto_generate = auto_switch.is_checked() if auto_switch.count() > 0 else False

        return {
            "header": header,
            "title": title,
            "billing_type": billing_type,
            "currency": currency,
            "start_date": start_date,
            "next_invoice_date": next_invoice_date,
            "services": services,
            "subtotal": subtotal,
            "total_gst": total_gst,
            "total_amount": total_amount,
            "auto_generate": auto_generate,
        }

    def close_edit_modal(self):
        """Close the 'Update Billing Plan' modal via close button, Cancel, or Escape."""
        logger.info("Closing 'Update Billing Plan' modal...")
        modal = self.page.locator("section[role='dialog'], div.chakra-modal__content").first
        if modal.is_visible():
            close_btn = modal.locator("button.chakra-modal__close-btn, button[aria-label='Close']").first
            if close_btn.is_visible():
                close_btn.click()
            else:
                cancel_btn = modal.locator("button:has-text('Cancel')").first
                if cancel_btn.is_visible():
                    cancel_btn.click()
                else:
                    self.page.keyboard.press("Escape")
        else:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(1000)

    def submit_update_plan(self, generate_invoice_now: bool = False):
        """Submit the update billing plan form."""
        if generate_invoice_now:
            logger.info("Submitting via 'Update Plan & Generate Invoice Now'...")
            btn = self.page.locator("button:has-text('Update Plan & Generate Invoice Now')").first
        else:
            logger.info("Submitting via 'Update Plan'...")
            btn = self.page.locator("button:has-text('Update Plan')").first
        btn.click()
        self.page.wait_for_timeout(1500)
