import os
import logging
from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)


class InvoicePage:
    """
    Page Object Model for the Invoices module (/invoice-list-page).
    Provides methods for:
      - Navigation via sidebar or direct URL.
      - Reading KPI metric cards (Due Today, Overdue, Due in Next 7 Days, Total Outstanding, Collected This Month).
      - Switching currency (INR / USD).
      - Status filter tabs (All, Pending, Paid, Balance, Overpay, Rejected).
      - Searching by invoice number, customer, or project.
      - Extracting table rows, header columns, and detailed row data.
    """

    def __init__(self, page: Page):
        self.page = page

    def get_base_url(self) -> str:
        base_url = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")
        return base_url.replace("/login", "").rstrip("/")

    # -------------------------------------------------------------------------
    # NAVIGATION
    # -------------------------------------------------------------------------

    def go_to_invoices(self):
        """Navigate to Invoices module via direct URL or sidebar."""
        logger.info("Navigating to Invoices module...")
        base_url = self.get_base_url()
        target_url = f"{base_url}/invoice-list-page"
        try:
            self.page.goto(target_url, wait_until="domcontentloaded")
            self.page.wait_for_url("**/invoice-list-page*", timeout=20000)
        except Exception as e:
            logger.warning(f"Direct goto failed: {e}. Trying sidebar link...")
            invoice_link = self.page.locator("a[href*='invoice-list'], a:has-text('Invoices')").first
            if invoice_link.count() > 0 and invoice_link.is_visible():
                invoice_link.click()
                self.page.wait_for_url("**/invoice-list-page*", timeout=20000)

        self.page.wait_for_timeout(1500)
        try:
            self.page.locator("table tbody tr, table, div[role='table']").first.wait_for(
                state="visible", timeout=20000
            )
        except Exception:
            pass
        logger.info(f"On Invoices page. Current URL: {self.page.url}")

    # -------------------------------------------------------------------------
    # KPI METRICS & CURRENCY TOGGLE
    # -------------------------------------------------------------------------

    def switch_currency(self, currency: str = "USD"):
        """
        Switch top KPI currency display: 'INR' (₹ INR) or 'USD' ($ USD).
        """
        logger.info(f"Switching invoice KPI currency to: {currency}")
        btn = self.page.locator(f"button:has-text('{currency}'), button:has-text('{currency.upper()}')").first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1000)

    def get_kpi_metrics(self) -> dict:
        """
        Extract values from top KPI summary cards:
        - due_today
        - overdue
        - due_in_next_7_days
        - total_outstanding
        - collected_this_month
        """
        metrics = {}
        labels = [
            ("due_today", "Due today"),
            ("overdue", "Overdue"),
            ("due_in_next_7_days", "Due in next 7 days"),
            ("total_outstanding", "Total outstanding"),
            ("collected_this_month", "Collected this month"),
        ]
        for key, text_label in labels:
            try:
                card_lbl = self.page.get_by_text(text_label, exact=True).first
                if card_lbl.is_visible():
                    card = card_lbl.locator("..")
                    lines = [l.strip() for l in card.inner_text().split("\n") if l.strip()]
                    if len(lines) >= 2:
                        metrics[key] = {"amount": lines[1], "info": lines[2] if len(lines) > 2 else ""}
            except Exception:
                pass

        logger.info(f"Invoices KPI metrics: {metrics}")
        return metrics

    # -------------------------------------------------------------------------
    # STATUS FILTER TABS
    # -------------------------------------------------------------------------

    def get_status_tabs(self) -> dict:
        """Extract available status tabs and their counts (e.g. {'All': 34, 'Pending': 11, 'Paid': 13...})."""
        tabs = {}
        tab_buttons = self.page.locator("button.chakra-tabs__tab, button:has-text('Pending'), button:has-text('Paid'), button:has-text('All')").all()
        for b in tab_buttons:
            txt = b.inner_text().strip()
            parts = txt.split("\n")
            if len(parts) >= 2:
                tabs[parts[0].strip()] = parts[1].strip()
            elif txt:
                tabs[txt] = ""
        logger.info(f"Detected Invoice status tabs: {tabs}")
        return tabs

    def filter_by_status_tab(self, status: str = "Pending"):
        """Click a status filter tab ('All', 'Pending', 'Paid', 'Balance', 'Overpay', 'Rejected')."""
        logger.info(f"Filtering invoices by status tab: '{status}'")
        btn = self.page.locator(f"button:has-text('{status}')").first
        btn.click()
        self.page.wait_for_timeout(1200)

    # -------------------------------------------------------------------------
    # SEARCH & FILTERS
    # -------------------------------------------------------------------------

    def search_invoices(self, query: str):
        """Search invoices by invoice number, customer, or project name."""
        logger.info(f"Searching invoices for: '{query}'")
        search_box = self.page.locator("input[placeholder*='Search invoice no'], input[placeholder*='Search']").first
        search_box.fill(query)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1000)

    def filter_by_customer(self, customer_name: str):
        """Filter by customer dropdown."""
        select = self.page.locator("select:has-text('All customers'), select").first
        select.select_option(label=customer_name)
        self.page.wait_for_timeout(1000)

    # -------------------------------------------------------------------------
    # TABLE & ROW DATA
    # -------------------------------------------------------------------------

    def get_table_headers(self) -> list[str]:
        """Return list of table header column names."""
        headers = self.page.locator("table thead th").all()
        return [th.inner_text().strip() for th in headers if th.is_visible()]

    def get_table_rows(self):
        """Return locator for table body rows."""
        return self.page.locator("table tbody tr")

    def get_invoice_row_data(self, row_index: int = 0) -> dict:
        """Extract structured data from a specific invoice row."""
        rows = self.get_table_rows()
        row = rows.nth(row_index)
        cells = [td.inner_text().strip().replace("\n", " ") for td in row.locator("td").all()]
        if len(cells) < 13:
            return {}
        status_td = row.locator("td").nth(12)
        select_loc = status_td.locator("select")
        if select_loc.count() > 0:
            try:
                selected_opt = select_loc.locator("option:checked")
                if selected_opt.count() > 0:
                    status_val = selected_opt.first.inner_text().strip()
                else:
                    status_val = select_loc.first.input_value()
            except Exception:
                status_val = select_loc.first.input_value()
        else:
            status_val = cells[12]

        return {
            "s_no": cells[0],
            "invoice_no": cells[1],
            "customer": cells[2],
            "project": cells[3],
            "issued": cells[4],
            "due": cells[5],
            "amount_inr": cells[6],
            "paid_inr": cells[7],
            "outstanding_inr": cells[8],
            "amount_usd": cells[9],
            "paid_usd": cells[10],
            "outstanding_usd": cells[11],
            "status": status_val,
            "credit_note": cells[13] if len(cells) > 13 else "",
            "verification": cells[14] if len(cells) > 14 else "",
            "edit": cells[15] if len(cells) > 15 else "",
        }

    def find_invoice_row_by_number(self, invoice_no: str):
        """Find the table row matching a specific invoice number."""
        rows = self.get_table_rows().all()
        for r in rows:
            if invoice_no.lower() in r.locator("td:nth-child(2)").inner_text().lower():
                return r
        return None

    # -------------------------------------------------------------------------
    # INVOICE ACTIONS: PDF, VERIFY, REJECT, STATUS UPDATE
    # -------------------------------------------------------------------------

    def download_invoice_pdf(self, invoice_no: str, download_dir: str = None) -> str:
        """
        Download the PDF invoice for a given invoice number.
        Returns the saved local file path.
        """
        logger.info(f"Downloading PDF for invoice: '{invoice_no}'")
        row = self.find_invoice_row_by_number(invoice_no)
        if not row:
            raise ValueError(f"Invoice '{invoice_no}' not found in table.")

        download_btn = row.locator("td:last-child button, button[title*='download'], button[aria-label*='download']").first
        if not download_btn.is_visible():
            download_btn = row.locator("td:nth-child(17) button").first

        with self.page.expect_download(timeout=20000) as download_info:
            download_btn.click()
        download = download_info.value

        suggested_name = download.suggested_filename
        if not download_dir:
            download_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(download_dir, exist_ok=True)
        target_path = os.path.join(download_dir, suggested_name)
        download.save_as(target_path)

        logger.info(f"Invoice PDF saved to: {target_path} (size: {os.path.getsize(target_path)} bytes)")
        return target_path

    def update_invoice_status(self, invoice_no: str, new_status: str):
        """
        Update the status of an invoice via table status select (Pending, Paid, Balance, Overpay).
        """
        logger.info(f"Updating invoice '{invoice_no}' status to: '{new_status}'")
        row = self.find_invoice_row_by_number(invoice_no)
        if not row:
            raise ValueError(f"Invoice '{invoice_no}' not found in table.")

        status_select = row.locator("td:nth-child(13) select").first
        if status_select.is_visible():
            status_select.select_option(label=new_status)
            self.page.wait_for_timeout(1000)
            logger.info(f"Invoice status updated to '{new_status}'.")
        else:
            logger.warning(f"Status select not interactive on row for '{invoice_no}'.")

    def verify_invoice(self, invoice_no: str):
        """Click 'Verify invoice' button if available on row."""
        logger.info(f"Verifying invoice: '{invoice_no}'")
        row = self.find_invoice_row_by_number(invoice_no)
        if not row:
            raise ValueError(f"Invoice '{invoice_no}' not found in table.")
        verify_btn = row.locator("button:has-text('Verify invoice'), button:has-text('Verify')").first
        if verify_btn.is_visible():
            verify_btn.click()
            self.page.wait_for_timeout(1000)

    def reject_invoice(self, invoice_no: str, reason: str = "Client Requested Cancellation"):
        """Click 'Reject invoice' button if available on row."""
        logger.info(f"Rejecting invoice: '{invoice_no}' with reason: '{reason}'")
        row = self.find_invoice_row_by_number(invoice_no)
        if not row:
            raise ValueError(f"Invoice '{invoice_no}' not found in table.")
        reject_btn = row.locator("button:has-text('Reject invoice'), button:has-text('Reject')").first
        if reject_btn.is_visible():
            reject_btn.click()
            self.page.wait_for_timeout(800)
            # Fill modal if present
            reason_inp = self.page.locator("textarea, input[placeholder*='reason']").first
            if reason_inp.is_visible():
                reason_inp.fill(reason)
            confirm_btn = self.page.locator("button:has-text('Confirm'), button:has-text('Reject')").last
            if confirm_btn.is_visible():
                confirm_btn.click()
            self.page.wait_for_timeout(1000)
