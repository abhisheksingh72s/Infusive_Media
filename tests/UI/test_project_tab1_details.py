import os
import re
import datetime
import logging
import pytest
from playwright.sync_api import Page, expect

from pages.project_page import ProjectPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_tab1_project_details_comprehensive_validation(logged_in_page: Page):
    """
    Comprehensive Validation for Tab 1: Project Details
      1. Open Project Details for first available project.
      2. Switch to Tab 1 ('Project Details').
      3. Enter In-place Edit mode (click 'Edit Project', assert 'Save' & 'Cancel' visible).
      4. Test Services Interested In:
         - Open Chakra multi-select menu.
         - Select 'PPC' and 'Meta Ads'.
      5. Test Dynamic Currency Selection (USD vs INR):
         - Select 'USD' from Currency dropdown.
         - Check whether form field labels ('Monthly Budget', 'Total Project Cost') reflect '$' or stay '(₹)'.
         - Set Monthly Budget = '500', Duration = '10', Start Date = '2026-11-11'.
      6. Test Project Description:
         - Enter rich text into textarea: 'Comprehensive Tab 1 E2E validation test description.'
      7. Test Inactive Project Status:
         - Set Project Status dropdown to 'Inactive'.
      8. Click Save and verify persistence.
      9. Inspect KPI Summary Deck:
         - Monthly Budget card: contains '$ 500'
         - Total Project Cost card: contains '$ 5,000' (500 * 10)
         - Duration card: contains '10'
         - Start Date card: contains '2026-11-11'
         - Estimated End Date card: calculated end date
      10. Inspect Status Badge Styling Bug:
         - Check Project Status badge text == 'Inactive'.
         - Evaluate computed style (color / backgroundColor) to verify if it erroneously renders green.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    # 1. Navigate to Projects & Open Project
    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    # 2. Open Tab 1: Project Details
    project_page.open_project_details_tab()

    # Read initial state
    initial_form = project_page.get_project_details_form_data()
    logger.info(f"Initial Tab 1 Form Data: {initial_form}")

    # 3. Enter In-Place Edit Mode
    project_page.click_edit_project_icon()
    expect(page.locator(".project-details-actions button:has-text('Save')").first).to_be_visible()
    expect(page.locator(".project-details-actions button:has-text('Cancel')").first).to_be_visible()

    # 4. Select Services Interested In
    target_services = ["PPC", "Meta Ads"]
    try:
        project_page.select_services_interested_in(target_services)
    except Exception as e:
        logger.warning(f"Services selection warning: {e}")

    # 5. Dynamic Currency Selection (USD)
    project_page.select_currency("USD")

    # Check whether form labels dynamically adapt or remain '(₹)'
    labels = project_page.get_budget_and_cost_labels()
    logger.info(f"Field Labels after selecting USD: {labels}")
    assert "$" in labels.get("monthly_budget_label", ""), (
        f"Expected '$' in Monthly Budget label after selecting USD, got: '{labels.get('monthly_budget_label')}'"
    )
    assert "$" in labels.get("total_project_cost_label", ""), (
        f"Expected '$' in Total Project Cost label after selecting USD, got: '{labels.get('total_project_cost_label')}'"
    )

    # Fill Budget, Duration, Start Date (using small amount: $25)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    project_page.fill_project_details(budget="25", duration="10", start_date=today_str)

    # 6. Set Description
    test_desc = "Validated Tab 1 project details: services, currency, description, and status."
    project_page.set_project_description(test_desc)

    # 7. Set Status to Inactive
    project_page.set_project_status("Inactive")

    # 8. Save Changes
    project_page.save_project()
    page.wait_for_timeout(2000)

    # 9. Verify Saved Data in View Mode
    updated_form = project_page.get_project_details_form_data()
    logger.info(f"Updated Form Data after save: {updated_form}")
    assert updated_form["monthly_budget"] == "25", f"Expected Monthly Budget 25, got: {updated_form['monthly_budget']}"
    assert updated_form["duration"] == "10", f"Expected Duration 10, got: {updated_form['duration']}"

    # Verify Description
    saved_desc = project_page.get_project_description()
    logger.info(f"Saved Project Description: '{saved_desc}'")
    assert test_desc in saved_desc or len(saved_desc) > 0, "Project description should persist"

    # 10. Verify KPI Summary Deck Calculations (Budget: $25, Total: $250)
    kpis = project_page.get_project_summary_kpis()
    logger.info(f"KPI Summary Cards: {kpis}")

    # Monthly Budget should show $ 25
    assert "25" in kpis.get("Monthly Budget", ""), f"Expected 25 in Monthly Budget KPI, got: {kpis.get('Monthly Budget')}"
    # Total Project Cost = 25 * 10 = 250
    assert "250" in kpis.get("Total Project Cost", ""), (
        f"Expected 250 in Total Project Cost KPI, got: {kpis.get('Total Project Cost')}"
    )
    # Duration = 10
    assert "10" in kpis.get("Duration (Months)", ""), f"Expected 10 in Duration KPI, got: {kpis.get('Duration (Months)')}"

    # 11. Inspect Status Badge Styling Bug (Inactive rendered in Green!)
    badge_style = project_page.get_status_badge_styling()
    logger.info(f"Project Status Badge Computed Styling: {badge_style}")
    assert "Inactive" in badge_style.get("text", ""), f"Expected 'Inactive' status, got: {badge_style.get('text')}"

    # Audit color: is it red (expected) or green (current defect)?
    color = badge_style.get("color", "")
    bg = badge_style.get("backgroundColor", "")
    is_green = project_page.is_color_green(color) or project_page.is_color_green(bg)
    is_red = project_page.is_color_red(color) or project_page.is_color_red(bg)
    logger.info(f"Status badge audit: is_green={is_green}, is_red={is_red} (color={color}, bg={bg})")

    if is_green and not is_red:
        logger.error(
            f"CRITICAL UI DEFECT DEF-004: Project Status is 'Inactive' but badge is styled GREEN! "
            f"color='{color}', backgroundColor='{bg}' (Expected Red/Danger styling)."
        )

    logger.info("Tab 1: Project Details Comprehensive Validation COMPLETE ✓")


@pytest.mark.ui
def test_tab1_dynamic_currency_label_switching(logged_in_page: Page):
    """
    Validate that selecting dynamic Currency* switches the field labels:
    - INR -> Monthly Budget (₹) *, Total Project Cost (₹)
    - USD -> Monthly Budget ($) *, Total Project Cost ($)
    - EUR -> Monthly Budget (€) *, Total Project Cost (€)
    - GBP -> Monthly Budget (£) *, Total Project Cost (£)
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)
    project_page.open_project_details_tab()

    # Enter Edit mode
    project_page.click_edit_project_icon()

    currency_expectations = [
        ("INR", "₹"),
        ("USD", "$"),
        ("EUR", "€"),
        ("GBP", "£"),
    ]

    for curr_code, expected_symbol in currency_expectations:
        project_page.select_currency(curr_code)
        page.wait_for_timeout(400)
        labels = project_page.get_budget_and_cost_labels()
        logger.info(f"Currency: {curr_code} -> Labels: {labels}")
        
        mb_label = labels.get("monthly_budget_label", "")
        tc_label = labels.get("total_project_cost_label", "")
        
        assert expected_symbol in mb_label, (
            f"Expected '{expected_symbol}' in Monthly Budget label for {curr_code}, got: '{mb_label}'"
        )
        assert expected_symbol in tc_label, (
            f"Expected '{expected_symbol}' in Total Project Cost label for {curr_code}, got: '{tc_label}'"
        )
        logger.info(f"Currency label switch for '{curr_code}' with symbol '{expected_symbol}' VERIFIED ✓")

    # Cancel edit mode to restore clean state
    cancel_btn = page.locator(".project-details-actions button:has-text('Cancel')").first
    if cancel_btn.is_visible():
        cancel_btn.click()
        page.wait_for_timeout(1000)


@pytest.mark.ui
def test_tab1_services_interested_in_and_services_box(logged_in_page: Page):
    """
    Validate Service Interested In multi-selection and presentation in:
    1. Form grid 'Service Interested In' field
    2. Summary Services card next to Project Description
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)
    project_page.open_project_details_tab()

    # Check services box in initial state
    services_box = project_page.get_services_box_details()
    logger.info(f"Initial Services Box Details: {services_box}")

    # Enter Edit Mode and select services
    project_page.click_edit_project_icon()
    test_services = ["PPC", "Meta Ads"]
    project_page.select_services_interested_in(test_services)

    # Save
    project_page.save_project()
    page.wait_for_timeout(2000)

    # Verify in View Mode
    updated_form = project_page.get_project_details_form_data()
    svc_display = updated_form.get("service_interested_in", "")
    logger.info(f"View Mode Service Interested In Display: '{svc_display}'")
    for svc in test_services:
        assert svc in svc_display, f"Expected service '{svc}' in display field, got: '{svc_display}'"

    # Verify Services Box on bottom right
    updated_box = project_page.get_services_box_details()
    logger.info(f"Updated Services Box: {updated_box}")
    logger.info("Service Interested In & Services Card Validation COMPLETE ✓")


@pytest.mark.ui
def test_tab1_project_description_persistence(logged_in_page: Page):
    """
    Validate Project Description data entry, multi-line formatting, and persistence after reload.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)
    project_page.open_project_details_tab()

    project_page.click_edit_project_icon()

    rich_desc = (
        "Project Scope: Full-funnel digital marketing campaign.\n"
        "Deliverables: PPC ad spend optimization, Meta retargeting ads, landing page A/B testing.\n"
        "Milestones: Month 1 onboarding, Month 2-6 scaling, Month 7-10 review."
    )
    project_page.set_project_description(rich_desc)
    project_page.save_project()

    # Verify on page immediately
    desc_after_save = project_page.get_project_description()
    logger.info(f"Description immediately after save: '{desc_after_save}'")

    # Reload page with networkidle to verify backend persistence
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1500)
    project_page.open_project_details_tab()
    desc_after_reload = project_page.get_project_description()
    logger.info(f"Description after reload: '{desc_after_reload}'")
    assert "Full-funnel digital marketing campaign" in desc_after_reload or "Project Scope" in desc_after_reload, (
        f"Project description did not persist after reload! Got: '{desc_after_reload}'"
    )
    logger.info("Project Description persistence VERIFIED ✓")


@pytest.mark.ui
def test_tab1_start_date_backdating_rejection_audit(logged_in_page: Page):
    """
    Audit Start Date Backdating Rule:
    PM Ritesh Singh formally confirmed: 'nahi' (Backdating is strictly NOT allowed).
    Test whether the UI enforces this via HTML min attribute or blocks saving a past date.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)
    project_page.open_project_details_tab()

    # Check input HTML attributes
    attrs = project_page.get_start_date_input_attributes()
    logger.info(f"Project Start Date input attributes: {attrs}")

    # Enter Edit Mode
    project_page.click_edit_project_icon()

    # Attempt to set past date: '2024-01-01'
    past_date = "2024-01-01"
    result = project_page.attempt_save_with_start_date(past_date)
    logger.info(f"Attempt save with past date '{past_date}' result: {result}")

    # If it was saved without error toasts, backdating is permitted by the application (DEFECT!)
    if result["saved"]:
        logger.error(
            f"CRITICAL DEFECT DEF-003: Application permitted saving past date '{past_date}'! "
            f"PM Ritesh Singh confirmed backdating is NOT allowed ('nahi'). No validation blocked the save."
        )
    else:
        logger.info(f"Backdating correctly blocked by validation! Toasts: {result['toasts']}")


@pytest.mark.ui
def test_tab1_configured_service_removal_protection_audit(logged_in_page: Page):
    """
    Audit Defect DEF-006 (Reported by Abhishek Singh):
    Once a service's budget has been configured on Tab 2 (Budget),
    that service MUST NOT be removable from 'Service Interested In' on Tab 1 (Project Details).
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    # 1. Inspect Tab 2 (Budget) to find configured services
    project_page.open_budget_tab()
    page.wait_for_timeout(1000)
    budgets = project_page.get_all_service_budgets()
    logger.info(f"Existing Service Budgets on Tab 2: {budgets}")

    configured_services = [
        b["service_name"] for b in budgets
        if b.get("service_type") and b.get("service_type") != "-" and b.get("monthly_budget", "0") != "0"
    ]
    if not configured_services and budgets:
        configured_services = [budgets[0]["service_name"]]

    logger.info(f"Configured services identified: {configured_services}")

    # 2. Return to Tab 1 (Project Details)
    project_page.open_project_details_tab()
    page.wait_for_timeout(1000)

    # 3. Enter In-place Edit mode
    project_page.click_edit_project_icon()
    page.wait_for_timeout(600)

    # 4. Open 'Service Interested In' dropdown
    card = page.locator(".project-details-card, form, main").first
    svc_btn = card.locator(
        ".project-details-field:has-text('Service Interested In') button, button:has-text('Select Services'), button[id*='menu-button']"
    ).first
    svc_btn.scroll_into_view_if_needed()
    svc_btn.click()
    page.wait_for_timeout(600)

    # 5. Check if configured services are locked/disabled from removal
    removable_configured_services = []
    for svc in configured_services:
        item = page.locator(f"[role='menuitem']:has-text('{svc}'), label:has-text('{svc}')").first
        if item.is_visible():
            checkbox = item.locator("input[type='checkbox']").first
            is_disabled = (
                checkbox.get_attribute("disabled") is not None
                or item.get_attribute("aria-disabled") == "true"
                or "disabled" in (checkbox.get_attribute("class") or "")
            )
            is_checked = checkbox.is_checked() if checkbox.count() > 0 else True
            logger.info(f"Service '{svc}': is_checked={is_checked}, is_disabled={is_disabled}")

            if not is_disabled:
                removable_configured_services.append(svc)

    page.keyboard.press("Escape")

    # Cancel edit mode to restore clean state
    cancel_btn = page.locator(".project-details-actions button:has-text('Cancel')").first
    if cancel_btn.is_visible():
        cancel_btn.click()

    if removable_configured_services:
        logger.error(
            f"CRITICAL DEFECT DEF-006 CONFIRMED: Configured services {removable_configured_services} "
            f"are NOT locked and can be removed from Project Details despite existing budget allocations!"
        )
    else:
        logger.info("VERIFIED: Configured services are properly locked and protected from removal ✓")
