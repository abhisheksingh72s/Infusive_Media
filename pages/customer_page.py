import os
import logging
from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)


class CustomerPage:
    """
    Page Object Model for the Customers Module (/customers and /customers/{id}).
    Handles:
      - Phase 5: Navigation to Customers list
      - Table inspection, column header verification
      - Search by Customer Name / Email
      - Row data extraction (Customer Name, Email, Phone, Address, Outstanding, Status)
      - View details action (/customers/{id})
      - Detail profile assertions (Customer ID, Name, Email, Address)
    """

    def __init__(self, page: Page):
        self.page = page

    def get_base_url(self) -> str:
        base_url = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")
        return base_url.replace("/login", "").rstrip("/")

    def go_to_customers(self):
        """Navigate to the Customers module."""
        logger.info("Navigating to Customers module (/customers)...")

        cust_link = self.page.locator("a[href='/customers'], a[href*='customers']")
        try:
            if cust_link.count() > 0 and cust_link.first.is_visible():
                cust_link.first.click()
            else:
                base_url = self.get_base_url()
                self.page.goto(f"{base_url}/customers", wait_until="domcontentloaded")
        except Exception as e:
            logger.warning(f"Sidebar click navigation failed: {e}. Navigating directly via URL.")
            base_url = self.get_base_url()
            self.page.goto(f"{base_url}/customers", wait_until="domcontentloaded")

        try:
            self.page.wait_for_url("**/customers*", timeout=15000)
        except Exception:
            pass

        self.page.wait_for_timeout(1500)
        logger.info(f"On Customers page. Current URL: {self.page.url}")

    def get_table_headers(self) -> list:
        """Return list of table header names."""
        self.page.locator("thead th, table th").first.wait_for(state="visible", timeout=10000)
        headers = [h.inner_text().strip() for h in self.page.locator("thead th, table th").all() if h.inner_text().strip()]
        logger.info(f"Customers table headers: {headers}")
        return headers

    def search_customer(self, query: str):
        """Search for a customer by name or email."""
        logger.info(f"Searching Customers table for: '{query}'...")
        search_box = self.page.get_by_placeholder("Search by name, email", exact=False)
        if search_box.count() == 0 or not search_box.first.is_visible():
            search_box = self.page.locator("input[placeholder*='Search'], input[type='search']")

        if search_box.count() > 0 and search_box.first.is_visible():
            search_box.first.fill(query)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(1500)
        else:
            logger.warning("Customer search input not found; filtering rows directly.")

    def get_customer_rows(self) -> list:
        """Return all rows currently visible in the customers table."""
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=10000)
            return self.page.locator("tbody tr").all()
        except Exception:
            return []

    def verify_customer_exists(self, customer_name: str) -> bool:
        """Search and check if customer row exists in table."""
        logger.info(f"Verifying customer existence for: '{customer_name}'...")
        self.search_customer(customer_name)
        rows = self.get_customer_rows()
        for r in rows:
            if customer_name.lower() in r.inner_text().lower():
                logger.info(f"Customer '{customer_name}' found in table ✓")
                return True

        # Fallback check across all rows without search filter
        all_text = self.page.locator("tbody").inner_text()
        found = customer_name.lower() in all_text.lower()
        if found:
            logger.info(f"Customer '{customer_name}' found in raw table body ✓")
        return found

    def get_customer_row_data(self, customer_name: str) -> dict:
        """
        Extract row data for the given customer name:
        Columns: S.NO, CUSTOMER NAME, EMAIL, PHONE, ADDRESS, OUTSTANDING, STATUS
        """
        logger.info(f"Extracting row data for customer: '{customer_name}'...")
        self.search_customer(customer_name)
        rows = self.get_customer_rows()
        for r in rows:
            if customer_name.lower() in r.inner_text().lower():
                cells = [td.inner_text().strip() for td in r.locator("td").all()]
                data = {
                    "s_no": cells[0] if len(cells) > 0 else "",
                    "name": cells[1] if len(cells) > 1 else "",
                    "email": cells[2] if len(cells) > 2 else "",
                    "phone": cells[3] if len(cells) > 3 else "",
                    "address": cells[4] if len(cells) > 4 else "",
                    "outstanding": cells[5] if len(cells) > 5 else "",
                    "status": cells[6] if len(cells) > 6 else "",
                }
                logger.info(f"Extracted customer data: {data}")
                return data

        raise ValueError(f"Customer '{customer_name}' not found in Customers table.")

    def click_view_customer_details(self, customer_name: str = ""):
        """
        Click the View Details (eye) action icon for the given customer or first available.
        Navigates to /customers/{id}.
        """
        logger.info(f"Opening Customer Details for: '{customer_name}'..." if customer_name else "Opening first Customer Details...")
        if customer_name:
            self.search_customer(customer_name)

        target_row = self.page.locator("tbody tr").first
        if customer_name:
            matching = self.page.locator("tbody tr").filter(has_text=customer_name).first
            if matching.count() > 0 and matching.is_visible():
                target_row = matching

        action_cell = target_row.locator("td:last-child")
        eye_icon = action_cell.locator("svg, div.css-1m9jp0d, div.css-ih2uuh")
        if eye_icon.count() > 0 and eye_icon.first.is_visible():
            eye_icon.first.click()
        else:
            action_cell.click()

        self.page.wait_for_timeout(2000)
        try:
            self.page.wait_for_url("**/customers/*", timeout=15000)
        except Exception:
            pass
        logger.info(f"Navigated to Customer Details. Current URL: {self.page.url}")

    def get_customer_detail_profile(self) -> dict:
        """
        Extract profile attributes from /customers/{id} detail page.
        """
        logger.info("Extracting customer detail profile...")
        self.page.wait_for_timeout(1500)
        content_loc = self.page.locator("text='Customer Details', div.chakra-card, main, #root").first
        try:
            content_loc.wait_for(state="visible", timeout=10000)
        except Exception:
            pass
        raw_text = self.page.locator("main, #root").inner_text()

        # Parse common detail fields
        profile = {
            "url": self.page.url,
            "raw_text": raw_text,
        }

        # Extract Customer ID if present (e.g. CUST-006)
        import re
        cust_id_match = re.search(r"CUST-\d+", raw_text)
        if cust_id_match:
            profile["customer_id"] = cust_id_match.group(0)

        logger.info(f"Customer profile details: {profile}")
        return profile

    # -------------------------------------------------------------------------
    # CUSTOMER DETAILS TABS & PROFILE SUB-TABS
    # -------------------------------------------------------------------------

    def switch_to_customer_tab(self, tab_name: str = "Overview"):
        """
        Switch between main tabs on /customers/{id}:
        - Overview
        - Projects
        - Invoices
        - Client Profile
        """
        logger.info(f"Switching to Customer tab: '{tab_name}'...")
        tab_btn = self.page.locator(".chakra-tabs__tablist button[role='tab']").filter(has_text=tab_name).first
        if tab_btn.count() > 0 and tab_btn.is_visible():
            tab_btn.click()
            self.page.wait_for_timeout(800)
            logger.info(f"Switched to Customer tab: '{tab_name}' ✓")
        else:
            raise AssertionError(f"Customer tab '{tab_name}' not found or not visible.")

    def switch_to_client_profile_subtab(self, subtab_name: str = "Basic Information"):
        """
        Switch between sub-tabs under 'Client Profile':
        - Basic Information
        - Billing Address
        - Tax & GST Details
        """
        logger.info(f"Switching to Client Profile sub-tab: '{subtab_name}'...")
        subtab_btn = self.page.locator("button.chakra-stack").filter(has_text=subtab_name).first
        if subtab_btn.count() > 0 and subtab_btn.is_visible():
            subtab_btn.click()
            self.page.wait_for_timeout(800)
            logger.info(f"Switched to Client Profile sub-tab: '{subtab_name}' ✓")
        else:
            raise AssertionError(f"Client Profile sub-tab '{subtab_name}' not found.")

    def toggle_overview_currency(self, currency_code: str = "USD"):
        """
        Toggle currency view on Overview tab ('INR' or 'USD').
        """
        logger.info(f"Toggling Overview currency view to: '{currency_code}'...")
        btn_text = "$ USD" if "USD" in currency_code.upper() else "₹ INR"
        curr_btn = self.page.locator(".chakra-button__group button").filter(has_text=btn_text).first
        if curr_btn.is_visible():
            curr_btn.click()
            self.page.wait_for_timeout(500)
            logger.info(f"Currency view toggled to '{btn_text}' ✓")

    def get_overview_kpis(self) -> dict:
        """
        Extract Invoices, Paid Amount, Outstanding, and Last Invoice from Overview tab.
        """
        overview_panel = self.page.locator(".chakra-tabs__tab-panel:not([hidden])").first
        cards = overview_panel.locator(".chakra-stack.css-1ggra3u, div:has(> div > p.chakra-text)").all()
        kpis = {}
        for c in cards:
            text = c.inner_text().strip()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if len(lines) >= 2:
                kpis[lines[0]] = lines[1]
        logger.info(f"Customer Overview KPIs: {kpis}")
        return kpis

    def get_basic_information(self) -> dict:
        """
        Extract Basic Information form values from Client Profile.
        """
        panel = self.page.locator(".chakra-tabs__tab-panel:not([hidden])").first
        def get_val(label_text: str, is_select: bool = False):
            field = panel.locator(f".chakra-form-control:has-text('{label_text}')")
            if field.count() == 0:
                return ""
            if is_select:
                select_elem = field.locator("select").first
                return select_elem.input_value() if select_elem.is_visible() else ""
            else:
                inp = field.locator("input, textarea").first
                return inp.input_value() if inp.count() > 0 and inp.is_visible() else ""

        return {
            "client_name": get_val("Client Name"),
            "industry": get_val("Industry", is_select=True),
            "website": get_val("Website"),
            "phone": get_val("Phone"),
            "email": get_val("Email"),
            "status": get_val("Status", is_select=True),
            "client_description": get_val("Client Description"),
        }

    def fill_basic_information(
        self,
        client_name: str = None,
        industry: str = None,
        website: str = None,
        phone: str = None,
        email: str = None,
        status: str = None,
        description: str = None,
    ):
        """Fill editable fields on Basic Information form."""
        logger.info("Filling Client Profile - Basic Information...")
        panel = self.page.locator(".chakra-tabs__tab-panel:not([hidden])").first

        if client_name is not None:
            inp = panel.locator(".chakra-form-control:has-text('Client Name') input").first
            if inp.is_visible():
                inp.fill(client_name)

        if industry is not None:
            sel = panel.locator(".chakra-form-control:has-text('Industry') select").first
            if sel.is_visible():
                try:
                    sel.select_option(label=industry)
                except Exception:
                    sel.select_option(value=industry)

        if website is not None:
            inp = panel.locator(".chakra-form-control:has-text('Website') input").first
            if inp.is_visible():
                inp.fill(website)

        if phone is not None:
            inp = panel.locator(".chakra-form-control:has-text('Phone') input").first
            if inp.is_visible():
                inp.fill(phone)

        if email is not None:
            inp = panel.locator(".chakra-form-control:has-text('Email') input").first
            if inp.is_visible():
                inp.fill(email)

        if status is not None:
            sel = panel.locator(".chakra-form-control:has-text('Status') select").first
            if sel.is_visible():
                sel.select_option(status)

        if description is not None:
            txt = panel.locator(".chakra-form-control:has-text('Client Description') textarea").first
            if txt.is_visible():
                txt.fill(description)

        self.page.wait_for_timeout(400)

    def save_basic_information(self):
        """Click 'Save Basic Information' button."""
        logger.info("Clicking 'Save Basic Information' button...")
        btn = self.page.locator("button:has-text('Save Basic Information')").first
        if btn.is_visible() and btn.is_enabled():
            btn.click()
            self.page.wait_for_timeout(1000)
            logger.info("Clicked 'Save Basic Information'.")
        else:
            logger.warning("Save Basic Information button not enabled or visible.")

    # -------------------------------------------------------------------------
    # CLIENT PROFILE: SUB-TAB 2 - BILLING ADDRESS
    # -------------------------------------------------------------------------

    def get_billing_address_data(self) -> dict:
        """Extract structured fields from Billing Address sub-tab."""
        panel = self.page.locator(".chakra-tabs__tab-panel:not([hidden])").first

        same_as_reg = panel.locator("label.chakra-checkbox:has-text('Same as Registered Address') input").is_checked()
        addr1 = panel.locator(".chakra-form-control:has-text('Address Line 1') input").input_value()
        addr2 = panel.locator(".chakra-form-control:has-text('Address Line 2') input").input_value()
        country = panel.locator(".chakra-form-control:has-text('Country') select").input_value()
        state = panel.locator(".chakra-form-control:has-text('State') select").input_value()
        city_sel = panel.locator(".chakra-form-control:has-text('City') select")
        city = city_sel.input_value() if city_sel.count() > 0 else ""
        postal = panel.locator(".chakra-form-control:has-text('Postal') input").input_value()
        
        pos_sel = panel.locator("div:has-text('Place of Supply') select").first
        place_of_supply = pos_sel.input_value() if pos_sel.count() > 0 and pos_sel.is_visible() else ""

        data = {
            "same_as_registered": same_as_reg,
            "address_line_1": addr1,
            "address_line_2": addr2,
            "country": country,
            "state": state,
            "city": city,
            "postal_code": postal,
            "place_of_supply": place_of_supply,
        }
        logger.info(f"Billing Address data: {data}")
        return data

    def fill_billing_address(
        self,
        same_as_registered: bool = None,
        address_line_1: str = None,
        address_line_2: str = None,
        country: str = None,
        state: str = None,
        city: str = None,
        postal_code: str = None,
        place_of_supply: str = None,
    ):
        """Populate fields on the Billing Address form."""
        logger.info("Populating Billing Address form...")
        panel = self.page.locator(".chakra-tabs__tab-panel:not([hidden])").first

        if same_as_registered is not None:
            chk = panel.locator("label.chakra-checkbox:has-text('Same as Registered Address')").first
            is_checked = panel.locator("label.chakra-checkbox:has-text('Same as Registered Address') input").is_checked()
            if is_checked != same_as_registered:
                chk.click()
                self.page.wait_for_timeout(400)

        if address_line_1 is not None:
            inp = panel.locator(".chakra-form-control:has-text('Address Line 1') input").first
            if inp.is_visible():
                inp.fill(address_line_1)

        if address_line_2 is not None:
            inp = panel.locator(".chakra-form-control:has-text('Address Line 2') input").first
            if inp.is_visible():
                inp.fill(address_line_2)

        if country is not None:
            sel = panel.locator(".chakra-form-control:has-text('Country') select").first
            if sel.is_visible():
                sel.select_option(country)
                self.page.wait_for_timeout(400)

        if state is not None:
            sel = panel.locator(".chakra-form-control:has-text('State') select").first
            if sel.is_visible():
                sel.select_option(state)
                self.page.wait_for_timeout(500)

        if city is not None:
            sel = panel.locator(".chakra-form-control:has-text('City') select").first
            if sel.is_visible() and sel.is_enabled():
                try:
                    sel.select_option(city)
                except Exception:
                    pass

        if postal_code is not None:
            inp = panel.locator(".chakra-form-control:has-text('Postal') input").first
            if inp.is_visible():
                inp.fill(postal_code)

        if place_of_supply is not None:
            pos_sel = panel.locator("div:has-text('Place of Supply') select").first
            if pos_sel.is_visible():
                pos_sel.select_option(place_of_supply)

        self.page.wait_for_timeout(400)

    def save_billing_address(self):
        """Click 'Save Billing Address' button."""
        logger.info("Clicking 'Save Billing Address'...")
        btn = self.page.locator("button:has-text('Save Billing Address')").first
        if btn.is_visible() and btn.is_enabled():
            btn.click()
            self.page.wait_for_timeout(1000)
            logger.info("Clicked 'Save Billing Address' ✓")
        else:
            logger.warning("Save Billing Address button is disabled or not visible.")

    # -------------------------------------------------------------------------
    # CLIENT PROFILE: SUB-TAB 3 - TAX & GST DETAILS
    # -------------------------------------------------------------------------

    def get_tax_gst_details_data(self) -> dict:
        """Extract structured fields from Tax & GST Details sub-tab."""
        panel = self.page.locator(".chakra-tabs__tab-panel:not([hidden])").first

        country_sel = panel.locator(".chakra-form-control:has-text('Country') select").first
        country = country_sel.input_value() if country_sel.count() > 0 else ""

        curr_sel = panel.locator(".chakra-form-control:has-text('Currency') select").first
        curr_val = curr_sel.input_value() if curr_sel.count() > 0 else ""
        curr_disabled = curr_sel.is_disabled() if curr_sel.count() > 0 else False

        # Radio selection: Yes, No, Not Sure
        radio_checked = "no"
        for val in ["yes", "no", "not_sure"]:
            r = panel.locator(f"input[type='radio'][value='{val}']")
            if r.count() > 0 and r.is_checked():
                radio_checked = val
                break

        data = {
            "country": country,
            "currency": curr_val,
            "is_currency_disabled": curr_disabled,
            "is_tax_registered": radio_checked,
        }
        logger.info(f"Tax & GST Details data: {data}")
        return data

    def select_tax_country(self, country_name: str):
        """Select Country in Tax & GST Details sub-tab."""
        logger.info(f"Selecting Tax & GST Country: '{country_name}'...")
        panel = self.page.locator(".chakra-tabs__tab-panel:not([hidden])").first
        sel = panel.locator(".chakra-form-control:has-text('Country') select").first
        if sel.is_visible():
            sel.select_option(country_name)
            self.page.wait_for_timeout(600)
            logger.info(f"Selected Tax Country '{country_name}'. Currency auto-derived.")

    def set_tax_registration(self, option: str = "yes"):
        """Select 'Yes', 'No', or 'Not Sure' for tax registration."""
        logger.info(f"Setting tax registration radio to: '{option}'...")
        panel = self.page.locator(".chakra-tabs__tab-panel:not([hidden])").first
        radio_label = panel.locator(f"label.chakra-radio:has(input[value='{option}']), label.chakra-radio:has-text('{option.title()}')").first
        if radio_label.is_visible():
            radio_label.click()
            self.page.wait_for_timeout(400)

    def save_tax_gst_details(self):
        """Click 'Save Tax & GST Details' button."""
        logger.info("Clicking 'Save Tax & GST Details'...")
        btn = self.page.locator("button:has-text('Save Tax & GST Details')").first
        if btn.is_visible() and btn.is_enabled():
            btn.click()
            self.page.wait_for_timeout(1000)
            logger.info("Clicked 'Save Tax & GST Details' ✓")
        else:
            logger.warning("Save Tax & GST Details button is disabled or not visible.")

    # -------------------------------------------------------------------------
    # CUSTOMER PROJECTS & INVOICES TABS
    # -------------------------------------------------------------------------

    def get_customer_projects_table(self) -> list:
        """Extract projects listed under Customer -> Projects tab."""
        self.switch_to_customer_tab("Projects")
        panel = self.page.locator(".chakra-tabs__tab-panel:not([hidden])").first
        rows = panel.locator("tbody tr").all()
        projects = []
        for r in rows:
            tds = [td.inner_text().strip() for td in r.locator("td").all()]
            if tds:
                projects.append(tds)
        logger.info(f"Customer associated projects: {projects}")
        return projects

    def get_customer_invoices_table(self) -> list:
        """Extract invoices listed under Customer -> Invoices tab."""
        self.switch_to_customer_tab("Invoices")
        panel = self.page.locator(".chakra-tabs__tab-panel:not([hidden])").first
        rows = panel.locator("tbody tr").all()
        invoices = []
        for r in rows:
            tds = [td.inner_text().strip() for td in r.locator("td").all()]
            if tds:
                invoices.append(tds)
        logger.info(f"Customer associated invoices: {invoices}")
        return invoices


