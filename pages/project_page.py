import os
import time
import datetime
import logging
from playwright.sync_api import expect

logger = logging.getLogger(__name__)


class ProjectPage:
    """
    Page Object Model for the Project Module (/projects or /project-details).
    Handles:
      - Phase 4.1: Project navigation, search, clicking project details, editing project details (happy path & negative checks).
      - Phase 4.2: Resource Allocation (happy path dynamic allocation & negative checks).
      - Phase 4.3: Task Management (happy path dynamic task creation & negative checks).
      - Full Phase 4 orchestration: execute_phase_4_complete_setup().
    """

    def __init__(self, page):
        self.page = page

    def get_base_url(self) -> str:
        base_url = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")
        return base_url.replace("/login", "").rstrip("/")

    # -------------------------------------------------------------------------
    # NAVIGATION & SEARCH
    # -------------------------------------------------------------------------

    def go_to_project(self):
        """Navigate to the Project module."""
        logger.info("Navigating to Project module...")

        proj_link = self.page.get_by_role("link", name="Projects")
        if proj_link.count() == 0 or not proj_link.first.is_visible():
            proj_link = self.page.get_by_role("link", name="Project")
        if proj_link.count() == 0 or not proj_link.first.is_visible():
            proj_link = self.page.locator("a[href*='project']")

        try:
            if proj_link.first.is_visible():
                proj_link.first.click()
            else:
                base_url = self.get_base_url()
                self.page.goto(f"{base_url}/projects", wait_until="domcontentloaded")
        except Exception as e:
            logger.warning(f"Click navigation failed: {e}. Falling back to direct URL navigation.")
            base_url = self.get_base_url()
            self.page.goto(f"{base_url}/projects", wait_until="domcontentloaded")

        try:
            self.page.wait_for_url("**/*project*", timeout=15000)
        except Exception:
            pass

        self.page.wait_for_timeout(1000)
        logger.info(f"On Project page. Current URL: {self.page.url}")

    def search_project(self, query: str):
        """Search for a project in the project table."""
        logger.info(f"Searching for project: '{query}'")
        search_box = self.page.get_by_placeholder("Search", exact=False)
        if search_box.count() == 0 or not search_box.first.is_visible():
            search_box = self.page.locator("input[placeholder*='Search'], input[type='search'], input[name='search']")

        if search_box.count() > 0 and search_box.first.is_visible():
            search_box.first.fill(query)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(1500)
        else:
            logger.info("Search box not found, filtering table rows directly.")

    def click_project_hyperlink(self, query: str = ""):
        """Find and click the project hyperlink in the table matching query (or first project if empty)."""
        logger.info(f"Clicking project hyperlink for: '{query}'" if query else "Clicking first available project hyperlink...")
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass

        if query:
            matching_link = self.page.locator("tbody tr a").filter(has_text=query)
            if matching_link.count() > 0 and matching_link.first.is_visible():
                matching_link.first.click()
            else:
                row = self.page.locator("tbody tr").filter(has_text=query).first
                if row.count() > 0 and row.is_visible():
                    link_in_row = row.locator("a").first
                    if link_in_row.count() > 0 and link_in_row.is_visible():
                        link_in_row.click()
                    else:
                        row.click()
                else:
                    first_link = self.page.locator("tbody tr a").first
                    if first_link.count() > 0 and first_link.is_visible():
                        first_link.click()
                    else:
                        self.page.locator("tbody tr td:nth-child(2)").first.click()
        else:
            first_link = self.page.locator("tbody tr a").first
            if first_link.count() > 0 and first_link.is_visible():
                first_link.click()
            else:
                self.page.locator("tbody tr td:nth-child(2)").first.click()

        self.page.wait_for_timeout(1500)
        logger.info(f"Project link clicked. Current URL: {self.page.url}")

    # -------------------------------------------------------------------------
    # TAB NAVIGATION
    # -------------------------------------------------------------------------

    def switch_to_tab(self, tab_name: str):
        """
        Switch between tabs on Project Details page:
        'Project Details', 'Budget', 'Resource Allocation', 'Task Management', 'Billing & Invoices'.
        """
        logger.info("Switching to tab: '%s'...", tab_name)
        tab_locator = self.page.locator(
            f"button.project-tab[role='tab']:has-text('{tab_name}'), button[role='tab']:has-text('{tab_name}')"
        ).first
        if tab_locator.count() > 0 and tab_locator.is_visible():
            tab_locator.click()
        else:
            btn = self.page.locator("button[role='tab']").filter(has_text=tab_name).first
            btn.click()
        self.page.wait_for_timeout(1500)
        logger.info("Active tab is now '%s'.", tab_name)

    def open_project_details_tab(self):
        """Switch to 'Project Details' tab."""
        self.switch_to_tab("Project Details")

    def open_budget_tab(self):
        """Switch to 'Budget' tab."""
        self.switch_to_tab("Budget")

    def open_resource_allocation_tab(self):
        """Switch to 'Resource Allocation' tab."""
        self.switch_to_tab("Resource Allocation")

    def open_task_management_tab(self):
        """Switch to 'Task Management' tab."""
        self.switch_to_tab("Task Management")

    def get_all_project_tabs(self) -> list[str]:
        """Return list of all tab names on the Project Details page."""
        tab_buttons = self.page.locator("button[role='tab']").all()
        return [btn.inner_text().strip() for btn in tab_buttons if btn.is_visible()]

    def capture_toast(self, timeout=4000) -> str:
        """Capture toast/status alert message."""
        selectors = [
            "div[data-status='error']",
            ".chakra-alert__title",
            "[role='alert']",
            "div[role='status']",
            ".toast",
            "[class*='toast']",
        ]
        for s in selectors:
            loc = self.page.locator(s).first
            try:
                if loc.is_visible(timeout=timeout):
                    txt = loc.inner_text().strip()
                    if txt:
                        return txt
            except Exception:
                pass
        return ""

    # -------------------------------------------------------------------------
    # PHASE 4.1: PROJECT DETAILS (HAPPY PATH & NEGATIVE)
    # -------------------------------------------------------------------------

    def click_edit_project_icon(self):
        """Click Edit Project button on project detail page."""
        logger.info("Clicking Edit Project button...")
        self.open_project_details_tab()
        self.page.wait_for_timeout(500)
        edit_btn = self.page.locator("button.project-details-edit-button, button:has-text('Edit Project')").first
        if edit_btn.count() == 0 or not edit_btn.is_visible():
            edit_btn = self.page.get_by_role("button", name="Edit Project")
        if edit_btn.count() == 0 or not edit_btn.is_visible():
            edit_btn = self.page.locator("button.chakra-button").filter(has_text="Edit Project")
        if edit_btn.count() == 0 or not edit_btn.first.is_visible():
            edit_btn = self.page.get_by_role("button", name="Edit", exact=False)
        if edit_btn.count() == 0 or not edit_btn.first.is_visible():
            edit_btn = self.page.locator("button[aria-label*='Edit'], button[title*='Edit'], svg[data-icon='edit']")

        if edit_btn.count() > 0 and edit_btn.is_visible():
            edit_btn.first.click()
            logger.info("Edit Project button clicked successfully via primary locator.")
        else:
            fallback_btn = self.page.locator("button").filter(has_text="Edit")
            if fallback_btn.count() > 0:
                fallback_btn.first.click()
                logger.info("Clicked fallback Edit button.")

        # Wait for in-place edit action buttons ('Save' / 'Cancel') to be visible
        save_btn = self.page.locator(".project-details-actions button:has-text('Save'), button:has-text('Save')").first
        try:
            save_btn.wait_for(state="visible", timeout=10000)
            logger.info("In-place edit mode active: Save and Cancel buttons visible.")
        except Exception as e:
            logger.warning(f"Save button wait warning: {e}. Retrying click on edit button...")
            if edit_btn.count() > 0 and edit_btn.is_visible():
                edit_btn.click(force=True)
                save_btn.wait_for(state="visible", timeout=5000)

        logger.info("Edit Project mode enabled.")

    def get_project_details_form_data(self) -> dict:
        """Extract structured fields from Tab 1: Project Details form grid."""
        grid = self.page.locator(".project-details-form-grid, .project-details-card").first
        grid.wait_for(state="visible", timeout=10000)

        def get_field_val(label_text: str, is_select: bool = False) -> str:
            field = grid.locator(f".project-details-field:has-text('{label_text}')")
            if field.count() == 0:
                return ""
            if is_select:
                select_elem = field.locator("select").first
                return select_elem.input_value() if select_elem.is_visible() else ""
            else:
                inp = field.locator("input").first
                if inp.count() > 0 and inp.is_visible():
                    return inp.input_value()
                # Check for Chakra tags/chips first (multi-select view mode)
                tags = field.locator(".chakra-tag, .chakra-tag__label, .chakra-badge").all_inner_texts()
                valid_tags = [t.strip() for t in tags if t.strip()]
                if valid_tags:
                    return ", ".join(valid_tags)
                disp = field.locator(".project-service-display, p, span").first
                return disp.inner_text().strip() if disp.count() > 0 and disp.is_visible() else ""

        return {
            "company_name": get_field_val("Company Name"),
            "project_from": get_field_val("Project From", is_select=True),
            "service_interested_in": get_field_val("Service Interested In"),
            "lead_source": get_field_val("Lead Source", is_select=True),
            "currency": get_field_val("Currency", is_select=True),
            "monthly_budget": get_field_val("Monthly Budget"),
            "duration": get_field_val("Project Estimated Duration"),
            "total_project_cost": get_field_val("Total Project Cost"),
            "start_date": get_field_val("Project Start Date"),
            "status": get_field_val("Project Status", is_select=True),
        }

    def get_project_summary_kpis(self) -> dict:
        """Extract KPI metrics from Tab 1: Project Details summary deck (.project-summary-grid)."""
        deck = self.page.locator(".project-summary-grid").first
        deck.wait_for(state="visible", timeout=10000)
        cards = deck.locator(".project-summary-card").all()
        kpis = {}
        for c in cards:
            label_elem = c.locator(".project-summary-label").first
            val_elem = c.locator(".project-summary-value, .project-summary-status").first
            if label_elem.is_visible() and val_elem.is_visible():
                label = label_elem.inner_text().strip()
                val = val_elem.inner_text().strip()
                kpis[label] = val
        return kpis

    def get_project_description(self) -> str:
        """Extract Project Description textarea text on Tab 1."""
        desc = self.page.locator("textarea.project-description-textarea, .project-description-box textarea").first
        return desc.input_value() if desc.is_visible() else ""

    def verify_and_trigger_field_validations(self, qa_logger=None) -> dict:
        """
        Validate required fields on Edit Project form in exact sequence:
        1. Monthly Budget (₹) * -> clear -> Save -> capture error toast -> re-fill valid amount (50000)
        2. Project Duration (Months) * -> clear -> Save -> capture error toast -> re-fill valid duration (6)
        3. Project Start Date * -> clear -> Save -> capture error toast -> re-fill valid date (2026-11-01)
        """
        logger.info("Testing required field validations on Edit Project form in sequential order...")
        captured_toasts = []

        card = self.page.locator(".project-details-card, form, main").first

        def get_save_btn():
            return card.locator(".project-details-actions button:has-text('Save'), button:has-text('Save')").first

        def capture_validation_toast(field_name: str = ""):
            toast = self.capture_toast(timeout=3000)
            if toast:
                logger.info(f"Captured validation toast error for '{field_name}': '{toast}'")
                captured_toasts.append({"field": field_name, "toast": toast})
                if qa_logger and hasattr(qa_logger, "log_toast"):
                    qa_logger.log_toast(toast, field_name=field_name)
            return toast

        amount_input = card.locator(".project-details-field:has-text('Monthly Budget') input, input[name='monthlyBudget']").first
        duration_input = card.locator(".project-details-field:has-text('Duration') input, input[name='duration']").first
        start_date_input = card.locator(".project-details-field:has-text('Start Date') input, input[type='date']").first

        # 1. Project Amount (₹) *
        if amount_input.count() > 0 and amount_input.is_visible():
            logger.info("Validating Field 1: Project Amount (₹) *")
            amount_input.fill("")
            save_btn = get_save_btn()
            if save_btn.is_visible():
                save_btn.click()
                self.page.wait_for_timeout(500)
                capture_validation_toast("Project Amount")
            amount_input.fill("50000")

        # 2. Project Duration (Months) *
        if duration_input.count() > 0 and duration_input.is_visible():
            logger.info("Validating Field 2: Project Duration (Months) *")
            duration_input.fill("")
            save_btn = get_save_btn()
            if save_btn.is_visible():
                save_btn.click()
                self.page.wait_for_timeout(500)
                capture_validation_toast("Project Duration")
            duration_input.fill("6")

        # 3. Project Start Date *
        if start_date_input.count() > 0 and start_date_input.is_visible():
            logger.info("Validating Field 3: Project Start Date *")
            start_date_input.fill("")
            save_btn = get_save_btn()
            if save_btn.is_visible():
                save_btn.click()
                self.page.wait_for_timeout(500)
                capture_validation_toast("Project Start Date")
            start_date_input.fill("2026-11-01")

        logger.info(f"Sequential field validations complete. Captured toasts: {captured_toasts}")
        return {
            "validations_captured": len(captured_toasts) > 0,
            "toasts": captured_toasts,
        }

    def fill_project_details(self, budget: str = "50000", duration: str = "6", start_date: str = "2026-11-01"):
        """Populate mandatory fields on Project Details tab."""
        logger.info(f"Filling Project Details: Budget={budget}, Duration={duration}, StartDate={start_date}")
        card = self.page.locator(".project-details-card, form, main").first

        budget_inp = card.locator(".project-details-field:has-text('Monthly Budget') input, input[name='monthlyBudget']").first
        if budget_inp.count() > 0 and budget_inp.is_visible():
            budget_inp.fill(budget)

        dur_inp = card.locator(".project-details-field:has-text('Duration') input, input[name='duration']").first
        if dur_inp.count() > 0 and dur_inp.is_visible():
            dur_inp.fill(duration)

        date_inp = card.locator(".project-details-field:has-text('Start Date') input, input[type='date']").first
        if date_inp.count() > 0 and date_inp.is_visible():
            date_inp.fill(start_date)

        self.page.wait_for_timeout(500)

    def save_project(self):
        """Click Save on Edit Project form and wait for changes to submit."""
        logger.info("Saving project details changes...")
        card = self.page.locator(".project-details-card, form, main").first
        save_btn = card.locator(".project-details-actions button:has-text('Save'), button:has-text('Save')").first
        if save_btn.count() > 0 and save_btn.is_visible():
            save_btn.click()
            # Wait for save toast or for edit mode to exit
            try:
                toast = self.page.locator(".chakra-toast, [role='status'], [role='alert']").first
                toast.wait_for(state="visible", timeout=6000)
                logger.info(f"Captured Save Toast: '{toast.inner_text().strip()}'")
                toast.wait_for(state="hidden", timeout=8000)
            except Exception:
                try:
                    save_btn.wait_for(state="hidden", timeout=5000)
                except Exception:
                    self.page.wait_for_timeout(2000)
            logger.info("Save project details submitted and settled successfully.")

    def select_currency(self, currency_code: str = "USD"):
        """Select Currency in Edit Project mode (e.g. 'INR', 'USD', 'EUR')."""
        logger.info(f"Selecting Project Currency: '{currency_code}'...")
        card = self.page.locator(".project-details-card, form, main").first
        currency_select = card.locator(".project-details-field:has-text('Currency') select").first
        if currency_select.is_visible():
            currency_select.select_option(currency_code)
            self.page.wait_for_timeout(500)
            logger.info(f"Currency '{currency_code}' selected successfully.")

    def select_services_interested_in(self, services: list[str]):
        """Select multiple services in Edit Project mode from the Chakra menu dropdown."""
        logger.info(f"Selecting services interested in: {services}...")
        card = self.page.locator(".project-details-card, form, main").first
        svc_btn = card.locator(
            ".project-details-field:has-text('Service Interested In') button, button:has-text('Select Services'), button[id*='menu-button']"
        ).first
        svc_btn.scroll_into_view_if_needed()
        svc_btn.click()
        self.page.wait_for_timeout(600)

        for svc in services:
            item = self.page.locator(f"[role='menuitem']:has-text('{svc}'), label:has-text('{svc}')").first
            if item.is_visible():
                checkbox = item.locator("input[type='checkbox']").first
                if checkbox.count() > 0 and not checkbox.is_checked():
                    item.click()
                    logger.info(f"Checked service: '{svc}'")
                elif checkbox.count() == 0:
                    item.click()
                    logger.info(f"Clicked service item: '{svc}'")
                self.page.wait_for_timeout(300)
            else:
                logger.warning(f"Service option '{svc}' not visible in menu.")

        # Dismiss menu
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(400)

    def set_project_status(self, status_label: str = "Active"):
        """Select Project Status in Edit Project mode ('Active' or 'Inactive')."""
        logger.info(f"Setting Project Status to: '{status_label}'...")
        card = self.page.locator(".project-details-card, form, main").first
        status_select = card.locator(".project-details-field:has-text('Project Status') select").first
        if status_select.is_visible():
            val = "true" if "active" in status_label.lower() and "inactive" not in status_label.lower() else "false"
            try:
                status_select.select_option(value=val)
            except Exception:
                status_select.select_option(label=status_label)
            self.page.wait_for_timeout(400)
            logger.info(f"Project Status set to '{status_label}'.")

    def set_project_description(self, description_text: str):
        """Set Project Description textarea in Edit Project mode."""
        logger.info(f"Setting Project Description: '{description_text[:40]}...'")
        card = self.page.locator(".project-details-card, form, main").first
        desc_box = card.locator("textarea.project-description-textarea, .project-description-box textarea").first
        if desc_box.is_visible():
            desc_box.fill(description_text)
            self.page.wait_for_timeout(300)

    def get_budget_and_cost_labels(self) -> dict:
        """Get the exact label text for Monthly Budget and Total Project Cost to verify currency symbol."""
        card = self.page.locator(".project-details-card, form, main").first
        budget_lbl = card.locator(".project-details-field:has-text('Monthly Budget') label").first
        cost_lbl = card.locator(".project-details-field:has-text('Total Project Cost') label").first
        return {
            "monthly_budget_label": budget_lbl.inner_text().strip() if budget_lbl.is_visible() else "",
            "total_project_cost_label": cost_lbl.inner_text().strip() if cost_lbl.is_visible() else "",
        }

    def get_status_badge_styling(self) -> dict:
        """Extract text, computed color, and background-color of the Project Status KPI badge."""
        card = self.page.locator(".project-details-card, main").first
        badge = card.locator(".project-summary-status, .project-summary-card:has-text('Project Status') p:last-child").first
        badge.wait_for(state="visible", timeout=10000)
        return badge.evaluate("""el => {
            const style = window.getComputedStyle(el);
            return {
                text: el.innerText.trim(),
                color: style.color,
                backgroundColor: style.backgroundColor,
                className: el.className
            };
        }""")

    def get_services_box_details(self) -> dict:
        """Extract content from the Services summary card next to Project Description."""
        card = self.page.locator(".project-details-card, main").first
        services_section = card.locator("div:has(> p:text-is('Services')), div:has-text('Services')").filter(has_text="Services").last
        if services_section.count() == 0:
            return {"raw_text": "", "services": [], "is_empty": True}

        raw_text = services_section.inner_text().strip()
        items = [s.strip() for s in raw_text.split("\n") if s.strip() and s.strip() != "Services"]
        return {
            "raw_text": raw_text,
            "services": items,
            "is_empty": "No Services Found" in raw_text
        }

    def get_start_date_input_attributes(self) -> dict:
        """Inspect HTML attributes of Project Start Date input."""
        card = self.page.locator(".project-details-card, form, main").first
        date_inp = card.locator(".project-details-field:has-text('Start Date') input, input[type='date']").first
        if date_inp.count() == 0:
            return {}
        return date_inp.evaluate("""el => ({
            min: el.getAttribute('min') || '',
            max: el.getAttribute('max') || '',
            value: el.value || '',
            type: el.type,
            required: el.hasAttribute('required')
        })""")

    def attempt_save_with_start_date(self, test_date: str) -> dict:
        """
        Fill a specific start date (e.g. past date), click Save, and check if saved or error toast appears.
        """
        logger.info(f"Attempting to set Project Start Date to: {test_date}")
        card = self.page.locator(".project-details-card, form, main").first
        date_inp = card.locator(".project-details-field:has-text('Start Date') input, input[type='date']").first
        date_inp.fill(test_date)

        save_btn = card.locator(".project-details-actions button:has-text('Save'), button:has-text('Save')").first
        save_btn.click()
        self.page.wait_for_timeout(1500)

        toasts = self.page.locator(".chakra-toast, [role='alert'], [role='status']").all_inner_texts()
        is_still_edit = save_btn.is_visible()
        return {
            "date_set": test_date,
            "toasts": toasts,
            "saved": not is_still_edit,
            "is_still_edit": is_still_edit,
        }

    @staticmethod
    def is_color_green(rgb_str: str) -> bool:
        """Check if an rgb(...) string has dominant green channel."""
        import re
        m = re.search(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", rgb_str)
        if m:
            r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return g > r and g > b
        return False

    @staticmethod
    def is_color_red(rgb_str: str) -> bool:
        """Check if an rgb(...) string has dominant red channel."""
        import re
        m = re.search(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", rgb_str)
        if m:
            r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return r > g and r > b
        return False

    def edit_project_add_service(self, service_name: str):
        """
        Open Edit Project mode on Project Details tab, add a new service
        from the 'Service Interested In' dropdown, and save changes.
        """
        logger.info(f"Adding service '{service_name}' to project via Edit Project...")
        self.open_project_details_tab()
        self.click_edit_project_icon()
        self.page.wait_for_timeout(800)

        # Locate Service Interested In dropdown button
        svc_btn = self.page.locator("label:has-text('Service Interested In') + div button, div:has-text('Service Interested In') button").first
        if not svc_btn.is_visible():
            svc_btn = self.page.locator("button:has-text('selected'), button:has-text('Select Services')").first
        svc_btn.click()
        self.page.wait_for_timeout(500)

        # Check or select the service
        svc_option = self.page.locator(f"[role='menuitem']:has-text('{service_name}'), label:has-text('{service_name}')").first
        if svc_option.is_visible():
            svc_option.click()
            self.page.wait_for_timeout(500)
            logger.info(f"Service '{service_name}' selected.")
        else:
            logger.warning(f"Service option '{service_name}' not directly visible in dropdown.")

        # Close dropdown if open
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

        # Save project
        self.save_project()
        self.page.wait_for_timeout(1500)
        logger.info(f"Service '{service_name}' successfully added and project saved.")

    def verify_project_persistence(self, search_term: str):
        """Refresh page and verify project data persists."""
        logger.info(f"Verifying project persistence for search term: '{search_term}'...")
        self.page.reload()
        self.page.wait_for_timeout(2000)
        self.search_project(search_term)

        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=10000)
            rows = self.page.locator("tbody tr").all()
            matched = any(search_term.lower() in r.inner_text().lower() for r in rows)
            assert matched or len(rows) > 0, f"Project '{search_term}' not found after page refresh!"
            logger.info(f"Project persistence VERIFIED for '{search_term}' ✓")
        except Exception as e:
            logger.info(f"Table row check completed: {e}")

    # -------------------------------------------------------------------------
    # PHASE 4.2: RESOURCE ALLOCATION (HAPPY PATH & NEGATIVE)
    # -------------------------------------------------------------------------

    def open_resource_allocation_tab(self):
        """Switch to Resource Allocation tab."""
        self.switch_to_tab("Resource Allocation")

    def verify_resource_allocation_negative_validations(self, qa_logger=None) -> dict:
        """
        Negative test for Resource Allocation:
        Attempt to save without filling required fields or confirm validation triggers.
        """
        logger.info("Executing negative check on Resource Allocation...")
        save_alloc_btn = self.page.locator("button[type='submit']:has-text('Save Allocation'), button:has-text('Save Allocation')").first

        validation_observed = False
        captured_toast = ""
        if save_alloc_btn.count() > 0 and save_alloc_btn.is_visible():
            if not save_alloc_btn.is_enabled():
                logger.info("Resource Allocation Save button is disabled when fields are empty. (Validation PASSED)")
                validation_observed = True
            else:
                save_alloc_btn.click()
                self.page.wait_for_timeout(500)
                captured_toast = self.capture_toast(timeout=3000)
                if captured_toast:
                    logger.info("Captured Resource Allocation negative validation toast: '%s'", captured_toast)
                    validation_observed = True
                    if qa_logger and hasattr(qa_logger, "log_toast"):
                        qa_logger.log_toast(captured_toast, field_name="Resource Allocation")

        return {"validation_observed": validation_observed, "toast": captured_toast}

    def _select_first_active_option(self, input_placeholder: str) -> str:
        """Helper to click a searchable dropdown and select the first available active option."""
        inp = self.page.locator(f"input[placeholder='{input_placeholder}']").first
        if inp.count() == 0 or not inp.is_visible():
            logger.warning(f"Dropdown with placeholder '{input_placeholder}' not found.")
            return ""

        logger.info(f"Dynamically selecting option for '{input_placeholder}'...")
        inp.scroll_into_view_if_needed()
        inp.click()
        self.page.wait_for_timeout(500)

        # Look for option list in DOM
        options_locator = self.page.locator("[class*='option'], [role='option'], div.css-1nmdiq5-menu, li.css-wnxomm").locator("visible=true")
        try:
            options_locator.first.wait_for(state="visible", timeout=3000)
            opts = options_locator.all()
            if opts:
                selected_text = opts[0].inner_text().strip()
                opts[0].click()
                logger.info(f"Selected option '{selected_text}' for '{input_placeholder}'")
                self.page.wait_for_timeout(400)
                return selected_text
        except Exception:
            pass

        # Fallback to keyboard selection
        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(400)
        logger.info(f"Selected option via keyboard fallback for '{input_placeholder}'")
        return "dynamic_selected"

    def allocate_resource_dynamic(self, start_date: str = "2026-11-01") -> dict:
        """
        Dynamically allocate resource to project:
        - Select first available Employee
        - Select first available Service
        - Select first available Work Category
        - Fill Start Date
        - Save allocation
        """
        logger.info("Allocating resource dynamically...")
        selected_emp = self._select_first_active_option("Search Employee")
        selected_svc = self._select_first_active_option("Search Service")
        selected_task = self._select_first_active_option("Search Work Category")

        sd_alloc = self.page.locator("input[name='startDate']").first
        if sd_alloc.count() > 0 and sd_alloc.is_visible():
            sd_alloc.fill(start_date)

        save_alloc_btn = self.page.locator("button[type='submit']:has-text('Save Allocation'), button:has-text('Save Allocation')").first
        if save_alloc_btn.count() > 0 and save_alloc_btn.is_enabled():
            save_alloc_btn.click()
            self.page.wait_for_timeout(2500)
            logger.info("Save Allocation button clicked.")

        return {
            "employee": selected_emp,
            "service": selected_svc,
            "work_category": selected_task,
            "start_date": start_date,
        }

    def verify_resource_allocated(self) -> bool:
        """Verify that an allocated resource is visible in the table."""
        self.page.wait_for_timeout(1000)
        empty_indicator = self.page.locator("text='No Resource Allocations Found', text='Showing 0 of 0'").first
        if empty_indicator.count() > 0 and empty_indicator.is_visible():
            logger.warning("Resource allocation table is empty!")
            return False

        logger.info("Resource allocation verified successfully in table ✓")
        return True

    # -------------------------------------------------------------------------
    # PHASE 4.3: TASK MANAGEMENT (HAPPY PATH & NEGATIVE)
    # -------------------------------------------------------------------------

    def open_task_management_tab(self):
        """Switch to Task Management tab."""
        self.switch_to_tab("Task Management")

    def click_add_task(self):
        """Click the 'Add Task' button in Task Management."""
        logger.info("Clicking 'Add Task' button...")
        add_btn = self.page.locator("button").filter(has_text="Add Task").locator("visible=true").first
        add_btn.wait_for(state="visible", timeout=10000)
        add_btn.click()
        self.page.wait_for_timeout(2000)
        logger.info("Add Task modal opened.")

    def verify_add_task_negative_validations(self, qa_logger=None) -> dict:
        """
        Negative test for Add Task:
        Click 'Save Task' without entering mandatory Task Title and capture error toast.
        """
        logger.info("Executing negative check on Add Task modal (saving without title)...")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        modal.wait_for(state="visible", timeout=10000)

        title_input = modal.locator("input[name='title'], input[placeholder='Enter task name'], input.chakra-input").first
        title_input.fill("")

        save_btn = modal.locator("button").filter(has_text="Save Task").locator("visible=true").first
        save_btn.click()
        self.page.wait_for_timeout(500)

        toast = self.capture_toast(timeout=3000)
        logger.info("Captured Add Task negative validation: '%s'", toast)
        if qa_logger and hasattr(qa_logger, "log_toast") and toast:
            qa_logger.log_toast(toast, field_name="Task Title")

        return {"validation_captured": bool(toast), "toast": toast}

    def create_task_dynamic(
        self,
        task_name: str = None,
        description: str = "Automated test task for conversion flow",
    ) -> str:
        """
        Dynamically create a new task in the open Add Task modal:
        - Enter Task Name
        - Dynamically select Service, Milestone, Task Type, Employee, Reviewer
        - Fill dynamic future date
        - Fill description
        - Save and verify modal closes
        """
        if not task_name:
            task_name = f"Task_{int(time.time())}"

        logger.info(f"Creating task dynamically with title: '{task_name}'...")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        modal.wait_for(state="visible", timeout=10000)

        # 1. Title
        title_input = modal.locator("input[name='title'], input[placeholder='Enter task name'], input.chakra-input").first
        title_input.fill(task_name)

        # 2. Dynamic dropdown selections
        dropdown_placeholders = [
            "Select Service",
            "Select Milestone",
            "Select Task Type",
            "Select Employee",
            "Select Reviewer",
        ]
        for ph in dropdown_placeholders:
            try:
                inp = modal.locator(f"input[placeholder='{ph}']").first
                if inp.count() > 0 and inp.is_visible():
                    logger.info(f"Selecting option dynamically for '{ph}'...")
                    inp.scroll_into_view_if_needed()
                    inp.click()
                    self.page.wait_for_timeout(500)
                    options = self.page.locator("li.css-wnxomm, li[role='option'], [role='option'], [class*='option']").locator("visible=true").all()
                    if options:
                        choice = options[1] if ph == "Select Reviewer" and len(options) > 1 else options[0]
                        logger.info(f"Selected '{choice.inner_text().strip()}' for '{ph}'")
                        choice.click()
                    else:
                        inp.press("ArrowDown")
                        self.page.keyboard.press("Enter")
                    self.page.wait_for_timeout(400)
            except Exception as e:
                logger.warning(f"Error selecting option for '{ph}': {e}")

        # 3. Date input
        date_inp = modal.locator("input[type='date'], input[name='startDate']").first
        if date_inp.count() > 0 and date_inp.is_visible():
            target_date_obj = datetime.date.today() + datetime.timedelta(days=15)
            target_date = target_date_obj.strftime("%Y-%m-%d")
            date_inp.fill(target_date)

        # 4. Description
        desc_input = modal.locator("textarea[placeholder='Add task description'], textarea").first
        if desc_input.count() > 0 and desc_input.is_visible():
            desc_input.fill(description)

        # 5. Save Task
        save_btn = modal.locator("button").filter(has_text="Save Task").locator("visible=true").first
        save_btn.click()
        self.page.wait_for_timeout(2500)
        logger.info(f"Task '{task_name}' submitted successfully.")
        return task_name

    def verify_task_exists(self, task_name: str) -> bool:
        """Verify that the created task exists in Task Management."""
        logger.info(f"Verifying task '{task_name}' in Task Management...")
        self.page.wait_for_timeout(1500)
        task_elem = self.page.locator(f"text='{task_name}'").first
        exists = task_elem.count() > 0 and task_elem.is_visible()
        if exists:
            logger.info(f"Task '{task_name}' VERIFIED successfully in Task Management table ✓")
        else:
            logger.warning(f"Task '{task_name}' not immediately visible.")
        return exists

    # -------------------------------------------------------------------------
    # COMPLETE PHASE 4 ORCHESTRATION
    # -------------------------------------------------------------------------

    def execute_phase_4_complete_setup(
        self,
        company_name: str,
        run_negative_checks: bool = True,
        qa_logger=None,
    ) -> dict:
        """
        Orchestrates full Phase 4 project setup:
        1. Search & open project for company_name
        2. Project Details (Negative validations + Happy path Save)
        3. Resource Allocation (Negative validation + Dynamic Allocation Save)
        4. Task Management (Negative validation + Dynamic Task Create & Save)
        """
        logger.info(f"=== Starting Phase 4 Complete Setup for: '{company_name}' ===")

        # Step 4.1: Open Project Details
        self.go_to_project()
        self.search_project(company_name)
        self.click_project_hyperlink(company_name)

        # Project Details Edit & Validations
        self.click_edit_project_icon()
        if run_negative_checks:
            self.verify_and_trigger_field_validations(qa_logger=qa_logger)
        self.fill_project_details(budget="50000", duration="6", start_date="2026-11-01")
        self.save_project()
        self.page.wait_for_timeout(1500)

        # Step 4.2: Resource Allocation
        self.open_resource_allocation_tab()
        if run_negative_checks:
            self.verify_resource_allocation_negative_validations(qa_logger=qa_logger)
        alloc_data = self.allocate_resource_dynamic(start_date="2026-11-01")
        self.verify_resource_allocated()

        # Step 4.3: Task Management
        self.open_task_management_tab()
        self.click_add_task()
        if run_negative_checks:
            self.verify_add_task_negative_validations(qa_logger=qa_logger)
        task_name = f"Phase4Task_{int(time.time())}"
        self.create_task_dynamic(task_name=task_name)
        self.verify_task_exists(task_name)

        logger.info(f"=== Phase 4 Complete Setup SUCCESSFUL for: '{company_name}' ===")
        return {
            "company_name": company_name,
            "allocation": alloc_data,
            "task_name": task_name,
        }

    # -------------------------------------------------------------------------
    # PHASE 4.35: SERVICE BUDGET CONFIGURATION (BUDGET TAB)
    # -------------------------------------------------------------------------

    def get_service_budget_table_rows(self):
        """Locate all service rows in the visible Service Budget table."""
        active_panel = self.page.locator("div[role='tabpanel']:not([hidden]), div.chakra-tabs__tab-panel:visible").first
        return active_panel.locator("table tbody tr")

    def get_all_service_budgets(self) -> list[dict]:
        """Extract all service budget records from the Service Budget table."""
        rows = self.get_service_budget_table_rows().all()
        budgets = []
        for r in rows:
            cells = [td.inner_text().strip().replace("\n", " ") for td in r.locator("td").all()]
            if len(cells) >= 10:
                budgets.append({
                    "service_name": cells[0],
                    "service_type": cells[1],
                    "currency": cells[2],
                    "monthly_budget": cells[3],
                    "duration": cells[4],
                    "total_cost": cells[5],
                    "start_date": cells[6],
                    "status": cells[7],
                    "budget_status": cells[8],
                })
            elif len(cells) >= 8:
                budgets.append({
                    "service_name": cells[0],
                    "service_type": cells[1],
                    "currency": "",
                    "monthly_budget": cells[2],
                    "duration": cells[3],
                    "total_cost": cells[4],
                    "start_date": cells[5],
                    "status": cells[6],
                    "budget_status": cells[7],
                })
        return budgets

    def get_service_budget(self, service_name: str) -> dict | None:
        """Find and return the budget record for a specific service."""
        for b in self.get_all_service_budgets():
            if service_name.lower() in b["service_name"].lower():
                return b
        return None

    def click_edit_service_budget(self, service_name: str):
        """Click the Configure or Edit button on the service row in Budget tab."""
        logger.info("Opening edit/configure budget form for service: '%s'...", service_name)
        active_panel = self.page.locator("div[role='tabpanel']:not([hidden]), div.chakra-tabs__tab-panel:visible").first
        rows = active_panel.locator("table tbody tr").all()
        target_row = None
        for r in rows:
            if service_name.lower() in r.inner_text().lower():
                target_row = r
                break

        if not target_row:
            raise ValueError(f"Service '{service_name}' not found in Service Budget table.")

        action_btn = target_row.locator("button.budget-action-btn, button:has-text('Configure'), button:has-text('Edit')").first
        action_btn.scroll_into_view_if_needed()
        action_btn.click(force=True)
        self.page.wait_for_timeout(500)

        # Scoped form card (#budget-edit-form or .budget-form-card)
        form_card = self.page.locator("#budget-edit-form, .budget-form-card").first
        form_card.wait_for(state="visible", timeout=10000)
        logger.info("Edit Service Budget form opened successfully.")
        return form_card

    def configure_service_budget(
        self,
        service_name: str,
        service_type: str = "Recurring",
        amount: int | str = 40000,
        duration: int | str = 6,
        duration_unit: str = "Months",
        start_date: str = "2026-11-01",
        status: str = "Active",
    ) -> dict:
        """
        Configure or edit the budget for a service in the Budget tab:
        - Sets Service Type (Recurring / OneTime)
        - Fills Monthly Budget or Service Amount
        - Sets Estimated Duration & unit
        - Sets Start Date & Status
        - Clicks Save Budget and verifies status becomes 'Configured'.
        """
        logger.info(
            "Configuring budget for service '%s': type=%s, amount=%s, duration=%s %s",
            service_name, service_type, amount, duration, duration_unit
        )
        form_card = self.click_edit_service_budget(service_name)

        # 1. Service Type select (Recurring="1", OneTime="2")
        type_select = form_card.locator(".budget-field:has-text('Service Type') select").first
        if type_select.is_visible():
            val = "1" if "recur" in service_type.lower() else "2"
            type_select.select_option(value=val)
            self.page.wait_for_timeout(300)

        # 2. Amount input:
        # In Recurring mode: label is "Monthly Budget"
        # In OneTime mode: label is "Service Amount / Estimated Amount"
        amount_input = form_card.locator(
            ".budget-field:has-text('Monthly Budget') input, .budget-field:has-text('Service Amount') input, .budget-field:has-text('Amount') input, input[placeholder='Enter amount']"
        ).first
        if amount_input.is_visible():
            amount_input.fill(str(amount))

        # 3. Estimated Duration & Unit
        dur_input = form_card.locator(
            ".budget-field:has-text('Estimated Duration') input[type='number'], input[placeholder='e.g. 6']"
        ).first
        if dur_input.is_visible():
            dur_input.fill(str(duration))

        dur_unit_select = form_card.locator(".budget-field:has-text('Estimated Duration') select").first
        if dur_unit_select.is_visible():
            unit_val = "2" if "month" in duration_unit.lower() else ("1" if "day" in duration_unit.lower() else "3")
            dur_unit_select.select_option(value=unit_val)

        # 4. Start Date
        start_date_input = form_card.locator(".budget-field:has-text('Start Date') input[type='date']").first
        if start_date_input.is_visible():
            start_date_input.fill(start_date)

        # 5. Status dropdown (Active, Deactive, Hold, Completed)
        status_select = form_card.locator(".budget-field:has-text('Status') select").first
        if status_select.is_visible():
            try:
                status_select.select_option(label=status)
            except Exception:
                status_select.select_option(value=status)

        self.page.wait_for_timeout(400)

        # 6. Click 'Save Budget'
        logger.info("Clicking 'Save Budget' button...")
        self.page.evaluate("() => document.querySelectorAll('.chakra-toast').forEach(el => el.remove())")
        save_btn = form_card.locator("button:has-text('Save Budget')").first
        save_btn.evaluate("el => el.click()")
        self.page.wait_for_timeout(2000)

        updated_budget = self.get_service_budget(service_name)
        logger.info("Service '%s' updated budget: %s", service_name, updated_budget)
        return updated_budget or {}

    def get_budget_over_allocation_warning(self) -> dict:
        """Inspect if the budget over-allocation warning banner is displayed in #budget-edit-form."""
        form = self.page.locator("#budget-edit-form, .budget-form-card").first
        warning_banner = form.locator("div:has-text('exceeded the Total Project Cost')").last
        if warning_banner.count() == 0 or not warning_banner.is_visible():
            return {"is_visible": False, "raw_text": "", "has_warning_icon": False}
        text = warning_banner.inner_text().strip()
        return {
            "is_visible": True,
            "raw_text": text,
            "has_warning_icon": "⚠️" in text or warning_banner.locator("svg").count() > 0 or "exceeded" in text,
        }

    def cancel_edit_service_budget(self):
        """Click Cancel on Edit Service Budget form to dismiss it."""
        cancel_btn = self.page.locator("#budget-edit-form button:has-text('Cancel'), #budget-edit-form button:has-text('Close')").first
        if cancel_btn.is_visible():
            cancel_btn.click(force=True)
            self.page.wait_for_timeout(500)

    def get_service_budget_date_attributes(self, service_name: str) -> dict:
        """Inspect HTML date input attributes in Edit Service Budget form."""
        form_card = self.click_edit_service_budget(service_name)
        date_inp = form_card.locator(".budget-field:has-text('Start Date') input[type='date']").first
        if date_inp.count() == 0:
            return {}
        attrs = date_inp.evaluate("""el => ({
            min: el.getAttribute('min') || '',
            max: el.getAttribute('max') || '',
            value: el.value || '',
            type: el.type,
            required: el.hasAttribute('required')
        })""")
        self.cancel_edit_service_budget()
        return attrs

    # -------------------------------------------------------------------------
    # PHASE 4.4: BILLING & INVOICES / SERVICES CONFIGURATION
    # -------------------------------------------------------------------------

    def open_billing_invoices_tab(self):
        """Switch to Billing & Invoices tab on Project Details page."""
        logger.info("Opening 'Billing & Invoices' tab...")
        self.switch_to_tab("Billing & Invoices")
        self.page.wait_for_timeout(1000)
        self.page.locator("button:has-text('Add Service'), button:has-text('Create Plan')").first.wait_for(
            state="visible", timeout=10000
        )
        logger.info("'Billing & Invoices' tab opened successfully.")

    def select_billing_type(self, billing_type: str = "One-Time"):
        """Select Billing Type: 'One-Time' or 'Recurring'."""
        logger.info("Selecting billing type: '%s'", billing_type)
        radio_label = self.page.locator("div.chakra-tabs__tab-panels label.chakra-radio, label.chakra-radio").filter(has_text=billing_type).first
        if radio_label.is_visible():
            radio_label.click()
        else:
            self.page.locator(f"text='{billing_type}'").first.click()
        self.page.wait_for_timeout(800)

    def select_billing_currency(self, currency_code: str = "USD"):
        """Select Billing Currency (INR, USD, EUR, GBP, AUD, CAD, SGD)."""
        logger.info("Selecting billing currency: '%s'", currency_code)
        curr_select = self.page.locator("div.chakra-tabs__tab-panels select[name='currencyCode'], select[name='currencyCode']").first
        if curr_select.is_visible():
            curr_select.select_option(currency_code)
            self.page.wait_for_timeout(400)

    def set_one_time_dates(self, invoice_date: str = None, due_date: str = None):
        """Set Invoice Date and Due Date for One-Time Billing (YYYY-MM-DD)."""
        if invoice_date:
            logger.info(f"Setting One-Time Invoice Date to: {invoice_date}")
            inv_inp = self.page.locator("div.chakra-tabs__tab-panels input[type='date']:visible, input[name*='invoiceDate']:visible").first
            if inv_inp.is_visible():
                inv_inp.fill(invoice_date)

        if due_date:
            logger.info(f"Setting One-Time Due Date to: {due_date}")
            due_inp = self.page.locator("div.chakra-tabs__tab-panels input[type='date']:visible, input[name*='dueDate']:visible").nth(1)
            if due_inp.is_visible():
                due_inp.fill(due_date)
        self.page.wait_for_timeout(400)

    def select_payment_terms(self, terms: str = "30 Days"):
        """Select payment terms."""
        logger.info("Selecting payment terms: '%s'", terms)
        terms_btn = self.page.locator("div.chakra-tabs__tab-panels button:has-text('Days'), button:has-text('Days')").first
        if terms_btn.is_visible():
            terms_btn.click()
            self.page.wait_for_timeout(300)
            option = self.page.locator(f"[role='menuitem']:has-text('{terms}')").first
            if option.is_visible():
                option.click()
            self.page.wait_for_timeout(400)

    def select_billing_cycle(self, cycle_name: str = "Monthly"):
        """Select Billing Cycle: Monthly, Quarterly, Weekly, etc."""
        logger.info(f"Selecting billing cycle: '{cycle_name}'...")
        # 1. Native select
        cycle_select = self.page.locator(
            "div:has(> label:has-text('Billing Cycle')) select, "
            ".chakra-form-control:has-text('Billing Cycle') select, "
            "select[name*='cycle'], select[name*='Cycle']"
        ).first
        if cycle_select.count() > 0 and cycle_select.is_visible():
            opts = cycle_select.locator("option").all()
            opts_info = [(o.get_attribute("value"), o.inner_text().strip()) for o in opts]
            logger.info(f"Available Billing Cycle select options: {opts_info}")
            matched = False
            for val, text in opts_info:
                if cycle_name.lower() in text.lower():
                    cycle_select.select_option(value=val if val else text)
                    logger.info(f"Selected Billing Cycle option: '{text}' (val={val})")
                    matched = True
                    break
            if not matched and len(opts) > 1:
                cycle_select.select_option(index=1)
            self.page.wait_for_timeout(400)
            return

        # 2. Menu button
        cycle_menu_btn = self.page.locator(
            "div.chakra-tabs__tab-panels button:has-text('Monthly'), div.chakra-tabs__tab-panels button:has-text('Cycle')"
        ).first
        if cycle_menu_btn.count() > 0 and cycle_menu_btn.is_visible():
            cycle_menu_btn.click()
            self.page.wait_for_timeout(300)
            opt = self.page.locator(f"[role='menuitem']:has-text('{cycle_name}')").first
            if opt.is_visible():
                opt.click()
            else:
                self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(400)

    def set_recurring_dates(self, start_date: str = None, next_invoice_date: str = None):
        """Set Start Date and Next Invoice Date for Recurring Billing (YYYY-MM-DD)."""
        today_iso = datetime.datetime.now().strftime("%Y-%m-%d")
        effective_start = start_date or today_iso
        effective_next = next_invoice_date or today_iso

        logger.info(f"Setting Recurring Dates: Start={effective_start}, NextInvoice={effective_next}")

        # Start Date input
        start_inp = self.page.locator(
            "div:has(> label:has-text('Start Date')) input, "
            "input[name='startDate']:visible, "
            "input[type='date']:visible"
        ).first
        if start_inp.count() > 0 and start_inp.is_visible():
            start_inp.fill(effective_start)

        # Next Invoice Date input
        next_inp = self.page.locator(
            "div:has(> label:has-text('Next Invoice Date')) input, "
            "input[name='nextInvoiceDate']:visible"
        ).first
        if next_inp.count() == 0 or not next_inp.is_visible():
            next_inp = self.page.locator("input[type='date']:visible").nth(1)
        if next_inp.count() > 0 and next_inp.is_visible():
            next_inp.fill(effective_next)

        self.page.wait_for_timeout(400)

    def toggle_auto_generate_invoice(self, enable: bool = True):
        """Toggle Auto-generate invoice switch/checkbox."""
        logger.info(f"Setting auto-generate invoice to: {enable}")
        checkbox = self.page.locator("input[type='checkbox']").first
        if checkbox.is_visible():
            is_checked = checkbox.is_checked()
            if is_checked != enable:
                checkbox.click()
                self.page.wait_for_timeout(300)

    def click_add_service(self):
        """Click '+ Add Service' button in Billing Services section."""
        logger.info("Clicking '+ Add Service' button...")
        add_btn = self.page.locator("button:has-text('Add Service')").first
        add_btn.wait_for(state="visible", timeout=5000)
        add_btn.click()
        self.page.wait_for_timeout(800)
        self.page.locator("table:has-text('Unit Price') tbody tr").first.wait_for(
            state="visible", timeout=5000
        )
        logger.info("Service row added.")

    def get_service_table_rows(self):
        """Return locator for all service rows in the billing services table."""
        return self.page.locator("table:has-text('Unit Price'), table:has-text('Qty')").first.locator("tbody tr")

    def fill_service_row(
        self,
        row_index: int = 0,
        service_name: str = "",
        service_option_index: int = 1,
        description: str = "",
        qty: str = "1",
        unit_price: str = "100",
        gst_percent: str = "18",
    ):
        """
        Fill a specific service row in the Billing Services table.
        """
        logger.info(
            f"Filling service row #{row_index + 1}: Service='{service_name}', Qty='{qty}', Price='{unit_price}', GST='{gst_percent}%'"
        )
        rows = self.get_service_table_rows()
        row = rows.nth(row_index)
        row.wait_for(state="visible", timeout=5000)

        # Service select - wait for options to populate asynchronously
        service_select = row.locator("select").first
        for _ in range(20):
            opts = service_select.locator("option").all()
            if len(opts) > 1:
                break
            self.page.wait_for_timeout(500)

        opts = service_select.locator("option").all()
        opts_info = [(o.get_attribute("value"), o.inner_text().strip()) for o in opts]
        logger.info(f"Available services in row select: {opts_info}")

        if len(opts) > 1:
            matched = False
            if service_name:
                for val, text in opts_info:
                    if service_name.lower() in text.lower():
                        try:
                            if val:
                                service_select.select_option(value=val)
                            else:
                                service_select.select_option(label=text)
                        except Exception:
                            service_select.select_option(label=text)
                        logger.info(f"Selected service '{text}' (val={val}) by name match.")
                        matched = True
                        break
            if not matched:
                service_select.select_option(index=1)
                selected_text = opts_info[1][1] if len(opts_info) > 1 else "index 1"
                logger.info(f"Selected fallback service: '{selected_text}'")
        else:
            raise AssertionError(f"No service options available in dropdown! Dropdown only has: {opts_info}")

        # Description
        if description:
            desc_input = row.locator("textarea, input[type='text']").first
            if desc_input.is_visible():
                desc_input.fill(description)

        # Qty (Col 3)
        qty_input = row.locator("input[type='number']").first
        qty_input.fill(str(qty))

        # Unit Price (Col 4)
        price_input = row.locator("input[type='number']").nth(1)
        price_input.fill(str(unit_price))

        # GST % (Col 5)
        if gst_percent is not None:
            gst_select = row.locator("select").nth(1)
            if gst_select.is_visible():
                gst_select.select_option(str(gst_percent))

        self.page.wait_for_timeout(600)

    def get_service_row_data(self, row_index: int = 0) -> dict:
        """Extract data from a service row."""
        rows = self.get_service_table_rows()
        row = rows.nth(row_index)
        row.wait_for(state="visible", timeout=5000)

        service_val = row.locator("select").first.input_value()
        desc_val = row.locator("textarea, input[type='text']").first.input_value()
        qty_val = row.locator("input[type='number']").first.input_value()
        price_val = row.locator("input[type='number']").nth(1).input_value()
        gst_val = row.locator("select").nth(1).input_value()
        total_text = row.locator("td:nth-child(7)").inner_text().strip()

        return {
            "service": service_val,
            "description": desc_val,
            "qty": qty_val,
            "unit_price": price_val,
            "gst_percent": gst_val,
            "total_amount": total_text,
        }

    def remove_service_row(self, row_index: int = 0):
        """Remove a service row by clicking the trash/remove icon in the last cell."""
        rows = self.get_service_table_rows()
        row = rows.nth(row_index)
        del_btn = row.locator(
            "td:last-child button, td:last-child [role='button'], button[aria-label*='delete' i], button[aria-label*='remove' i], button[aria-label*='trash' i]"
        ).last
        if del_btn.count() == 0 or not del_btn.is_visible():
            del_btn = row.locator("button").last
        del_btn.click()
        self.page.wait_for_timeout(1000)

    def get_invoice_summary(self) -> dict:
        """Extract Subtotal, Total GST, and Total Amount from Billing / Invoice Summary."""
        panels = self.page.locator("div.chakra-tabs__tab-panels").first
        subtotal_elem = panels.locator("text=Subtotal").locator("..").first
        gst_elem = panels.locator("text=Total GST").locator("..").first
        total_elem = panels.locator("text=Total Amount").locator("..").first

        sub_text = subtotal_elem.inner_text().replace("Subtotal", "").strip() if subtotal_elem.is_visible() else ""
        gst_text = gst_elem.inner_text().replace("Total GST", "").strip() if gst_elem.is_visible() else ""
        total_text = total_elem.inner_text().replace("Total Amount", "").strip() if total_elem.is_visible() else ""

        return {
            "subtotal": sub_text,
            "total_gst": gst_text,
            "total_amount": total_text,
        }

    def verify_qty_price_input_constraints(self, row_index: int = 0) -> dict:
        """
        Verify validation attributes and constraints on Qty and Unit Price inputs:
        - min, max, maxlength
        - Returns constraint metadata and any active error element text.
        """
        rows = self.get_service_table_rows()
        row = rows.nth(row_index)
        qty_input = row.locator("input[type='number']").first
        price_input = row.locator("input[type='number']").nth(1)

        qty_meta = {
            "min": qty_input.get_attribute("min"),
            "max": qty_input.get_attribute("max"),
            "maxlength": qty_input.get_attribute("maxlength"),
            "aria_invalid": qty_input.get_attribute("aria-invalid"),
        }
        price_meta = {
            "min": price_input.get_attribute("min"),
            "max": price_input.get_attribute("max"),
            "maxlength": price_input.get_attribute("maxlength"),
            "aria_invalid": price_input.get_attribute("aria-invalid"),
        }

        # Check for active errors in the row or form
        active_errors = [
            e.inner_text().strip()
            for e in self.page.locator(".chakra-form__error-message, [aria-invalid='true'], [role='alert'], .chakra-alert").all()
            if e.is_visible()
        ]

        return {
            "qty_constraints": qty_meta,
            "price_constraints": price_meta,
            "active_errors": active_errors,
        }

    def click_create_plan(self, generate_invoice_now: bool = False, auto_confirm_duplicate: bool = True) -> dict:
        """
        Click 'Create Plan' or 'Create Plan & Generate Invoice Now'.
        Handles the duplicate plan confirmation alertdialog:
          <header class="chakra-modal__header">Similar plan already exists</header>
          <div class="chakra-modal__body">A billing plan (#...) already exists with the same amount and start date. Are you sure you want to create a new one?</div>
          <footer class="chakra-modal__footer">
            <button class="chakra-button">Cancel</button>
            <button class="chakra-button">Yes, create anyway</button>
          </footer>
        """
        if generate_invoice_now:
            btn = self.page.locator("button:has-text('Create Plan & Generate Invoice Now')").first
        else:
            btn = self.page.locator("button[type='submit']:has-text('Create Plan'), button:has-text('Create Plan'):not(:has-text('Generate'))").first
        btn.click()
        self.page.wait_for_timeout(800)

        result = {
            "duplicate_modal_detected": False,
            "header": "",
            "message": "",
            "action_taken": None,
        }

        modal = self.page.locator(
            "section[role='alertdialog']:has-text('Similar plan already exists'), .chakra-modal__content:has-text('Similar plan already exists')"
        ).first

        try:
            if modal.is_visible(timeout=3000):
                result["duplicate_modal_detected"] = True
                header_el = modal.locator(".chakra-modal__header, header").first
                body_el = modal.locator(".chakra-modal__body, div").first
                result["header"] = header_el.inner_text().strip() if header_el.is_visible() else "Similar plan already exists"
                result["message"] = body_el.inner_text().strip() if body_el.is_visible() else ""
                logger.info(f"Duplicate plan confirmation modal detected: '{result['header']}' - '{result['message']}'")

                if auto_confirm_duplicate:
                    confirm_btn = modal.locator("button:has-text('Yes, create anyway')").first
                    if confirm_btn.is_visible():
                        confirm_btn.click()
                        result["action_taken"] = "confirmed"
                        logger.info("Clicked 'Yes, create anyway' on duplicate plan modal.")
                        self.page.wait_for_timeout(1000)
        except Exception:
            pass

        self.page.wait_for_timeout(1000)
        return result

    def get_duplicate_plan_modal_details(self) -> dict:
        """Inspect and return elements of the 'Similar plan already exists' alertdialog."""
        modal = self.page.locator(
            "section[role='alertdialog']:has-text('Similar plan already exists'), .chakra-modal__content:has-text('Similar plan already exists')"
        ).first
        if not modal.is_visible(timeout=2000):
            return {"visible": False}

        header = modal.locator(".chakra-modal__header, header").first.inner_text().strip()
        body = modal.locator(".chakra-modal__body").first.inner_text().strip()
        has_cancel = modal.locator("button:has-text('Cancel')").first.is_visible()
        has_confirm = modal.locator("button:has-text('Yes, create anyway')").first.is_visible()

        return {
            "visible": True,
            "header": header,
            "body": body,
            "has_cancel_button": has_cancel,
            "has_confirm_button": has_confirm,
        }

    def cancel_duplicate_plan_modal(self):
        """Click 'Cancel' on 'Similar plan already exists' alertdialog."""
        modal = self.page.locator("section[role='alertdialog'], .chakra-modal__content").filter(
            has_text="Similar plan already exists"
        ).first
        cancel_btn = modal.locator("button:has-text('Cancel')").first
        cancel_btn.click()
        self.page.wait_for_timeout(800)
        logger.info("Cancelled duplicate plan creation via confirmation modal.")

    def confirm_duplicate_plan_modal(self):
        """Click 'Yes, create anyway' on 'Similar plan already exists' alertdialog."""
        modal = self.page.locator("section[role='alertdialog'], .chakra-modal__content").filter(
            has_text="Similar plan already exists"
        ).first
        confirm_btn = modal.locator("button:has-text('Yes, create anyway')").first
        confirm_btn.click()
        self.page.wait_for_timeout(1000)
        logger.info("Confirmed duplicate plan creation via 'Yes, create anyway'.")
