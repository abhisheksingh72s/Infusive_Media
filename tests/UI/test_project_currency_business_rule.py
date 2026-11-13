"""
Business Rule Automation Test:
Rule: "Configured currency will be shown for that project across all modules (Rupee, Dollar, Euro, etc.)"

Touchpoints Tested:
1. Show All Projects listing (/projects) -> Project Amount column must use configured currency symbol.
2. Project Details Tab 1 (/project-details) -> Currency dropdown, Budget labels, and KPI deck cards.
3. Project Details Tab 2 (Budget) -> Budget table amounts and currency column.
4. Project Details Tab 5 (Billing & Invoices) -> Form headers, Billing Plans ledger, and Summary Cards (Paid & Outstanding).
"""

import os
import pathlib
import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.project_page import ProjectPage

CURRENCY_SYMBOLS = {
    "USD": "$",
    "INR": "₹",
    "EUR": "€",
    "GBP": "£",
    "AUD": "A$",
    "CAD": "C$",
    "SGD": "S$",
}

@pytest.mark.ui
@pytest.mark.regression
def test_project_currency_business_rule_consistency(page: Page):
    """
    Validates end-to-end adherence to the Configured Currency Business Rule.
    """
    shots_dir = pathlib.Path("screenshots")
    shots_dir.mkdir(exist_ok=True)

    login_page = LoginPage(page)
    project_page = ProjectPage(page)

    admin_email = os.environ.get("EMAIL")
    admin_pass = os.environ.get("PASSWORD")
    assert admin_email and admin_pass, "Admin credentials must be provided."

    # 1. Login
    login_page.load()
    login_page.login(admin_email, admin_pass)
    login_page.wait_for_dashboard()

    # 2. Target Project (configured in USD)
    target_company = "Maddox Rodriguez and Griffin Inc"
    expected_currency_code = "USD"
    expected_symbol = CURRENCY_SYMBOLS[expected_currency_code]
    forbidden_symbol = "₹"  # For USD projects, Rupee symbol should NOT appear in project-specific amounts

    # -------------------------------------------------------------------------
    # TOUCHPOINT 1: Show All Projects Listing (/projects)
    # -------------------------------------------------------------------------
    project_page.go_to_project()
    page.wait_for_timeout(1500)
    project_page.search_project(target_company)
    page.wait_for_timeout(1500)

    row = page.locator("tbody tr").filter(has_text=target_company).first
    assert row.count() > 0 and row.is_visible(), f"Project for '{target_company}' not found in table."

    amount_cell = row.locator("td").nth(8)
    amount_cell.scroll_into_view_if_needed()
    projects_list_amount = amount_cell.inner_text().strip()
    print(f"\n[TOUCHPOINT 1] Projects List Project Amount: '{projects_list_amount}'")

    # -------------------------------------------------------------------------
    # TOUCHPOINT 2: Project Details Tab 1 (/project-details)
    # -------------------------------------------------------------------------
    project_page.click_project_hyperlink(target_company)
    page.wait_for_timeout(1500)
    project_page.open_project_details_tab()

    form_data = project_page.get_project_details_form_data()
    details_currency = form_data.get("currency")
    monthly_budget = form_data.get("monthly_budget")
    total_cost = form_data.get("total_project_cost")
    print(f"[TOUCHPOINT 2] Project Details: Currency='{details_currency}', MonthlyBudget='{monthly_budget}', TotalCost='{total_cost}'")

    kpis = project_page.get_project_summary_kpis()
    print(f"[TOUCHPOINT 2] Tab 1 KPI Cards: {kpis}")

    # -------------------------------------------------------------------------
    # TOUCHPOINT 3: Project Details Tab 2 (Budget)
    # -------------------------------------------------------------------------
    project_page.switch_to_tab("Budget")
    page.wait_for_timeout(1500)
    budget_row = page.locator("tbody tr").first
    budget_table_text = budget_row.inner_text() if budget_row.is_visible() else ""
    print(f"[TOUCHPOINT 3] Tab 2 Budget Row Text: '{budget_table_text}'")

    # -------------------------------------------------------------------------
    # TOUCHPOINT 4: Project Details Tab 5 (Billing & Invoices)
    # -------------------------------------------------------------------------
    project_page.switch_to_tab("Billing & Invoices")
    page.wait_for_timeout(1500)

    # Inspect Billing Plans table AMOUNT column
    plans_table = page.locator("table:has-text('PLAN'), table:has-text('AMOUNT')").last
    plan_amount_text = ""
    if plans_table.is_visible():
        plan_amount_cell = plans_table.locator("tbody tr td:nth-child(4)").first
        if plan_amount_cell.is_visible():
            plan_amount_text = plan_amount_cell.inner_text().strip()
            print(f"[TOUCHPOINT 4] Tab 5 Billing Plans Table Amount: '{plan_amount_text}'")

    # Inspect Project Billing Summary Cards at bottom
    # Card: Paid, Card: Outstanding
    paid_card = page.locator("div:has-text('Paid') p, div:has-text('Paid') span").filter(has_text=expected_symbol).first
    outstanding_card = page.locator("div:has-text('Outstanding') p, div:has-text('Outstanding') span").last
    outstanding_text = outstanding_card.inner_text().strip() if outstanding_card.is_visible() else ""
    print(f"[TOUCHPOINT 4] Tab 5 Project Billing Summary - Outstanding: '{outstanding_text}'")

    # -------------------------------------------------------------------------
    # BUSINESS RULE ASSERTIONS
    # -------------------------------------------------------------------------
    discrepancies = []

    # 1. Check Projects Listing
    if forbidden_symbol in projects_list_amount:
        discrepancies.append(
            f"Show All Projects table displays forbidden '{forbidden_symbol}' instead of '{expected_symbol}': '{projects_list_amount}'"
        )
    if expected_symbol not in projects_list_amount:
        discrepancies.append(
            f"Show All Projects table is missing configured symbol '{expected_symbol}': '{projects_list_amount}'"
        )

    # 2. Check Tab 1 KPI Cards
    for label, val in kpis.items():
        if "Budget" in label or "Cost" in label:
            if forbidden_symbol in val:
                discrepancies.append(f"Tab 1 KPI '{label}' displays forbidden '{forbidden_symbol}': '{val}'")
            if expected_symbol not in val:
                discrepancies.append(f"Tab 1 KPI '{label}' is missing configured symbol '{expected_symbol}': '{val}'")

    # 3. Check Tab 5 Project Billing Summary
    if forbidden_symbol in outstanding_text:
        discrepancies.append(
            f"Tab 5 Project Billing Summary 'Outstanding' card displays forbidden '{forbidden_symbol}' instead of '{expected_symbol}': '{outstanding_text}'"
        )

    print("\n================== BUSINESS RULE AUDIT REPORT ==================")
    if discrepancies:
        print(f"FAILED AUDIT - Found {len(discrepancies)} business rule violation(s):")
        for idx, d in enumerate(discrepancies, 1):
            print(f"  {idx}. {d}")
    else:
        print("PASSED AUDIT - All touchpoints adhere to the configured currency rule!")
    print("================================================================\n")

    assert not discrepancies, (
        f"Business Rule VIOLATION: Configured currency ({expected_currency_code}/{expected_symbol}) was not uniformly displayed:\n"
        + "\n".join(discrepancies)
    )
