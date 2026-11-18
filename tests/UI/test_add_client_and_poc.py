"""
Test: Add Client (Company) and Add Multi-Currency POCs
======================================================
Tests the Client and POC creation flow on https://infusive-front.jobvritta.com/company:
  1. Navigate to Companies module.
  2. Create/Verify Client Company ('Apex Global Solutions LLC', United States).
  3. Expand the company row using the user-icon:
     <img class="chakra-image css-1bkxj8e" src="/static/media/user-icon...svg">
  4. Verify the expanded sub-table opens showing existing POCs and 'Add New POC' button.
  5. Click 'Add New POC' to open the dedicated #poc-form.
  6. Fill POC 0 (AGS_POC_USD) with unique email and phone.
  7. Click 'Add More POC' to append block 1 dynamically on the same form.
  8. Fill POC 1 (AGS_POC_EUR) with unique email and phone.
  9. Click Save once to submit the multi-POC batch to POST /api/CompanyPoc/addUpdatepoc.
  10. Assert all added POC rows appear in the expanded POC table for the company.
"""

import logging
import pytest
from playwright.sync_api import Page, expect

from pages.company_page import CompanyPage
from workflows.lead.lead_workflow import LeadWorkflow
from utilities.matrix_data_generator import get_client_by_id

logger = logging.getLogger(__name__)


@pytest.mark.ui
def test_add_client_and_poc_flow(logged_in_page: Page, poc_count: int):
    page = logged_in_page
    company_page = CompanyPage(page)
    lead_workflow = LeadWorkflow(page)

    logger.info(f"Dynamic execution parameters: POC count requested = {poc_count}")

    # Retrieve Client 1 (United States) definition from matrix generator
    client_def = get_client_by_id(1)
    company_name = client_def["company_name"]
    initial = client_def.get("initial", "AGS")
    country = client_def["country"]
    country_code = client_def["country_code"]
    phone = client_def["primary_phone"]
    email = client_def["primary_email"]

    logger.info("==========================================================================")
    logger.info(f"TEST: Add Client '{company_name}' ({country}) and Row-Level POCs ({initial}_POC_XX)")
    logger.info("==========================================================================")

    # -------------------------------------------------------------------------
    # STEP 1: Navigate to Companies module
    # -------------------------------------------------------------------------
    logger.info("Step 1: Navigating to Company module (/company)...")
    company_page.go_to_company()
    page.wait_for_timeout(1500)

    # -------------------------------------------------------------------------
    # STEP 2: Check if Company already exists; if not, create via Quick Lead
    # -------------------------------------------------------------------------
    logger.info(f"Step 2: Checking if company '{company_name}' exists in table...")
    company_page.search_company(company_name)
    page.wait_for_timeout(1000)

    company_row = page.locator("tbody tr").filter(has_text=company_name).first
    if company_row.count() == 0 or not company_row.is_visible():
        logger.info(f"Company '{company_name}' not found. Creating via Quick Lead form...")
        lead_workflow.create_quick_lead(
            company_name=company_name,
            country=country,
            country_code=country_code,
            email=email,
            phone=phone,
            service="PPC",
        )
        page.wait_for_timeout(2000)
        logger.info(f"Company '{company_name}' successfully provisioned.")

    # Return to /company and search for target company
    company_page.go_to_company()
    page.wait_for_timeout(1000)
    company_page.search_company(company_name)
    page.wait_for_timeout(1500)

    # -------------------------------------------------------------------------
    # STEP 3: Expand Company POCs using the User Icon
    # -------------------------------------------------------------------------
    logger.info(f"Step 3: Expanding POCs for '{company_name}' using user-icon...")
    company_page.expand_company_pocs(company_name)
    page.wait_for_timeout(1000)

    # Verify expanded sub-table row
    add_poc_btn = page.locator("button:has-text('Add New POC')").first
    expect(add_poc_btn).to_be_visible(timeout=10000)
    logger.info("Expanded POC sub-table is visible with 'Add New POC' button.")

    # -------------------------------------------------------------------------
    # STEP 4: Add POCs with Unique Values (No Duplicates) via Multi-POC Form
    # -------------------------------------------------------------------------
    target_pocs = client_def["pocs"][:poc_count]
    logger.info(f"Target POCs to process ({len(target_pocs)}): {[p['poc_name'] for p in target_pocs]}")

    missing_pocs = []
    for p_def in target_pocs:
        p_name = p_def["poc_name"]
        exists = page.locator("tr").filter(has_text=p_name).count() > 0
        if not exists:
            missing_pocs.append(p_def)

    if missing_pocs:
        logger.info(f"Step 4: Opening 'Add New POC' form for {len(missing_pocs)} missing POC(s)...")
        company_page.click_add_new_poc_button()
        page.wait_for_timeout(1000)

        for idx, p_def in enumerate(missing_pocs):
            if idx > 0:
                logger.info(f"Clicking 'Add More POC' to append Block {idx}...")
                company_page.click_add_more_poc_button(expected_next_index=idx)
            
            logger.info(f"Filling Block {idx} with '{p_def['poc_name']}' ({p_def['email']})...")
            company_page.fill_add_new_poc_form(
                name=p_def["poc_name"],
                email=p_def["email"],
                designation=p_def["designation"],
                phone=p_def["phone"],
                country_code=p_def["country_code"],
                same_as_phone=True,
                index=idx,
            )

        # Save the form
        logger.info("Saving multi-POC form...")
        company_page.save_add_new_poc_form()
        page.wait_for_timeout(2500)

    # -------------------------------------------------------------------------
    # STEP 5: Verify POC rows exist in expanded POC table
    # -------------------------------------------------------------------------
    logger.info("Step 5: Verifying POC rows in the expanded table...")
    company_page.go_to_company()
    company_page.search_company(company_name)
    company_page.expand_company_pocs(company_name)
    page.wait_for_timeout(1500)

    for p_def in target_pocs:
        p_name = p_def["poc_name"]
        p_row = page.locator("tr").filter(has_text=p_name).first
        expect(p_row).to_be_visible(timeout=10000)
        logger.info(f"VERIFIED: POC '{p_name}' is visible in company POC table!")

    logger.info("==========================================================================")
    logger.info(f"SUCCESS: {len(target_pocs)} POC(s) verified under '{company_name}'!")
    logger.info("==========================================================================")
