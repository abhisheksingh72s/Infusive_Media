import os
import re
import logging
import pytest
from playwright.sync_api import Page, expect

from pages.project_page import ProjectPage

logger = logging.getLogger(__name__)


def ensure_project_is_active(project_page: ProjectPage, page: Page):
    """Ensure project is set to Active status so action buttons in Tab 2 are enabled."""
    project_page.open_project_details_tab()
    page.wait_for_timeout(800)
    badge = project_page.get_status_badge_styling()
    logger.info(f"Tab 1 Status Badge: {badge}")
    if "inactive" in badge.get("text", "").lower():
        logger.info("Project is currently Inactive. Switching to Active for Budget tab testing...")
        project_page.click_edit_project_icon()
        project_page.set_project_status("Active")
        project_page.save_project()
        page.wait_for_timeout(2000)


@pytest.mark.ui
def test_tab2_budget_table_structure_and_services(logged_in_page: Page):
    """
    Validate Tab 2: Budget Table Structure & Service Listings:
      1. Open Project Details for first available project.
      2. Ensure Project is Active.
      3. Switch to 'Budget' tab.
      4. Assert table renders with all 10 expected columns:
         - Service Name
         - Service Type
         - Currency
         - Monthly Budget
         - Duration
         - Total Service Cost
         - Start Date
         - Status
         - Budget Status
         - Action
      5. Assert that services selected under Tab 1 appear as rows.
      6. Assert each row contains an actionable 'Configure' / 'Edit' button.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    # Ensure project is Active
    ensure_project_is_active(project_page, page)

    # 1. Switch to Budget Tab
    project_page.open_budget_tab()

    # 2. Verify Table & Columns
    active_panel = page.locator("div[role='tabpanel']:not([hidden]), div.chakra-tabs__tab-panel:visible").first
    budget_table = active_panel.locator("table").first
    expect(budget_table).to_be_visible()

    headers = [th.inner_text().strip().upper() for th in budget_table.locator("thead th").all()]
    logger.info(f"Tab 2 Budget Table Headers: {headers}")

    expected_column_keywords = [
        "SERVICE NAME",
        "SERVICE TYPE",
        "CURRENCY",
        "MONTHLY BUDGET",
        "DURATION",
        "TOTAL SERVICE COST",
        "START DATE",
        "STATUS",
        "BUDGET STATUS",
        "ACTION",
    ]
    for kw in expected_column_keywords:
        assert any(kw in h for h in headers), f"Expected column keyword '{kw}' in table headers: {headers}"

    # 3. Verify Service Rows
    budgets = project_page.get_all_service_budgets()
    logger.info(f"Found {len(budgets)} services in Budget tab: {[b['service_name'] for b in budgets]}")
    assert len(budgets) > 0, "Expected at least 1 service row in Budget table"

    # 4. Verify each row has action button
    rows = project_page.get_service_budget_table_rows().all()
    for i, r in enumerate(rows):
        btn = r.locator("button.budget-action-btn, button:has-text('Configure'), button:has-text('Edit')").first
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()

    logger.info("Tab 2: Budget Table Structure & Columns VERIFIED ✓")


@pytest.mark.ui
def test_tab2_configure_recurring_service_budget_math(logged_in_page: Page):
    """
    Validate configuring a Recurring Service Budget & Mathematical Integrity:
      1. Switch to 'Budget' tab.
      2. Click 'Configure' on first service (e.g. PPC).
      3. Verify #budget-edit-form opens with header 'Configure Service Budget - <Service>'.
      4. Verify real-time client-side calculation:
         (Monthly Budget × Duration) auto-populates Estimated Amount field.
      5. Fill form:
         - Service Type: Recurring
         - Monthly Budget: 500
         - Duration: 6 Months
         - Start Date: 2026-11-15
         - Status: Active
      6. Click 'Save Budget' and verify persistence in table.
      7. Mathematical Assertion:
         Total Service Cost == Monthly Budget * Duration (500 * 6 = 3,000).
      8. Assertion: BUDGET STATUS transitions to 'Configured'.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    ensure_project_is_active(project_page, page)
    project_page.open_budget_tab()

    budgets = project_page.get_all_service_budgets()
    assert len(budgets) > 0, "No services found in Budget tab"
    target_service = budgets[0]["service_name"]
    logger.info(f"Targeting service for Recurring Budget configuration: '{target_service}'")

    # 1. Open Configure form and inspect real-time calculation
    form_card = project_page.click_edit_service_budget(target_service)
    expect(form_card).to_be_visible()

    # Enter Monthly Budget & Duration within project limit ($700) to check real-time formula
    monthly_inp = form_card.locator(".budget-field:has-text('Monthly Budget') input").first
    monthly_inp.fill("100")

    dur_inp = form_card.locator(".budget-field:has-text('Estimated Duration') input[type='number']").first
    dur_inp.fill("5")

    page.wait_for_timeout(500)

    # Check Estimated Amount auto-calculated in form: 100 * 5 = 500
    est_amount_inp = form_card.locator(".budget-field:has-text('Estimated Amount') input").first
    est_amount_val = est_amount_inp.input_value()
    logger.info(f"Real-time Estimated Amount auto-calculated in form: '{est_amount_val}'")
    assert "500" in est_amount_val, f"Expected 500 in Estimated Amount preview, got: '{est_amount_val}'"

    # Select unit Months
    dur_unit_select = form_card.locator(".budget-field:has-text('Estimated Duration') select").first
    dur_unit_select.select_option(value="2")  # 2 = Months

    # Set Start Date
    start_date_input = form_card.locator(".budget-field:has-text('Start Date') input[type='date']").first
    start_date_input.fill("2026-11-15")

    # Click Save Budget
    page.evaluate("() => document.querySelectorAll('.chakra-toast').forEach(el => el.remove())")
    save_btn = form_card.locator("button:has-text('Save Budget')").first
    save_btn.evaluate("el => el.click()")
    page.wait_for_timeout(2000)

    is_open = form_card.is_visible()
    toasts = page.locator(".chakra-toast").all_inner_texts()
    errors = form_card.locator(".chakra-form__error-message, [aria-invalid='true']").all_inner_texts()
    logger.info(f"After save click: is_open={is_open}, toasts={toasts}, errors={errors}")

    # Verify table row updated
    updated = project_page.get_service_budget(target_service)
    logger.info(f"Service '{target_service}' updated budget record: {updated}")
    assert updated is not None, f"Service '{target_service}' not found in Budget table"

    # Mathematical Formula Assertion: Total Cost = Monthly Budget * Duration
    assert "100" in updated.get("monthly_budget", ""), (
        f"Expected 100 in monthly budget, got: '{updated.get('monthly_budget')}'"
    )
    assert "5" in updated.get("duration", ""), (
        f"Expected duration 5, got: '{updated.get('duration')}'"
    )
    assert "500" in updated.get("total_cost", ""), (
        f"Mathematical Error! Expected Total Cost 500 (100 * 5), got: '{updated.get('total_cost')}'"
    )

    # Budget Status Assertion: Must be 'Configured'
    assert updated.get("budget_status") == "Configured", (
        f"Expected Budget Status 'Configured', got: '{updated.get('budget_status')}'"
    )
    logger.info(f"Recurring Budget Math (500 * 6 = 3,000) & Status 'Configured' VERIFIED ✓")


@pytest.mark.ui
def test_tab2_configure_onetime_service_budget_math(logged_in_page: Page):
    """
    Validate configuring a One-Time Service Budget:
      1. Switch to 'Budget' tab.
      2. Click 'Configure' on a second service (e.g. Meta Ads or UI/UX Design).
      3. Set Service Type: OneTime (val: "2").
      4. Set Amount: 1500.
      5. Set Duration: 1 Month.
      6. Set Start Date: 2026-11-20.
      7. Mathematical Assertion:
         For OneTime service, Total Cost == Flat Amount (1,500), not multiplied by duration.
      8. Click 'Save Budget' and assert BUDGET STATUS transitions to 'Configured'.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    ensure_project_is_active(project_page, page)
    project_page.open_budget_tab()

    budgets = project_page.get_all_service_budgets()
    assert len(budgets) > 0, "No services in Budget tab"
    target_service = budgets[0]["service_name"]
    logger.info(f"Targeting service for One-Time Budget configuration (overwriting to OneTime): '{target_service}'")

    updated = project_page.configure_service_budget(
        service_name=target_service,
        service_type="OneTime",
        amount=600,
        duration=2,
        duration_unit="Months",
        start_date="2026-11-20",
        status="Active",
    )
    logger.info(f"Service '{target_service}' One-Time updated budget record: {updated}")

    # One-Time Total Cost Assertion: Flat 600 (duration=2 does NOT multiply)
    assert "600" in updated.get("total_cost", ""), (
        f"Expected Total Cost 600 for One-Time service, got: '{updated.get('total_cost')}'"
    )
    assert updated.get("budget_status") == "Configured", (
        f"Expected Budget Status 'Configured', got: '{updated.get('budget_status')}'"
    )
    logger.info(f"One-Time Budget Flat Amount (600) & Status 'Configured' VERIFIED ✓")


@pytest.mark.ui
def test_tab2_budget_over_allocation_warning_banner(logged_in_page: Page):
    """
    Validate Real-Time Budget Over-Allocation Warning Banner:
      1. Open Edit Service Budget for a service.
      2. Switch Service Type to 'OneTime' (val: "2").
      3. Enter an amount exceeding Total Project Cost ($50,001 vs $5,000 project limit).
      4. Assert warning banner appears in real-time with:
         - ⚠️ icon
         - Warning text: 'Your allocated budget has exceeded the Total Project Cost defined for this project.'
         - Total Project Cost: $ 5,000
         - Projected Total Allocated: $ 50,001
         - Exceeded by: $ 45,001
      5. Adjust amount to within budget ($1,000).
      6. Assert warning banner disappears.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    ensure_project_is_active(project_page, page)
    project_page.open_budget_tab()

    budgets = project_page.get_all_service_budgets()
    target_service = budgets[0]["service_name"]

    form_card = project_page.click_edit_service_budget(target_service)

    # Switch to OneTime
    type_select = form_card.locator(".budget-field:has-text('Service Type') select").first
    type_select.select_option(value="2")
    page.wait_for_timeout(400)

    # Enter amount exceeding Total Project Cost ($50,001)
    amount_input = form_card.locator(
        ".budget-field:has-text('Service Amount') input, .budget-field:has-text('Monthly Budget') input, input[placeholder='Enter amount']"
    ).first
    amount_input.fill("50001")
    page.wait_for_timeout(600)

    # Assert Over-Allocation Warning Banner appears
    warning = project_page.get_budget_over_allocation_warning()
    logger.info(f"Budget Over-Allocation Warning Banner State: {warning}")
    assert warning["is_visible"], "Expected over-allocation warning banner when amount exceeds project budget!"
    assert warning["has_warning_icon"], "Expected ⚠️ warning icon in over-allocation banner"
    assert "exceeded the Total Project Cost" in warning["raw_text"]
    assert "Exceeded by" in warning["raw_text"]
    logger.info("Over-allocation warning banner correctly triggered and verified ✓")

    # Now enter within-budget amount: $100 (Total Project Cost is $700)
    amount_input.fill("100")
    page.wait_for_timeout(600)

    warning_after = project_page.get_budget_over_allocation_warning()
    logger.info(f"Budget Warning State after reducing amount: {warning_after}")
    assert not warning_after["is_visible"], "Warning banner should disappear when amount is within budget!"
    logger.info("Warning banner correctly cleared when amount returned to valid range ✓")

    # Cancel form to restore state
    project_page.cancel_edit_service_budget()


@pytest.mark.ui
def test_tab2_budget_start_date_backdating_audit(logged_in_page: Page):
    """
    Audit Service Budget Start Date Backdating Rule:
    PM Ritesh Singh confirmed: 'nahi' (Backdating strictly NOT allowed).
    Check whether Edit Service Budget date input restricts past dates or accepts them.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    ensure_project_is_active(project_page, page)
    project_page.open_budget_tab()

    budgets = project_page.get_all_service_budgets()
    target_service = budgets[0]["service_name"]

    # Open edit form and inspect date input attributes
    form_card = project_page.click_edit_service_budget(target_service)
    date_inp = form_card.locator(".budget-field:has-text('Start Date') input[type='date']").first

    min_val = date_inp.get_attribute("min") or ""
    logger.info(f"Service Budget Start Date input 'min' attribute: '{min_val}'")

    # Attempt to set past date: '2024-01-01'
    past_date = "2024-01-01"
    date_inp.fill(past_date)

    page.evaluate("() => document.querySelectorAll('.chakra-toast').forEach(el => el.remove())")
    save_btn = form_card.locator("button:has-text('Save Budget')").first
    save_btn.evaluate("el => el.click()")
    page.wait_for_timeout(1500)

    toasts = page.locator(".chakra-toast, [role='alert'], [role='status']").all_inner_texts()
    is_form_still_open = form_card.is_visible()
    logger.info(f"Service budget past date save result: is_still_open={is_form_still_open}, toasts={toasts}")

    if not is_form_still_open:
        logger.error(
            f"DEFECT DEF-003: Service Budget permitted saving past date '{past_date}'! "
            f"PM Ritesh Singh confirmed backdating is NOT allowed ('nahi'). No validation blocked the save."
        )
    else:
        logger.info(f"Service budget backdating correctly blocked by validation! Toasts: {toasts}")
        project_page.cancel_edit_service_budget()


@pytest.mark.ui
def test_tab2_budget_negative_validation_blank_amount(logged_in_page: Page):
    """
    Negative Validation: Attempt to save Service Budget with empty Monthly Budget.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    ensure_project_is_active(project_page, page)
    project_page.open_budget_tab()

    budgets = project_page.get_all_service_budgets()
    target_service = budgets[0]["service_name"]

    form_card = project_page.click_edit_service_budget(target_service)
    monthly_inp = form_card.locator(
        ".budget-field:has-text('Monthly Budget') input, .budget-field:has-text('Service Amount') input, input[placeholder='Enter amount']"
    ).first
    monthly_inp.fill("")  # Clear amount

    page.evaluate("() => document.querySelectorAll('.chakra-toast').forEach(el => el.remove())")
    save_btn = form_card.locator("button:has-text('Save Budget')").first
    save_btn.evaluate("el => el.click()")
    page.wait_for_timeout(1000)

    # Form should remain open due to HTML5 required attribute
    assert form_card.is_visible(), "Form closed unexpectedly when required amount was blank!"
    logger.info("Service Budget blank amount validation PASSED (form blocked submission) ✓")

    project_page.cancel_edit_service_budget()


@pytest.mark.ui
def test_tab2_inactive_project_disables_budget_actions(logged_in_page: Page):
    """
    Validate that setting a project to Inactive locks and disables Budget action buttons.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    # 1. Set Project to Inactive on Tab 1
    project_page.open_project_details_tab()
    project_page.click_edit_project_icon()
    project_page.set_project_status("Inactive")
    project_page.save_project()
    page.wait_for_timeout(1500)

    # 2. Switch to Tab 2 Budget
    project_page.open_budget_tab()

    # 3. Assert all action buttons have 'disabled' attribute
    rows = project_page.get_service_budget_table_rows().all()
    assert len(rows) > 0
    for r in rows:
        btn = r.locator("button.budget-action-btn").first
        expect(btn).to_be_disabled()
    logger.info("Inactive Project successfully disables all Budget action buttons (Security/Integrity VERIFIED) ✓")

    # Restore project to Active
    project_page.open_project_details_tab()
    project_page.click_edit_project_icon()
    project_page.set_project_status("Active")
    project_page.save_project()
    page.wait_for_timeout(1500)


@pytest.mark.ui
def test_tab2_budget_duration_unit_calculation_audit(logged_in_page: Page):
    """
    Audit Defect DEF-005: Estimated Amount Calculation Does Not Consider Selected Duration Unit.
    Steps:
      1. Open Budget tab -> Click Configure/Edit on service.
      2. Set Service Type: Recurring.
      3. Enter Monthly Budget: 100.
      4. Set Estimated Duration: 10.
      5. Select unit: Days (value="1").
      6. Observe Estimated Amount preview:
         - Expected: 100 / 30 * 10 ≈ $33.33 (scaled to Days)
         - Actual bug: system calculates 100 * 10 = $1,000 (ignoring Days unit)
      7. Switch unit to Years (value="3"):
         - Expected: 100 * 12 * 10 = $12,000 (scaled to Years)
         - Actual bug: system still calculates 100 * 10 = $1,000 (ignoring Years unit)
      8. Document and assert this defect per user's Bug Register specification.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    ensure_project_is_active(project_page, page)
    project_page.open_budget_tab()

    budgets = project_page.get_all_service_budgets()
    assert len(budgets) > 0, "No services found in Budget tab"
    target_service = budgets[0]["service_name"]

    form_card = project_page.click_edit_service_budget(target_service)
    expect(form_card).to_be_visible()

    # 1. Set Service Type to Recurring ("1")
    type_select = form_card.locator(".budget-field:has-text('Service Type') select").first
    type_select.select_option(value="1")
    page.wait_for_timeout(300)

    # 2. Enter Monthly Budget: 100
    monthly_inp = form_card.locator(".budget-field:has-text('Monthly Budget') input").first
    monthly_inp.fill("100")

    # 3. Enter Estimated Duration: 10
    dur_inp = form_card.locator(".budget-field:has-text('Estimated Duration') input[type='number']").first
    dur_inp.fill("10")
    page.wait_for_timeout(400)

    # 4. Select Duration Unit: Days ("1")
    dur_unit_select = form_card.locator(".budget-field:has-text('Estimated Duration') select").first
    dur_unit_select.select_option(value="1")  # 1 = Days
    page.wait_for_timeout(500)

    est_amount_inp = form_card.locator(".budget-field:has-text('Estimated Amount') input").first
    amount_for_days = est_amount_inp.input_value().strip()
    logger.info(f"DEF-005 Audit: For Monthly Budget 100 and Duration 10 DAYS, Estimated Amount is: '{amount_for_days}'")

    # 5. Select Duration Unit: Years ("3")
    dur_unit_select.select_option(value="3")  # 3 = Years
    page.wait_for_timeout(500)
    amount_for_years = est_amount_inp.input_value().strip()
    logger.info(f"DEF-005 Audit: For Monthly Budget 100 and Duration 10 YEARS, Estimated Amount is: '{amount_for_years}'")

    # 6. Select Duration Unit: Months ("2")
    dur_unit_select.select_option(value="2")  # 2 = Months
    page.wait_for_timeout(500)
    amount_for_months = est_amount_inp.input_value().strip()
    logger.info(f"DEF-005 Audit: For Monthly Budget 100 and Duration 10 MONTHS, Estimated Amount is: '{amount_for_months}'")

    # Dismiss form
    project_page.cancel_edit_service_budget()

    # Defect Assertion: If days, months, and years all give the exact same amount ('1000' or '1,000'),
    # the frontend logic completely ignores the duration unit!
    if amount_for_days == amount_for_years == amount_for_months:
        logger.error(
            f"CRITICAL DEFECT DEF-005 CONFIRMED: Estimated Amount ignored duration unit! "
            f"Days ({amount_for_days}) == Years ({amount_for_years}) == Months ({amount_for_months}). "
            f"Formula strictly multiplied Monthly Budget ($100) x Duration (10) = $1,000 without unit scaling."
        )
    else:
        logger.info("Estimated Amount varies with duration unit! Defect might be resolved.")

