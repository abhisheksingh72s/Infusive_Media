import logging
import pytest
from playwright.sync_api import Playwright, APIRequestContext
from utilities.api import base_api
from utilities.api.permission_api_client import PermissionApiClient
from utilities.api.permission_matrix import (
    build_permission_matrix,
    format_matrix_table,
    export_multi_role_matrix_to_excel
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def permission_api_client(playwright: Playwright) -> PermissionApiClient:
    """
    Pytest fixture to initialize an authenticated Playwright APIRequestContext
    using reusable API login token session management for STAGE.
    """
    stg_base = base_api.STG_BASE_API_URL
    api_context: APIRequestContext = base_api.create_playwright_api_context(playwright, user="admin", base_url=stg_base)
    client = PermissionApiClient(api_context=api_context, endpoint_url=base_api.get_stg_api_baseurl(1))
    yield client
    api_context.dispose()


@pytest.fixture(scope="function")
def unauthenticated_context(playwright: Playwright) -> APIRequestContext:
    """Pytest fixture to provide an unauthenticated Playwright APIRequestContext."""
    context = playwright.request.new_context(
        extra_http_headers={"Content-Type": "application/json"}
    )
    yield context
    context.dispose()


class TestPagePermissionApi:
    """
    Pure Playwright API Automation Test Suite for Page Permission Endpoint (STG vs PROD).
    """

    def test_permission_api_status_and_headers(
        self, permission_api_client: PermissionApiClient
    ):
        """
        Validate HTTP Status Code 200 OK, Content-Type application/json, and non-empty response body.
        """
        logger.info("--- Starting Test: Page Permission Status & Headers Validation ---")

        response, json_data = permission_api_client.get_page_permissions(environment="STAGE")

        # 1. Assert HTTP Status 200 OK
        assert response.status == 200, (
            f"Expected Status 200 OK, got {response.status} ({response.status_text}). Body: {response.text()}"
        )
        logger.info("✓ Status Code Assertion Passed: 200 OK")

        # 2. Assert Non-Empty Response Body
        response_body = response.text()
        assert response_body is not None and len(response_body.strip()) > 0, "Response body is empty!"
        logger.info("✓ Non-Empty Response Body Assertion Passed (Length: %d bytes)", len(response_body))

        # 3. Assert Content-Type Header
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type.lower(), (
            f"Expected Content-Type 'application/json', got '{content_type}'"
        )
        logger.info("✓ Content-Type Header Assertion Passed: %s", content_type)

        # 4. Assert Valid JSON Response
        assert json_data is not None, "Parsed JSON response is None!"
        logger.info("✓ Valid JSON Assertion Passed")

    def test_permission_api_schema_and_types(
        self, permission_api_client: PermissionApiClient
    ):
        """
        Validate Page Permission API response schema and data payload structure.
        """
        logger.info("--- Starting Test: Page Permission Schema & Data Types ---")

        response, json_data = permission_api_client.get_page_permissions(environment="STAGE")

        assert response.status == 200, f"API Request failed with status {response.status}"

        # Validate Schema structure using PermissionApiClient helper
        schema_errors = PermissionApiClient.validate_permission_schema(json_data)
        assert len(schema_errors) == 0, (
            f"Permission Schema validation failed with {len(schema_errors)} error(s):\n"
            + "\n".join(f" - {err}" for err in schema_errors)
        )
        logger.info("✓ Permission API Schema Validation Passed")

    def test_permission_api_unauthenticated_negative(
        self,
        permission_api_client: PermissionApiClient,
        unauthenticated_context: APIRequestContext
    ):
        """
        Negative Test Case: Validate unauthenticated request to stg_api_baseurl returns HTTP 401 Unauthorized.
        """
        logger.info("--- Starting Test: Unauthenticated 401 Negative Case ---")

        response = permission_api_client.get_unauthenticated(unauthenticated_context)

        assert response.status == 401, (
            f"Expected Status 401 Unauthorized for unauthenticated request, got {response.status} ({response.status_text})"
        )
        logger.info("✓ Unauthenticated 401 Negative Test Assertion Passed")

    def test_reusable_api_login_token_caching(self):
        """
        Verify that reusable API login method caches token and reuses session token.
        """
        logger.info("--- Starting Test: Reusable API Login Token Caching ---")

        token_1 = base_api.get_token(user="admin", base_url=base_api.STG_BASE_API_URL)
        assert token_1, "Token should not be empty"

        token_2 = base_api.get_token(user="admin", base_url=base_api.STG_BASE_API_URL)
        assert token_1 == token_2, "Token should be cached and reused while session is valid"
        logger.info("✓ Token Caching and Reuse Assertion Passed")

    def test_permission_matrix_strict_pass_fail_validation(self):
        """
        Unit Test: Verify that 10-column permission comparison matrix strictly evaluates Status & Difference.
        """
        logger.info("--- Starting Test: Strict 10-Column Pass/Fail Permission Matrix Validation ---")

        stage_sample = [
            {
                "id": 192,
                "name": "Meeting",
                "permission": True,
                "features": [
                    {"id": 199, "name": "Edit Meeting", "permission": False},
                    {"id": 195, "name": "showAllData", "permission": True},
                    {"id": 194, "name": "showMyCreatedList", "permission": False}
                ]
            },
            {
                "id": 19,
                "name": "MyLeads",
                "permission": False,
                "features": [
                    {"id": 72, "name": "showMyCreatedList", "permission": True}
                ]
            }
        ]

        prod_sample = [
            {
                "id": 192,
                "name": "Meeting",
                "permission": True,
                "features": [
                    {"id": 199, "name": "Edit Meeting", "permission": True},   # STG=FALSE, PROD=TRUE -> FAIL
                    {"id": 195, "name": "showAllData", "permission": True},    # STG=TRUE, PROD=TRUE -> PASS
                    {"id": 194, "name": "showMyCreatedList", "permission": False} # STG=FALSE, PROD=FALSE -> PASS
                ]
            },
            {
                "id": 19,
                "name": "MyLeads",
                "permission": False,
                "features": [
                    {"id": 72, "name": "showMyCreatedList", "permission": False} # STG=TRUE, PROD=FALSE -> FAIL
                ]
            }
        ]

        matrix = build_permission_matrix(stage_sample, prod_sample, role="Admin")

        table_log = format_matrix_table(matrix)
        logger.info("\n" + table_log)

        # Validate Edit Meeting: STG=FALSE, PROD=TRUE -> FAIL, "Permission enabled in Prod"
        edit_row = next(r for r in matrix if r["Feature"] == "Edit Meeting")
        assert edit_row["Page in Stage"] == "Yes"
        assert edit_row["Page in Prod"] == "Yes"
        assert edit_row["Feature in Stage"] == "Yes"
        assert edit_row["Feature in Prod"] == "Yes"
        assert edit_row["Stage Permission"] == "FALSE"
        assert edit_row["Prod Permission"] == "TRUE"
        assert edit_row["Status"] == "FAIL"
        assert edit_row["Difference"] == "Permission enabled in Prod"

        # Validate showAllData: STG=TRUE, PROD=TRUE -> PASS, ""
        show_all_row = next(r for r in matrix if r["Feature"] == "showAllData")
        assert show_all_row["Stage Permission"] == "TRUE"
        assert show_all_row["Prod Permission"] == "TRUE"
        assert show_all_row["Status"] == "PASS"
        assert show_all_row["Difference"] == ""

        # Validate showMyCreatedList for MyLeads: STG=TRUE, PROD=FALSE -> FAIL, "Permission disabled in Prod"
        myleads_feat_row = next(r for r in matrix if r["Page"] == "MyLeads" and r["Feature"] == "showMyCreatedList")
        assert myleads_feat_row["Stage Permission"] == "TRUE"
        assert myleads_feat_row["Prod Permission"] == "FALSE"
        assert myleads_feat_row["Status"] == "FAIL"
        assert myleads_feat_row["Difference"] == "Permission disabled in Prod"

        logger.info("✓ Strict 10-Column PASS/FAIL Matrix Logic Validation Passed")

    def test_multi_role_permission_matrix_excel_export(self, playwright: Playwright):
        """
        Build Page & Feature Permission Comparison Matrix comparing STG vs PROD APIs across all roles:
        - STG API Base URL: BASE_API_URL_STG (https://infusive-back.jobvritta.com/api/)
        - PROD API Base URL: BASE_API_URL_PROD (https://crmapi.infusivemedia.com/api/)

        Worksheets created:
        - Summary
        - Admin
        - BDM
        - Pre Sales
        - Team Lead
        - Manager

        Updated directly in reports/Permission_Comparison_Matrix.xlsx.
        """
        logger.info("--- Starting Test: Multi-Role STG vs PROD Permission Matrix Excel Export ---")

        role_configs = [
            ("Admin", 1),
            ("BDM", 2),
            ("Pre Sales", 3),
            ("Team Lead", 4),
            ("Manager", 5)
        ]

        stg_base = base_api.STG_BASE_API_URL
        prod_base = base_api.PROD_BASE_API_URL

        stg_context = base_api.create_playwright_api_context(playwright, user="admin", base_url=stg_base)
        prod_context = base_api.create_playwright_api_context(playwright, user="admin", base_url=prod_base)

        role_matrices = {}

        try:
            for role_name, role_id in role_configs:
                stg_url = f"{stg_base.rstrip('/')}/page/permission/{role_id}"
                prod_url = f"{prod_base.rstrip('/')}/page/permission/{role_id}"

                stg_client = PermissionApiClient(api_context=stg_context, endpoint_url=stg_url)
                prod_client = PermissionApiClient(api_context=prod_context, endpoint_url=prod_url)

                stg_response, stg_json = stg_client.get_page_permissions(environment="STAGE")
                prod_response, prod_json = prod_client.get_page_permissions(environment="PRODUCTION")

                matrix_rows = build_permission_matrix(stage_json=stg_json, prod_json=prod_json, role=role_name)
                role_matrices[role_name] = matrix_rows
                logger.info("Built STG vs PROD Matrix for Role '%s' (%d rows)", role_name, len(matrix_rows))

            # Print Admin matrix table to terminal log
            table_output = format_matrix_table(role_matrices["Admin"])
            logger.info("\n" + table_output)

            # Update single Excel report file directly
            excel_path = export_multi_role_matrix_to_excel(role_matrices, filepath="reports/Permission_Comparison_Matrix.xlsx")
            assert excel_path.exists(), f"Failed to update matrix XLSX file at {excel_path}"
            logger.info("✓ Successfully updated single Excel (.xlsx) report at: %s", excel_path)

        finally:
            stg_context.dispose()
            prod_context.dispose()
