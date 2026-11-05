import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DynamicTable — header-aware table abstraction
# ---------------------------------------------------------------------------

class TableRow:
    """A single row with named-column access."""

    def __init__(self, row_locator, headers: list):
        self._row = row_locator
        self._headers = [h.strip().upper() for h in headers]

    def get_value(self, column: str) -> str:
        """Return the text value of the cell in the given column (case-insensitive)."""
        col_upper = column.strip().upper()
        if col_upper not in self._headers:
            raise ValueError(
                f"Column '{column}' not found. Available columns: {self._headers}"
            )
        idx = self._headers.index(col_upper)
        cells = self._row.locator("td").all()
        if idx >= len(cells):
            raise IndexError(
                f"Column index {idx} out of range; row has {len(cells)} cells."
            )
        return cells[idx].inner_text().strip()

    def get_cell(self, column: str):
        """Return the Playwright Locator for the cell in the given column."""
        col_upper = column.strip().upper()
        if col_upper not in self._headers:
            raise ValueError(
                f"Column '{column}' not found. Available columns: {self._headers}"
            )
        idx = self._headers.index(col_upper)
        return self._row.locator("td").nth(idx)

    def get_all_values(self) -> dict:
        """Return all column values as a dict keyed by header name."""
        cells = self._row.locator("td").all()
        return {
            header: (cells[i].inner_text().strip() if i < len(cells) else "")
            for i, header in enumerate(self._headers)
        }


class DynamicTable:
    """
    Header-aware table abstraction for Playwright.

    Usage::

        table = DynamicTable(page)

        row = table.find_row(column="PHONE NUMBER", value=phone)
        lead_id   = row.get_value("LEAD ID")
        assigned  = row.get_value("ASSIGNED TO")
        status    = row.get_value("STATUS")

    Parameters
    ----------
    page              : Playwright page object.
    table_locator     : CSS selector for the <table> (default: "table").
    header_row_locator: CSS selector for TH cells relative to the table
                        (default: "thead th").
    timeout           : ms to wait for the table to appear (default: 30 000).
    """

    def __init__(
        self,
        page,
        table_locator: str = "table",
        header_row_locator: str = "thead th",
        timeout: int = 30_000,
    ):
        self._page = page
        self._table_locator = table_locator
        self._header_row_locator = header_row_locator
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_headers(self) -> list:
        table = self._page.locator(self._table_locator).first
        table.wait_for(state="visible", timeout=self._timeout)
        self._page.locator("tbody tr").first.wait_for(
            state="visible", timeout=self._timeout
        )
        headers = table.locator(self._header_row_locator).all()
        return [h.inner_text().strip() for h in headers]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_headers(self) -> list:
        return self._get_headers()

    def find_row(
        self,
        column: str,
        value: str,
        match_partial: bool = False,
        match_last_n: int = None,
    ) -> TableRow:
        """
        Return the first row whose ``column`` cell matches ``value``.

        Parameters
        ----------
        column        : Column header (case-insensitive).
        value         : Expected cell value.
        match_partial : If True, ``value in cell`` rather than ``value == cell``.
        match_last_n  : If set, compare only the last N characters of the cell.

        Raises
        ------
        LookupError   : When no matching row is found.
        """
        headers = self._get_headers()
        headers_upper = [h.upper() for h in headers]
        col_upper = column.strip().upper()

        if col_upper not in headers_upper:
            raise ValueError(
                f"Column '{column}' not found. Available: {headers}"
            )
        col_idx = headers_upper.index(col_upper)

        table = self._page.locator(self._table_locator).first
        rows = table.locator("tbody tr").all()

        for idx, row in enumerate(rows):
            cells = row.locator("td").all()
            if col_idx >= len(cells):
                continue
            cell_text = cells[col_idx].inner_text().strip()

            if match_last_n is not None:
                matched = cell_text[-match_last_n:] == value[-match_last_n:]
            elif match_partial:
                matched = value.lower() in cell_text.lower()
            else:
                matched = cell_text == value

            if matched:
                logger.info(
                    f"DynamicTable.find_row: hit at row {idx} "
                    f"(col='{column}', value='{value}', cell='{cell_text}')"
                )
                return TableRow(row, headers)

        # Dump rows for easier debugging
        for idx, row in enumerate(rows):
            cells = row.locator("td").all()
            logger.debug(f"  Row {idx}: {[c.inner_text().strip() for c in cells]}")

        raise LookupError(
            f"No row where '{column}' = '{value}' "
            f"(partial={match_partial}, last_n={match_last_n}). "
            f"Table has {len(rows)} row(s)."
        )

    def find_row_by_phone(self, phone_number: str) -> TableRow:
        """
        Find a row by phone number with automatic masked-number fallback
        (tries exact match first, then last-4-digit partial match).
        """
        headers = self._get_headers()
        headers_upper = [h.upper() for h in headers]
        phone_col = None
        for candidate in ["PHONE NUMBER", "PHONE", "CONTACT NUMBER", "MOBILE", "CONTACT"]:
            if candidate in headers_upper:
                phone_col = headers[headers_upper.index(candidate)]
                break
        if phone_col is None:
            raise ValueError(f"No phone column found. Headers: {headers}")

        last_four = phone_number[-4:] if len(phone_number) >= 4 else phone_number

        try:
            return self.find_row(column=phone_col, value=phone_number)
        except LookupError:
            pass

        logger.info(
            f"Exact phone match failed; trying last-4 '{last_four}'…"
        )
        return self.find_row(column=phone_col, value=last_four, match_partial=True)


# ---------------------------------------------------------------------------
# Page Objects
# ---------------------------------------------------------------------------

class LeadPoolPage:
    def __init__(self, page):
        self.page = page
        self.lead_module = self.page.locator("//a[text()='Lead']")
        self.lead_pool_menu = self.page.locator("//a[@href='/lead-pool']")

    def go_to_lead_pool(self):
        logger.info("Navigating to Lead Pool…")
        if not self.lead_pool_menu.is_visible():
            if self.lead_module.is_visible():
                self.lead_module.click()
        try:
            self.lead_pool_menu.wait_for(state="visible", timeout=5000)
            self.lead_pool_menu.click()
        except Exception:
            import os
            base_url = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login").replace("/login", "")
            self.page.goto(f"{base_url}/lead-pool", wait_until="domcontentloaded")

        self.page.wait_for_url("**/lead-pool", timeout=30_000)
        self.page.wait_for_timeout(1_000)

    def find_lead_by_phone(self, phone_number: str, company_name: str = None):
        """
        Return (lead_id, assigned_to) for the row matching the phone number.
        Uses DynamicTable — no positional indices.
        """
        logger.info(
            f"Finding lead: phone='{phone_number}', company='{company_name}'"
        )
        table = DynamicTable(self.page)

        # Primary: exact / masked phone match
        try:
            row = table.find_row_by_phone(phone_number)
        except LookupError:
            # Secondary: company name partial match
            if company_name:
                logger.info(
                    f"Phone match failed; trying company name '{company_name}'…"
                )
                row = table.find_row(
                    column="COMPANY", value=company_name, match_partial=True
                )
            else:
                raise

        all_vals = row.get_all_values()
        logger.info(f"Matched row values: {all_vals}")

        try:
            lead_id = row.get_value("LEAD ID")
        except ValueError:
            try:
                lead_id = row.get_value("S.NO")
            except ValueError:
                lead_id = company_name or phone_number

        assigned_to = row.get_value("ASSIGNED TO")
        logger.info(f"Lead ID: {lead_id} | Assigned To: {assigned_to}")
        return lead_id, assigned_to


class CreatedLeadPage:
    def __init__(self, page):
        self.page = page
        self.lead_module = self.page.locator("//a[text()='Lead' or text()='Leads']")
        self.created_lead_menu = self.page.locator("//a[contains(@href, 'created-lead') or contains(text(), 'Created Lead')]")

    def go_to_created_lead(self):
        logger.info("Navigating to Created Lead sub-module…")
        try:
            if not self.created_lead_menu.is_visible():
                if self.lead_module.is_visible():
                    self.lead_module.first.click()
                    self.page.wait_for_timeout(500)
            if self.created_lead_menu.is_visible():
                self.created_lead_menu.first.click()
            else:
                import os
                base_url = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login").replace("/login", "").rstrip("/")
                self.page.goto(f"{base_url}/created-lead", wait_until="domcontentloaded")
        except Exception:
            import os
            base_url = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login").replace("/login", "").rstrip("/")
            self.page.goto(f"{base_url}/created-lead", wait_until="domcontentloaded")

        self.page.wait_for_timeout(1_000)

    def search_lead(self, query: str):
        """Type search query into search input box and press Enter."""
        logger.info(f"Searching lead table for: '{query}'")
        search_box = self.page.get_by_placeholder("Search", exact=False)
        if search_box.count() == 0 or not search_box.first.is_visible():
            search_box = self.page.locator("input[placeholder*='Search'], input[type='search'], input[name='search']")
        if search_box.count() > 0 and search_box.first.is_visible():
            search_box.first.fill(query)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(1500)

    def find_lead_and_capture_assigned_bdm(self, phone_number: str, company_name: str = None):
        """
        Search for lead by phone or company name, verify Assigned To column, and return (lead_id, assigned_to).
        """
        logger.info(f"Searching Created Lead table: phone='{phone_number}', company='{company_name}'")
        if company_name or phone_number:
            self.search_lead(company_name or phone_number)

        table = DynamicTable(self.page)
        try:
            row = table.find_row_by_phone(phone_number)
        except LookupError:
            if company_name:
                row = table.find_row(column="COMPANY", value=company_name, match_partial=True)
            else:
                raise

        try:
            lead_id = row.get_value("LEAD ID")
        except ValueError:
            try:
                lead_id = row.get_value("S.NO")
            except ValueError:
                lead_id = company_name or phone_number

        assigned_to = row.get_value("ASSIGNED TO")
        logger.info(f"Captured Lead ID: {lead_id} | Assigned BDM: {assigned_to}")
        return lead_id, assigned_to



class MyLeadsPage:
    def __init__(self, page):
        self.page = page
        self.lead_module = self.page.locator("//a[text()='Lead']")
        self.my_leads_menu = self.page.locator("//a[@href='/my-leads']")

    def go_to_my_leads(self):
        logger.info("Navigating to My Leads…")
        if not self.my_leads_menu.is_visible():
            if self.lead_module.is_visible():
                self.lead_module.click()
        try:
            self.my_leads_menu.wait_for(state="visible", timeout=5000)
            self.my_leads_menu.click()
        except Exception:
            import os
            base_url = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login").replace("/login", "")
            self.page.goto(f"{base_url}/my-leads", wait_until="domcontentloaded")

        self.page.wait_for_url("**/my-leads", timeout=30_000)
        self.page.wait_for_timeout(1_000)

    def _get_table(self) -> DynamicTable:
        return DynamicTable(self.page)

    def get_row_by_lead_id(self, lead_id: str) -> TableRow:
        table = self._get_table()
        return table.find_row(column="LEAD ID", value=str(lead_id))

    def accept_lead_if_assigned(self, row: TableRow):
        """
        If lead is in 'Assigned' status, click the green checkmark action icon in ACTION column,
        fill optional reason in the 'Accept Lead' modal, click Accept button, and wait for modal to close.
        """
        current_status = row.get_value("LEAD STATUS").strip()
        logger.info(f"Current Lead Status in My Leads: '{current_status}'")
        if current_status.lower() in ["assigned", "new"]:
            logger.info("Lead status is 'Assigned'. Accepting lead via Accept Lead modal...")
            action_cell = row.get_cell("ACTION")
            green_check = action_cell.locator("button, svg, a").first
            if green_check.is_visible():
                green_check.click()
                self.page.wait_for_timeout(1000)

            # Locate the Accept Lead modal specifically
            modal = self.page.locator("section[aria-modal='true'], [role='dialog'], .chakra-modal__content").filter(
                has_text="Accept Lead"
            ).first
            if not modal.is_visible():
                modal = self.page.locator("section[aria-modal='true'], [role='dialog'], .chakra-modal__content").first

            modal.wait_for(state="visible", timeout=10000)
            logger.info("Accept Lead modal is visible.")

            # Fill optional reason textarea
            reason_area = modal.locator("textarea[placeholder*='Reason'], textarea")
            if reason_area.count() > 0 and reason_area.first.is_visible():
                reason_area.first.fill("Accepting lead via automated conversion test")
                logger.info("Filled reason for accepting lead.")

            # Click Accept button inside modal
            accept_btn = modal.get_by_role("button", name="Accept", exact=True)
            if accept_btn.count() == 0 or not accept_btn.first.is_visible():
                accept_btn = modal.locator("button.chakra-button").filter(has_text="Accept")
            if accept_btn.count() == 0 or not accept_btn.first.is_visible():
                accept_btn = modal.locator("button:has-text('Accept')")

            accept_btn.first.click()
            logger.info("Clicked Accept button inside Accept Lead modal.")

            # Wait for Accept Lead modal to close completely
            try:
                modal.wait_for(state="hidden", timeout=10000)
            except Exception:
                self.page.wait_for_timeout(2000)

            logger.info("Accept Lead modal closed successfully.")
            self.page.wait_for_timeout(1500)

    # ------------------------------------------------------------------
    # Update Status modal + Requirement Gathering
    # ------------------------------------------------------------------

    def update_lead_status(self, lead_id: str, status_name: str):
        """
        Click the LEAD STATUS cell to open the Update Status modal,
        select the given status via the native chakra-select, and click Update.
        Waits for the modal to close before returning.
        """
        from playwright.sync_api import expect

        # ── Find row ────────────────────────────────────────────────────
        table = DynamicTable(self.page)
        row = table.find_row(column="LEAD ID", value=str(lead_id))
        logger.info(f"Found Lead Row: {row.get_all_values()}")

        # ── Click LEAD STATUS cell ───────────────────────────────────────
        status_cell = row.get_cell("LEAD STATUS")
        try:
            status_cell.click(timeout=5_000)
        except Exception:
            status_cell.locator("div").first.click(timeout=5_000)

        # ── Wait for Update Status modal ─────────────────────────────────
        # DOM inspection confirmed: modal is section[aria-modal='true'] with
        # class 'chakra-modal__content', header has class 'chakra-modal__header'
        update_status_modal = self.page.locator("section[aria-modal='true']")
        update_status_modal.wait_for(state="visible", timeout=10_000)
        logger.info("Update Status modal opened")

        # ── Select status via native <select> scoped to modal ──────────────
        # Two selects on page: page-size (10/50/100) and status — scope to modal
        status_dropdown = self.page.locator("section[aria-modal='true'] select")
        status_dropdown.select_option(label=status_name)
        logger.info(f"Selected '{status_name}'")

        # ── Click Update ─────────────────────────────────────────────────
        update_btn = update_status_modal.get_by_role("button", name="Update")
        expect(update_btn).to_be_enabled(timeout=5_000)
        update_btn.click()
        logger.info("Clicked Update button")

        # ── Wait for modal to close ──────────────────────────────────────
        update_status_modal.wait_for(state="hidden", timeout=10_000)
        logger.info("Update Status modal closed")
        self.page.wait_for_timeout(1_000)

    # Kept for backward compatibility — delegates to update_lead_status
    def open_update_status_modal(self, lead_id: str):
        """Deprecated: use update_lead_status() instead."""
        pass  # modal is opened inside update_lead_status

    def select_status_and_update(self, status_name: str, description: str = ""):
        """Deprecated: use update_lead_status() instead."""
        pass

    # ------------------------------------------------------------------
    # Requirement Gathering form
    # ------------------------------------------------------------------

    def open_requirement_gathering_form(self, lead_id: str):
        logger.info(f"Opening Requirement Gathering form for Lead ID: {lead_id}")

        # Re-fetch row after table may have refreshed
        table = DynamicTable(self.page)
        row = table.find_row(column="LEAD ID", value=str(lead_id))

        # ── Open Action Menu ─────────────────────────────────────────────
        action_cell = row.get_cell("ACTION")
        try:
            action_cell.locator("button").first.click(timeout=5_000)
        except Exception:
            action_cell.click(timeout=5_000)
        logger.info("Action menu opened")

        # ── Click Requirement Gathering menu item ────────────────────────
        self.page.get_by_role("menuitem", name="Requirement Gathering").click()
        logger.info("Requirement Gathering option clicked")

        # ── Verify form opened ───────────────────────────────────────────
        from playwright.sync_api import expect
        expect(
            self.page.get_by_text("Basic Information", exact=False)
        ).to_be_visible(timeout=10_000)
        logger.info("Requirement Gathering form is visible")


# ---------------------------------------------------------------------------
# Requirement Gathering form
# ---------------------------------------------------------------------------

class RequirementGatheringPage:
    def __init__(self, page):
        self.page = page

    def _select_dropdown_option(
        self,
        textbox_name: str,
        option_text: str,
        exact: bool = True,
    ):
        dropdown = self.page.get_by_role("textbox", name=textbox_name)
        dropdown.wait_for(state="visible", timeout=30_000)
        dropdown.click()
        option = self.page.get_by_text(option_text, exact=exact)
        option.wait_for(state="visible", timeout=15_000)
        option.click()
        self.page.wait_for_timeout(500)

    def fill_step_1(
        self,
        industry_type: str = "Software Development",
        lead_source: str = "website",
        designation: str = "HR",
    ):
        logger.info(
            f"Filling Step 1 — Industry: '{industry_type}', Lead Source: '{lead_source}', Designation: '{designation}'"
        )
        self._select_dropdown_option("Industry Type *", industry_type)
        self._select_dropdown_option("Lead Source *", lead_source)
        self._select_dropdown_option("Designation *", designation)

        self.page.get_by_role("button", name="Next", exact=True).click()
        self.page.get_by_role("textbox", name="Business Type *").wait_for(
            state="visible", timeout=20_000
        )

    def fill_step_2_and_submit(
        self,
        business_type: str = "B2B",
        years_in_business: str = "3",
        search_source: str = "Google Ads",
        budget: str = "50000",
        competitor: str = "competior1",
        business_challenges: str = "Business challenge",
    ):
        logger.info(
            f"Filling Step 2 — Business Type: '{business_type}', Years: '{years_in_business}', Search Source: '{search_source}'"
        )
        self._select_dropdown_option("Business Type *", business_type)

        self.page.get_by_role("textbox", name="Years in Business *").click()
        self.page.get_by_role("list").get_by_text(years_in_business, exact=True).click()

        self.page.get_by_role("textbox", name="Search...").click()
        self.page.get_by_text(search_source, exact=True).click()

        self.page.get_by_placeholder("Budget", exact=True).fill(budget)
        self.page.get_by_role("textbox", name="Competitor").fill(competitor)
        self.page.get_by_role("textbox", name="Business Challenges").fill(
            business_challenges
        )

        self.page.get_by_role("button", name="Click To Speak").click()
        self.page.get_by_role("button", name="Submit").click()
        self.page.wait_for_timeout(2_000)


# ---------------------------------------------------------------------------
# Lead POC Page
# ---------------------------------------------------------------------------

class LeadPOCPage:
    """Page Object Model for the Lead -> POC sub-module."""

    def __init__(self, page):
        self.page = page

    def go_to_lead_module(self):
        """Click the Lead module from navigation sidebar."""
        logger.info("Clicking Lead module from navigation...")
        lead_lnk = self.page.get_by_role("link", name="Lead")
        if lead_lnk.count() == 0 or not lead_lnk.is_visible():
            lead_lnk = self.page.locator("//a[text()='Lead']")
        if lead_lnk.count() == 0 or not lead_lnk.is_visible():
            lead_lnk = self.page.get_by_text("Lead", exact=True)
        
        lead_lnk.first.click()
        self.page.wait_for_timeout(1000)

    def open_poc_submodule(self):
        """Click the POC sub-module under Lead navigation."""
        logger.info("Opening POC sub-module under Lead...")
        poc_sub = self.page.get_by_role("link", name="POC")
        if poc_sub.count() == 0 or not poc_sub.is_visible():
            poc_sub = self.page.locator("a[href='/poc'], a[href='/lead-poc'], a[href*='poc']")
        if poc_sub.count() == 0 or not poc_sub.is_visible():
            poc_sub = self.page.get_by_text("POC", exact=True)

        try:
            poc_sub.first.wait_for(state="visible", timeout=5000)
            poc_sub.first.click()
        except Exception:
            # Fallback to direct navigation if click fails
            import os
            base_url = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login").replace("/login", "").rstrip("/")
            self.page.goto(f"{base_url}/poc", wait_until="domcontentloaded")

        try:
            self.page.wait_for_url("**/*poc*", timeout=15000)
        except Exception:
            pass

        # Wait for table to load
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=15000)
        except Exception:
            pass

    def search_record(self, query: str):
        """Search for a Company or POC record using the search input."""
        logger.info(f"Searching POC records for: '{query}'")
        search_box = self.page.get_by_placeholder("Search", exact=False)
        if search_box.count() == 0 or not search_box.first.is_visible():
            search_box = self.page.locator("input[placeholder*='Search'], input[type='search'], input[name='search']")

        search_box.first.wait_for(state="visible", timeout=10000)
        search_box.first.fill(query)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(2000)

    def is_record_visible_in_table(self, identifier: str, poc_name: str = None) -> bool:
        """Verify that the matching record row is present in the table search results."""
        logger.info(f"Verifying presence of record '{identifier}' in POC table...")
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=15000)
        except Exception:
            logger.warning("No rows found in POC table after search.")
            return False

        rows = self.page.locator("tbody tr").all()
        for idx, row in enumerate(rows):
            row_text = row.inner_text().strip()
            logger.debug(f"POC Table Row {idx}: '{row_text}'")
            if identifier.lower() in row_text.lower():
                if poc_name:
                    if poc_name.lower() in row_text.lower():
                        return True
                else:
                    return True
        return False

