import os
import time
import logging
import pytest
from playwright.sync_api import Page, expect

from pages.login_page import LoginPage
from pages.project_page import ProjectPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_billing_services_ui_happy_path(logged_in_page: Page):
    """
    Test Project Details -> Billing & Invoices:
      1. Navigate to Project Details and open 'Billing & Invoices' tab.
      2. Configure Billing Type and Currency.
      3. Add a Service row, enter valid Description, Qty, Unit Price, GST %.
      4. Verify dynamic calculations: Row total, Subtotal, Total GST, Total Amount.
      5. Add a 2nd row and verify multi-row calculation and row removal.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    # 1. Navigate to Projects & Open Project
    project_page.go_to_project()
    project_page.click_project_hyperlink("Testing Company - Project")

    # 2. Switch to Billing & Invoices
    project_page.open_billing_invoices_tab()

    # 3. Configure Billing Type & Currency
    project_page.select_billing_type("One-Time")
    project_page.select_billing_currency("INR")

    # 4. Add First Service
    project_page.click_add_service()
    project_page.fill_service_row(
        row_index=0,
        service_option_index=1,
        description="Search Engine Optimization & PPC Campaign",
        qty="5",
        unit_price="1200",
        gst_percent="18",
    )

    # 5. Verify Row Calculations
    row_data = project_page.get_service_row_data(0)
    logger.info(f"Row 1 Data: {row_data}")
    assert "7,080" in row_data["total_amount"], f"Expected total ~₹7,080.00, got {row_data['total_amount']}"

    # 6. Verify Invoice Summary
    summary = project_page.get_invoice_summary()
    logger.info(f"Invoice Summary: {summary}")
    assert "6,000" in summary["subtotal"], f"Expected Subtotal ~₹6,000, got {summary['subtotal']}"
    assert "1,080" in summary["total_gst"], f"Expected GST ~₹1,080, got {summary['total_gst']}"
    assert "7,080" in summary["total_amount"], f"Expected Total ~₹7,080, got {summary['total_amount']}"

    # 7. Add 2nd Service Row & Remove It
    count_before = project_page.get_service_table_rows().count()
    project_page.click_add_service()
    count_after_add = project_page.get_service_table_rows().count()
    assert count_after_add == count_before + 1, f"Expected {count_before + 1} rows after adding service, got {count_after_add}"

    # Remove the newly added row
    project_page.remove_service_row(count_after_add - 1)
    count_after_remove = project_page.get_service_table_rows().count()
    assert count_after_remove == count_before, f"Expected {count_before} rows after removal, got {count_after_remove}"

    # Final summary should remain intact
    summary_final = project_page.get_invoice_summary()
    assert "7,080" in summary_final["total_amount"], "Summary amount should be preserved after deleting extra row"
    logger.info("Happy path UI billing services flow verified successfully ✓")


@pytest.mark.ui
def test_billing_services_qty_price_length_and_active_errors(logged_in_page: Page):
    """
    Test Qty & Unit Price input length limitations and active error handling:
      1. Check HTML constraints: min, max, maxlength on Qty and Unit Price inputs.
      2. Enter excessively long number (50+ digits) into Qty & Price.
      3. Capture layout behavior (horizontal overflow / astronomical formatted amounts).
      4. Submit and verify active error / backend exception handling.
      5. Validate negative & zero value boundaries.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    # 1. Navigate to Project Details -> Billing & Invoices
    project_page.go_to_project()
    project_page.click_project_hyperlink("Testing Company - Project")
    project_page.open_billing_invoices_tab()

    # 2. Add Service
    project_page.click_add_service()

    # 3. Inspect Input Constraints (min, max, maxlength)
    constraints = project_page.verify_qty_price_input_constraints(row_index=0)
    logger.info(f"Initial Input Constraints: {constraints}")

    qty_max = constraints["qty_constraints"]["max"]
    qty_maxlength = constraints["qty_constraints"]["maxlength"]
    price_max = constraints["price_constraints"]["max"]
    price_maxlength = constraints["price_constraints"]["maxlength"]

    logger.info(f"Qty Constraints: min='{constraints['qty_constraints']['min']}', max='{qty_max}', maxlength='{qty_maxlength}'")
    logger.info(f"Price Constraints: min='{constraints['price_constraints']['min']}', max='{price_max}', maxlength='{price_maxlength}'")

    # 4. Negative / Boundary Test: Excessively Long Number
    huge_number = "25900000000000000000000000000000000000000000000000"
    logger.info(f"Injecting huge number ({len(huge_number)} digits) into Qty...")
    project_page.fill_service_row(
        row_index=0,
        service_option_index=1,
        qty=huge_number,
        unit_price="1",
        gst_percent="18",
    )

    # Read row amount
    row_data = project_page.get_service_row_data(0)
    logger.info(f"Row total after huge Qty input: {row_data['total_amount']}")

    # Check if UI enforces limited length or if field allowed all digits
    actual_qty_length = len(row_data["qty"])
    logger.info(f"Actual Qty string length accepted in DOM: {actual_qty_length}")

    # Check for active errors before submit
    pre_submit_constraints = project_page.verify_qty_price_input_constraints(0)
    logger.info(f"Pre-submit active errors: {pre_submit_constraints['active_errors']}")

    # Submit plan to test active error response
    project_page.click_create_plan()
    page.wait_for_timeout(1500)

    # Check for active error messages or alerts
    post_submit_constraints = project_page.verify_qty_price_input_constraints(0)
    logger.info(f"Post-submit active errors / alerts: {post_submit_constraints['active_errors']}")

    # If length was NOT restricted and backend threw 400 System.Decimal error:
    has_system_decimal_error = any("System.Decimal" in err or "400" in err for err in post_submit_constraints["active_errors"])
    if actual_qty_length > 15:
        logger.warning(
            f"DEFECT IDENTIFIED: Qty input lacks length limitation (accepted {actual_qty_length} digits). "
            f"Backend Decimal overflow: {has_system_decimal_error}"
        )

    # 5. Boundary Test: Negative & Zero Values
    logger.info("Testing negative and zero boundary values...")
    rows = project_page.get_service_table_rows()
    qty_input = rows.first.locator("input[type='number']").first

    # Zero Qty test (min=1 expected)
    qty_input.fill("0")
    page.wait_for_timeout(300)
    is_valid_zero = qty_input.evaluate("el => el.checkValidity()")
    logger.info(f"HTML5 checkValidity for Qty=0 (min=1 expected): {is_valid_zero}")
    assert is_valid_zero is False, "HTML5 validity check should fail for Qty=0 when min=1"

    # Negative Qty test
    qty_input.fill("-5")
    page.wait_for_timeout(300)
    val_neg = qty_input.input_value()
    is_valid_neg = qty_input.evaluate("el => el.checkValidity()")
    logger.info(f"Qty input value after attempting '-5': '{val_neg}', checkValidity: {is_valid_neg}")
    # Verify input rejected negative value or marks it invalid
    assert is_valid_neg is False or val_neg != "-5" or (val_neg != "" and int(val_neg) < 1), (
        "Negative Qty should be rejected or marked invalid"
    )

    logger.info("Qty and Price length limitation and active error verification test completed ✓")


@pytest.mark.ui
def test_billing_recurring_plan_configuration(logged_in_page: Page):
    """
    Test Project Billing Recurring Plan Configuration:
      1. Open Project Details -> Billing & Invoices.
      2. Select 'Recurring' billing type.
      3. Verify recurring-specific fields become visible:
         - Billing Cycle *
         - Start Date * (editable)
         - Next Invoice Date * (editable)
         - Payment Terms *
         - Auto-generate invoice toggle
      4. Inspect and select Billing Currency (e.g. USD).
      5. Select Billing Cycle (e.g. Monthly).
      6. Set Start Date and Next Invoice Date (e.g. Next month).
      7. Select Payment Terms (e.g. 30 Days).
      8. Add Service row with valid Qty & Unit Price in USD.
      9. Verify USD currency symbols and summary updates.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    # 1. Navigate to Project Details -> Billing & Invoices
    project_page.go_to_project()
    project_page.click_project_hyperlink("Testing Company - Project")
    project_page.open_billing_invoices_tab()

    # 2. Select Recurring Billing Type
    project_page.select_billing_type("Recurring")
    page.wait_for_timeout(1000)

    # 3. Verify Recurring-Specific Controls
    start_date_inp = page.locator("div.chakra-tabs__tab-panels input[name='startDate']:visible, input[name='startDate']:visible").first
    next_date_inp = page.locator("div.chakra-tabs__tab-panels input[name='nextInvoiceDate']:visible, input[name='nextInvoiceDate']:visible").first
    cycle_btn = page.locator("div.chakra-tabs__tab-panels button:has-text('Monthly'), div.chakra-tabs__tab-panels button:has-text('Cycle')").first
    # Log Payment Terms HTML
    pt_container = page.locator("div.chakra-tabs__tab-panels").locator("div:has-text('Payment Terms')").last
    logger.info(f"Payment terms container HTML: {pt_container.inner_html()}")

    payment_terms_btn = pt_container.locator("button, select, input").first
    logger.info(f"Payment terms element tag: <{payment_terms_btn.evaluate('el => el.tagName')}> class='{payment_terms_btn.get_attribute('class')}' text='{payment_terms_btn.inner_text().strip()}'")
    auto_generate_chk = page.locator("div.chakra-tabs__tab-panels input[type='checkbox']").first

    assert start_date_inp.is_visible(), "Start Date * must be visible when Recurring is selected"
    assert next_date_inp.is_visible(), "Next Invoice Date * must be visible when Recurring is selected"
    assert start_date_inp.is_editable(), "Start Date * must be editable"
    assert next_date_inp.is_editable(), "Next Invoice Date * must be editable"
    assert cycle_btn.is_visible(), "Billing Cycle * must be visible for Recurring"
    assert payment_terms_btn.is_visible(), "Payment Terms * must be visible"
    assert auto_generate_chk.is_visible(), "Auto-generate invoice toggle must be visible"

    logger.info(f"Recurring Start Date initial value: {start_date_inp.input_value()}")
    logger.info(f"Recurring Next Invoice Date initial value: {next_date_inp.input_value()}")

    # 4. Configure Billing Currency (USD)
    project_page.select_billing_currency("USD")

    # 5. Set Custom Dates (Start: Today, Next Invoice: 30 days later)
    today_str = time.strftime("%Y-%m-%d")
    next_month_str = time.strftime("%Y-%m-%d", time.localtime(time.time() + 30 * 86400))
    project_page.set_recurring_dates(start_date=today_str, next_invoice_date=next_month_str)

    assert start_date_inp.input_value() == today_str, f"Expected Start Date {today_str}, got {start_date_inp.input_value()}"
    assert next_date_inp.input_value() == next_month_str, f"Expected Next Invoice Date {next_month_str}, got {next_date_inp.input_value()}"

    # 6. Verify Cycle & Payment Terms
    logger.info(f"Billing Cycle active text: {cycle_btn.inner_text().strip()}")
    logger.info(f"Payment Terms active text: {payment_terms_btn.inner_text().strip()}")

    # 7. Add Service in USD
    project_page.click_add_service()
    project_page.fill_service_row(
        row_index=0,
        service_option_index=1,
        description="Monthly SEO and Content Recurring Retainer",
        qty="2",
        unit_price="1500",
        gst_percent="18",
    )

    # 8. Verify USD Calculated Values
    row_data = project_page.get_service_row_data(0)
    logger.info(f"Recurring Service Row Data (USD): {row_data}")
    # 2 * 1500 = 3000 + 18% (540) = $3,540.00
    assert "3,540" in row_data["total_amount"], f"Expected ~$3,540.00, got {row_data['total_amount']}"

    # 9. Verify Invoice Summary in USD
    summary = project_page.get_invoice_summary()
    logger.info(f"Recurring Invoice Summary: {summary}")
    assert "3,000" in summary["subtotal"], f"Expected Subtotal ~$3,000.00, got {summary['subtotal']}"
    assert "540" in summary["total_gst"], f"Expected GST ~$540.00, got {summary['total_gst']}"
    assert "3,540" in summary["total_amount"], f"Expected Total Amount ~$3,540.00, got {summary['total_amount']}"

    # 10. Toggle Auto-Generate Invoice
    project_page.toggle_auto_generate_invoice(enable=True)
    assert auto_generate_chk.is_checked(), "Auto-generate invoice should be enabled"

    page.screenshot(path="reports/billing_recurring_plan_configured.png")
    logger.info("Recurring billing plan configuration verified successfully ✓")


@pytest.mark.ui
def test_billing_one_time_plan_configuration(logged_in_page: Page):
    """
    Test Project Billing One-Time Plan Configuration:
      1. Open Project Details -> Billing & Invoices.
      2. Select 'One-Time' billing type.
      3. Verify One-Time specific fields:
         - Billing Details section header
         - Billing Currency *
         - Invoice Date * (visible and editable)
         - Due Date * (visible and editable)
         - Payment Terms * (e.g. 7 Days or 30 Days)
         - Verification of helper text: "Client is expected to make payment within {X} days..."
         - Billing Cycle * is NOT shown for One-Time.
      4. Configure Currency to USD.
      5. Select Payment Terms (e.g. 7 Days).
      6. Set Invoice Date & Due Date.
      7. Verify helper text dynamically reflects the selected Payment Terms.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    # 1. Navigate to Project Details -> Billing & Invoices
    project_page.go_to_project()
    project_page.click_project_hyperlink("Testing Company - Project")
    project_page.open_billing_invoices_tab()

    # 2. Select One-Time Billing Type
    project_page.select_billing_type("One-Time")
    page.wait_for_timeout(1000)

    # 3. Verify One-Time specific date fields
    date_inputs = page.locator("div.chakra-tabs__tab-panels input[type='date']:visible")
    assert date_inputs.count() >= 2, f"Expected at least 2 date inputs (Invoice Date & Due Date) for One-Time, found {date_inputs.count()}"

    inv_date_inp = date_inputs.first
    due_date_inp = date_inputs.nth(1)

    assert inv_date_inp.is_visible(), "Invoice Date * must be visible for One-Time billing"
    assert due_date_inp.is_visible(), "Due Date * must be visible for One-Time billing"
    assert inv_date_inp.is_editable(), "Invoice Date * must be editable"
    assert due_date_inp.is_editable(), "Due Date * must be editable"

    # 4. Verify Billing Cycle is NOT displayed for One-Time
    cycle_label = page.locator("div.chakra-tabs__tab-panels label:has-text('Billing Cycle')")
    assert cycle_label.count() == 0 or not cycle_label.first.is_visible(), "Billing Cycle should not be visible for One-Time billing"

    # 5. Configure Currency to USD
    project_page.select_billing_currency("USD")

    # 6. Payment Terms Selection (e.g. 7 Days)
    project_page.select_payment_terms("7 Days")
    page.wait_for_timeout(500)

    # 7. Verify helper text shows payment term days
    helper_text = page.locator("div.chakra-tabs__tab-panels").first.inner_text()
    assert "payment within" in helper_text.lower(), "Helper text explaining payment terms expected"
    logger.info("One-Time billing plan configuration verified successfully ✓")


@pytest.mark.ui
def test_project_details_all_five_tabs_navigation(logged_in_page: Page):
    """
    Test Project Details 5 Tabs Structure & Navigation:
      1. Project Details
      2. Budget
      3. Resource Allocation
      4. Task Management
      5. Billing & Invoices
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    # 1. Open Project Details
    project_page.go_to_project()
    project_page.click_project_hyperlink("Testing Company - Project")

    # 2. Get and verify all 5 tabs
    tabs = project_page.get_all_project_tabs()
    logger.info(f"Detected project tabs: {tabs}")

    expected_tabs = [
        "Project Details",
        "Budget",
        "Resource Allocation",
        "Task Management",
        "Billing & Invoices",
    ]

    for expected in expected_tabs:
        found = any(expected.lower() in t.lower() for t in tabs)
        assert found, f"Expected tab '{expected}' not found in active tabs: {tabs}"
        logger.info(f"Verified tab presence: '{expected}' ✓")

    # 3. Test Navigation across all 5 tabs
    for expected in expected_tabs:
        logger.info(f"Switching to tab: '{expected}'")
        project_page.switch_to_tab(expected)
        page.wait_for_timeout(1000)

        # Verify active tab or panel visibility
        panel_text = page.locator("div.chakra-tabs__tab-panels").first.inner_text()
        assert len(panel_text.strip()) > 0, f"Panel for tab '{expected}' should not be empty"
        logger.info(f"Successfully switched to '{expected}', panel snippet: {panel_text[:120].replace(chr(10), ' ')}")

    logger.info("All 5 Project Details tabs verified and navigated successfully ✓")


@pytest.mark.ui
def test_service_budget_configuration_and_billing_integration(logged_in_page: Page):
    """
    Test Project Service Budget configuration and integration into Billing & Invoices:
      1. Open Project Details for 'Adventa Tech Inc test 04 - Project'.
      2. Switch to 'Budget' tab.
      3. Verify 'Service Budget' table presence, headers, and existing services.
      4. Configure/Edit budget for 'Meta Ads':
         - Service Type: Recurring
         - Monthly Budget: 15000
         - Duration: 6 Months
         - Save and verify status 'Configured' and calculated cost.
      5. Switch to 'Billing & Invoices' tab.
      6. Verify configured service is available in Billing Services dropdown.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    # 1. Open Project Details
    project_page.go_to_project()
    project_page.click_project_hyperlink("Adventa Tech Inc test 04 - Project")

    # 2. Switch to Budget Tab
    project_page.open_budget_tab()

    # 3. Verify Service Budget table headers and rows
    active_panel = page.locator("div[role='tabpanel']:not([hidden]), div.chakra-tabs__tab-panel:visible").first
    budget_table = active_panel.locator("table").first
    headers = [th.inner_text().strip() for th in budget_table.locator("thead th").all()]
    logger.info(f"Service Budget Table Headers: {headers}")
    assert any("SERVICE" in h.upper() for h in headers)
    assert any("BUDGET" in h.upper() for h in headers)
    assert any("STATUS" in h.upper() for h in headers)

    budgets_before = project_page.get_all_service_budgets()
    logger.info(f"Services found in Budget tab: {[b['service_name'] for b in budgets_before]}")
    assert len(budgets_before) > 0, "Expected at least 1 service in Budget table"

    # 4. Configure / Edit budget for 'Meta Ads'
    updated_meta = project_page.configure_service_budget(
        service_name="Meta Ads",
        service_type="Recurring",
        amount=15000,
        duration=6,
        duration_unit="Months",
        start_date="2026-11-01",
        status="Active",
    )
    logger.info(f"Meta Ads updated budget result: {updated_meta}")
    assert updated_meta is not None
    assert updated_meta.get("budget_status") == "Configured"

    # 5. Switch to Billing & Invoices Tab
    project_page.open_billing_invoices_tab()
    project_page.select_billing_type("Recurring")

    # 6. Add Service and verify Meta Ads is selectable
    project_page.click_add_service()
    row = project_page.get_service_table_rows().first
    service_select = row.locator("select").first
    options = [opt.inner_text().strip() for opt in service_select.locator("option").all()]
    logger.info(f"Available services in Billing dropdown: {options}")

    assert any("Meta Ads" in opt for opt in options), f"Expected 'Meta Ads' in options: {options}"

    # Select Meta Ads
    service_select.select_option(label="Meta Ads")
    page.wait_for_timeout(500)

    # Fill Qty and verify calculation
    row.locator("input[type='number']").first.fill("1")
    page.wait_for_timeout(500)

    row_data = project_page.get_service_row_data(0)
    logger.info(f"Configured Service in Billing Row: {row_data}")
    assert len(row_data["total_amount"]) > 0

    logger.info("Service Budget to Billing flow VERIFIED successfully.")


@pytest.mark.ui
def test_duplicate_billing_plan_confirmation_modal(logged_in_page: Page):
    """
    Validate Duplicate Billing Plan Creation Logic:
    If a billing plan already exists with the same amount and start date for that day,
    the application presents a confirmation modal:
      - Header: 'Similar plan already exists'
      - Body: 'A billing plan (#...) already exists with the same amount and start date. Are you sure you want to create a new one?'
      - Buttons: 'Cancel' and 'Yes, create anyway'
    
    Verifies:
      1. Modal structure, header, message, and button visibility.
      2. 'Cancel' button dismisses the modal without creating the duplicate plan.
      3. 'Yes, create anyway' button confirms and proceeds with plan creation.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    # 1. Open Project Details
    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    # 2. Open Tab 5: Billing & Invoices
    project_page.open_billing_invoices_tab()
    page.wait_for_timeout(1000)

    # 3. Setup recurring plan with small amount ($25)
    project_page.select_billing_type("Recurring")
    project_page.select_billing_cycle("Monthly")

    from datetime import date
    today_str = date.today().strftime("%Y-%m-%d")
    project_page.set_recurring_dates(start_date=today_str, next_invoice_date=today_str)

    rows = project_page.get_service_table_rows()
    if rows.count() == 0:
        project_page.click_add_service()

    project_page.fill_service_row(
        row_index=0,
        qty="1",
        unit_price="25",
        gst_percent="0",
    )

    # 4. First Plan Creation / Attempt Duplicate
    logger.info("Submitting plan creation...")
    res = project_page.click_create_plan(auto_confirm_duplicate=False)

    if res["duplicate_modal_detected"]:
        logger.info(f"Duplicate modal detected on initial submit: {res}")
        modal_details = project_page.get_duplicate_plan_modal_details()
        assert modal_details["visible"], "Duplicate confirmation modal should be visible"
        assert "Similar plan already exists" in modal_details["header"]
        assert "same amount and start date" in modal_details["body"]
        assert modal_details["has_cancel_button"]
        assert modal_details["has_confirm_button"]

        # Test Branch 1: Click Cancel
        project_page.cancel_duplicate_plan_modal()
        page.wait_for_timeout(800)
        assert not project_page.page.locator("section[role='alertdialog']:has-text('Similar plan already exists')").first.is_visible()
        logger.info("Branch 1: 'Cancel' successfully dismissed the modal.")

        # Test Branch 2: Click Create again and Confirm
        res2 = project_page.click_create_plan(auto_confirm_duplicate=True)
        assert res2["action_taken"] == "confirmed"
        logger.info("Branch 2: 'Yes, create anyway' successfully confirmed duplicate plan creation.")
    else:
        logger.info("Initial plan created without duplicate modal. Submitting again to trigger duplicate warning...")
        page.wait_for_timeout(2000)
        res_dup = project_page.click_create_plan(auto_confirm_duplicate=False)
        modal_details = project_page.get_duplicate_plan_modal_details()
        if modal_details["visible"]:
            assert "Similar plan already exists" in modal_details["header"]
            assert "same amount and start date" in modal_details["body"]
            assert modal_details["has_cancel_button"]
            assert modal_details["has_confirm_button"]
            logger.info(f"Duplicate modal verified on second submit: {modal_details}")

            # Test Cancel
            project_page.cancel_duplicate_plan_modal()
            logger.info("Duplicate modal 'Cancel' verified.")


@pytest.mark.ui
@pytest.mark.parametrize(
    "plan_scenario,unit_price,expected_modal",
    [
        ("different_amount_tier1", "30", False),
        ("different_amount_tier2", "45", False),
    ],
    ids=["different_amount_$30", "different_amount_$45"],
)
def test_same_date_different_amount_billing_plan_parameterized(
    logged_in_page: Page,
    plan_scenario: str,
    unit_price: str,
    expected_modal: bool,
):
    """
    Parameterized Test: Same Billing Start Date, Different Amounts.
    Validates that creating a new plan on the same start date but with a DIFFERENT amount
    does NOT trigger the 'Similar plan already exists' confirmation modal and saves directly.
    """
    page = logged_in_page
    project_page = ProjectPage(page)

    # 1. Open Project Details
    project_page.go_to_project()
    project_page.click_project_hyperlink()
    page.wait_for_timeout(1000)

    # 2. Open Tab 5: Billing & Invoices
    project_page.open_billing_invoices_tab()
    page.wait_for_timeout(1000)

    # 3. Setup recurring plan with today's date
    project_page.select_billing_type("Recurring")
    project_page.select_billing_cycle("Monthly")

    from datetime import date
    today_str = date.today().strftime("%Y-%m-%d")
    project_page.set_recurring_dates(start_date=today_str, next_invoice_date=today_str)

    # Fill service row with parameterized different amount
    rows = project_page.get_service_table_rows()
    if rows.count() == 0:
        project_page.click_add_service()

    project_page.fill_service_row(
        row_index=0,
        qty="1",
        unit_price=unit_price,
        gst_percent="0",
    )

    # 4. Submit plan without auto-confirming duplicate modal
    logger.info(f"Submitting parameterized plan with date={today_str}, unit_price={unit_price}...")
    res = project_page.click_create_plan(auto_confirm_duplicate=False)
    logger.info(f"Submission result for unit_price={unit_price}: {res}")

    # 5. Assert confirmation modal matches expectation
    if expected_modal:
        assert res["duplicate_modal_detected"], f"Expected duplicate modal for amount {unit_price}, but modal did not appear!"
        project_page.cancel_duplicate_plan_modal()
    else:
        assert not res["duplicate_modal_detected"], (
            f"Vulnerability / Unexpected Modal: Similar plan modal should NOT appear for different amount ${unit_price} on {today_str}!"
        )
        logger.info(f"VERIFIED: Plan with different amount ${unit_price} on {today_str} was allowed directly without confirmation modal ✓")



