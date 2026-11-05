import logging
import os
import time

logger = logging.getLogger(__name__)


class TaskPage:
    """
    Page Object Model for Projects -> Project Details -> Task Management -> Create Task.
    Handles navigating to project details, clicking Task Management tab, filling Create Task modal,
    and submitting to trigger the 'Task Created' notification event.
    """

    def __init__(self, page):
        self.page = page
        base = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")
        self.base_url = base.replace("/login", "").rstrip("/")
        self.projects_url = f"{self.base_url}/projects"

    def go_to_projects(self):
        """Navigate to the Projects listing page."""
        logger.info("Navigating to %s...", self.projects_url)
        self.page.goto(self.projects_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)
        self.page.locator("tbody tr").first.wait_for(state="visible", timeout=30000)

    def click_project_name(self, project_name=None):
        """Click on the Project Name in the table to open Project Details."""
        self.page.locator("tbody tr").first.wait_for(state="visible", timeout=30000)
        if project_name:
            logger.info("Clicking project with name '%s'...", project_name)
            target = self.page.locator(f"tbody tr:has-text('{project_name}') td:nth-child(2)").first
            target.click()
        else:
            xunit = self.page.locator("tbody tr:has-text('xUnit') td:nth-child(2)").first
            if xunit.count() > 0 and xunit.is_visible():
                logger.info("Clicking xUnit Test Project (with active allocated resources)...")
                xunit.click()
            else:
                logger.info("Clicking the first Project Name in the table...")
                first_project_cell = self.page.locator("tbody tr td:nth-child(2)").first
                first_project_cell.click()

        self.page.wait_for_timeout(2000)
        self.page.wait_for_url("**/project-details**", timeout=30000)
        logger.info("Navigated to Project Details: %s", self.page.url)

    def ensure_resource_allocation(self):
        """
        Phase 1: Resource Allocation
        Verifies if resources are allocated to the project.
        If not:
          1. Completes mandatory Project Details if needed (Budget, Duration, Start Date).
          2. Opens 'Resource Allocation' tab and allocates an employee to the project.
        """
        logger.info("Phase 1: Checking Resource Allocation for project...")
        res_tab = self.page.locator(
            "button.project-tab[role='tab']:has-text('Resource Allocation'), button[role='tab'][data-index='2']"
        ).first
        if not res_tab.is_visible():
            logger.info("Resource Allocation tab not visible or not needed.")
            return

        res_tab.click()
        self.page.wait_for_timeout(2000)

        # Check if project details are incomplete warning is displayed
        incomplete_warning = self.page.locator("text='Project Details Incomplete'").first
        if incomplete_warning.count() > 0 and incomplete_warning.is_visible():
            logger.info("Project Details incomplete. Filling mandatory fields in Project Details tab...")
            details_tab = self.page.locator(
                "button.project-tab[role='tab']:has-text('Project Details'), button[role='tab'][data-index='0']"
            ).first
            details_tab.click()
            self.page.wait_for_timeout(1500)

            # Click Edit Project
            edit_btn = self.page.locator("button.project-details-edit-button, button:has-text('Edit Project')").first
            if edit_btn.count() > 0 and edit_btn.is_visible():
                edit_btn.click()
                self.page.wait_for_timeout(1000)

            # Fill Monthly Budget
            budget_inp = self.page.locator("label:has-text('Monthly Budget') + input, input[name='monthlyBudget'], input[type='number']").first
            if budget_inp.count() > 0 and budget_inp.is_visible() and (budget_inp.input_value() == "0" or not budget_inp.input_value()):
                budget_inp.fill("50000")

            # Fill Duration
            dur_inp = self.page.locator("label:has-text('Duration') + input, input[name='duration']").first
            if dur_inp.count() > 0 and dur_inp.is_visible() and (dur_inp.input_value() == "0" or not dur_inp.input_value()):
                dur_inp.fill("6")

            # Fill Start Date
            start_date_inp = self.page.locator("label:has-text('Project Start Date') + input, input[type='date']").first
            if start_date_inp.count() > 0 and start_date_inp.is_visible() and not start_date_inp.input_value():
                start_date_inp.fill("2026-11-01")

            # Save Project Details
            save_proj_btn = self.page.locator("button:has-text('Save'), button:has-text('Update')").first
            if save_proj_btn.count() > 0 and save_proj_btn.is_visible():
                save_proj_btn.click()
                self.page.wait_for_timeout(2000)

            # Return to Resource Allocation tab
            res_tab.click()
            self.page.wait_for_timeout(2000)

        # Check if resources need to be allocated
        alloc_table_zero = self.page.locator("text='No Resource Allocations Found', text='Showing 0 of 0'").first
        if alloc_table_zero.count() > 0 and alloc_table_zero.is_visible():
            logger.info("Allocating employee to project in Resource Allocation tab...")
            # Fill Employee
            emp_inp = self.page.locator("input[placeholder='Search Employee']").first
            if emp_inp.count() > 0 and emp_inp.is_visible():
                emp_inp.click()
                self.page.wait_for_timeout(500)
                emp_opt = self.page.locator("[class*='option'], [role='option'], div.css-1nmdiq5-menu").locator("visible=true").first
                if emp_opt.count() > 0 and emp_opt.is_visible():
                    emp_opt.click()
                else:
                    self.page.keyboard.press("ArrowDown")
                    self.page.keyboard.press("Enter")
                self.page.wait_for_timeout(400)

            # Fill Service
            svc_inp = self.page.locator("input[placeholder='Search Service']").first
            if svc_inp.count() > 0 and svc_inp.is_visible():
                svc_inp.click()
                self.page.wait_for_timeout(500)
                svc_opt = self.page.locator("[class*='option'], [role='option'], div.css-1nmdiq5-menu").locator("visible=true").first
                if svc_opt.count() > 0 and svc_opt.is_visible():
                    svc_opt.click()
                else:
                    self.page.keyboard.press("ArrowDown")
                    self.page.keyboard.press("Enter")
                self.page.wait_for_timeout(400)

            # Fill Task / Work Category
            tsk_inp = self.page.locator("input[placeholder='Search Work Category']").first
            if tsk_inp.count() > 0 and tsk_inp.is_visible():
                tsk_inp.click()
                self.page.wait_for_timeout(500)
                tsk_opt = self.page.locator("[class*='option'], [role='option'], div.css-1nmdiq5-menu").locator("visible=true").first
                if tsk_opt.count() > 0 and tsk_opt.is_visible():
                    tsk_opt.click()
                else:
                    self.page.keyboard.press("ArrowDown")
                    self.page.keyboard.press("Enter")
                self.page.wait_for_timeout(400)

            # Fill Start Date
            sd_alloc = self.page.locator("input[name='startDate']").first
            if sd_alloc.count() > 0 and sd_alloc.is_visible() and not sd_alloc.input_value():
                sd_alloc.fill("2026-11-01")

            # Click Save Allocation
            save_alloc_btn = self.page.locator("button[type='submit']:has-text('Save Allocation'), button:has-text('Save Allocation')").first
            if save_alloc_btn.count() > 0 and save_alloc_btn.is_enabled():
                save_alloc_btn.click()
                self.page.wait_for_timeout(2000)
                logger.info("Resource allocation saved successfully.")

    def open_task_management_tab(self):
        """Click on the 'Task Management' tab in Project Details."""
        logger.info("Phase 2: Clicking 'Task Management' tab...")
        tab = self.page.locator(
            "button.project-tab[role='tab']:has-text('Task Management'), button[role='tab']:has-text('Task Management'), button[role='tab'][data-index='3']"
        ).first
        tab.wait_for(state="visible", timeout=10000)
        tab.click()
        self.page.wait_for_timeout(2000)
        logger.info("Task Management tab is active.")

    def click_add_task(self):
        """Click the 'Add Task' button in Task Management."""
        logger.info("Clicking 'Add Task' button...")
        add_btn = self.page.locator("button").filter(has_text="Add Task").locator("visible=true").first
        add_btn.wait_for(state="visible", timeout=10000)
        add_btn.click()
        self.page.wait_for_timeout(2000)
        logger.info("Add Task modal opened.")

    def select_field_option(self, modal, placeholder: str):
        """Select an option from a custom dropdown input by placeholder."""
        inp = modal.locator(f"input[placeholder='{placeholder}']").first
        if inp.count() > 0 and inp.is_visible():
            logger.info("Selecting option for '%s'...", placeholder)
            try:
                inp.click(timeout=3000)
            except Exception:
                inp.click(force=True)
            self.page.wait_for_timeout(400)
            option = self.page.locator("[class*='option'], [role='option'], div.css-1nmdiq5-menu, li.css-wnxomm").locator("visible=true").first
            if option.count() > 0 and option.is_visible():
                option.click()
            else:
                self.page.keyboard.press("ArrowDown")
                self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(400)

    def fill_and_submit_task(self, task_title: str, task_desc: str = "Automated test task for notification event"):
        """
        Fills the Create Task modal and submits it:
        - Task Name*
        - Dropdowns (Service, Milestone, Task Type, Assign To, Reviewer)
        - Date
        - Description
        - Clicks 'Save Task'
        """
        logger.info("Filling Create Task modal with title: '%s'...", task_title)
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        modal.wait_for(state="visible", timeout=10000)

        # 1. Task Name*
        title_input = modal.locator("input[name='title'], input[placeholder='Enter task name'], input.chakra-input").first
        title_input.fill(task_title)
        logger.info("Filled Task Name: '%s'", task_title)

        # 2. Dropdown selections
        dropdowns = [
            ("Select Service", "Design"),
            ("Select Milestone", None),
            ("Select Task Type", None),
            ("Select Employee", None),
            ("Select Reviewer", None),
        ]
        for ph, preferred_text in dropdowns:
            try:
                inp = modal.locator(f"input[placeholder='{ph}']").first
                if inp.count() > 0 and inp.is_visible():
                    logger.info("Selecting dropdown '%s'...", ph)
                    inp.scroll_into_view_if_needed()
                    inp.click()
                    self.page.wait_for_timeout(600)
                    menu_lis = inp.locator("xpath=following-sibling::div//li | xpath=..//li")
                    try:
                        menu_lis.first.wait_for(state="visible", timeout=2500)
                        all_opts = menu_lis.all()
                    except Exception:
                        all_opts = self.page.locator("li.css-wnxomm, li[role='option'], [role='option']").locator("visible=true").all()
                    
                    if all_opts:
                        chosen_opt = all_opts[0]
                        if preferred_text:
                            for o in all_opts:
                                if preferred_text.lower() in o.inner_text().lower():
                                    chosen_opt = o
                                    break
                        elif ph == "Select Reviewer" and len(all_opts) > 1:
                            chosen_opt = all_opts[1]
                        logger.info("Selected option '%s' for '%s'", chosen_opt.inner_text().strip(), ph)
                        chosen_opt.click()
                    else:
                        inp.press("ArrowDown")
                        self.page.keyboard.press("Enter")
                    self.page.wait_for_timeout(500)
            except Exception as e:
                logger.warning("Error selecting '%s': %s", ph, str(e))

        # 3. Date input (dynamically pick unassigned future date to avoid resource date collision)
        import datetime
        date_inp = modal.locator("input[type='date'], input[name='startDate']").first
        if date_inp.count() > 0 and date_inp.is_visible():
            day_offset = 10 + (int(time.time()) % 30)
            target_date_obj = datetime.date.today() + datetime.timedelta(days=day_offset)
            target_date = target_date_obj.strftime("%Y-%m-%d")
            if target_date in ["2026-11-05", "2026-12-30"]:
                target_date = (target_date_obj + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
            date_inp.fill(target_date)
            logger.info("Filled dynamic unconflicted task date: '%s'", target_date)

        # 4. Description
        desc_input = modal.locator("textarea[placeholder='Add task description'], textarea").first
        if desc_input.count() > 0 and desc_input.is_visible():
            desc_input.fill(task_desc)

        # 5. Click Save Task button
        logger.info("Clicking 'Save Task' button...")
        save_btn = modal.locator("button").filter(has_text="Save Task").locator("visible=true").first
        save_btn.click()
        self.page.wait_for_timeout(3000)
        logger.info("Save Task button clicked.")
        return True

    def capture_toast(self, timeout=5000):
        """Capture toast/status alert message."""
        selectors = ["div[role='status']", "div[role='alert']", ".toast", "[class*='toast']"]
        for s in selectors:
            loc = self.page.locator(s)
            if loc.first.is_visible(timeout=timeout):
                txt = loc.first.inner_text().strip()
                if txt:
                    return txt
        return ""
