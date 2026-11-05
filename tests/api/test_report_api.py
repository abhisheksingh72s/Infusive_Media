import logging
import pytest
from playwright.sync_api import Playwright, APIRequestContext
from utilities.api import base_api
from utilities.api.report_api_client import ReportApiClient as PresalesReportApiClient

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def api_client(playwright: Playwright) -> PresalesReportApiClient:
    """
    Pytest fixture to initialize an authenticated Playwright APIRequestContext
    and return an instance of PresalesReportApiClient (ReportApiClient).
    """
    token = base_api.get_token(user="admin")
    api_context: APIRequestContext = playwright.request.new_context(
        extra_http_headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    client = PresalesReportApiClient(api_context=api_context)
    yield client
    api_context.dispose()


@pytest.fixture(scope="function")
def unauthenticated_context(playwright: Playwright) -> APIRequestContext:
    """Pytest fixture to provide an unauthenticated Playwright APIRequestContext."""
    context = playwright.request.new_context(extra_http_headers={"Content-Type": "application/json"})
    yield context
    context.dispose()


class TestPresalesReportApi:
    """Pure API Automation Test Suite for Presales Report Endpoint."""

    def test_presales_report_status_and_headers(self, api_client: PresalesReportApiClient):
        """
        Validate HTTP Status Code 200 OK, non-empty payload, and valid JSON Content-Type.
        """
        logger.info("--- Starting Test: Status Code & Headers Validation ---")

        response, json_data = api_client.get_presales_report_filter()

        # 1. Assert Status Code == 200
        assert response.status == 200, (
            f"Expected Status 200 OK, got {response.status} ({response.status_text}). Body: {response.text()}"
        )
        logger.info("✓ Status Code Assertion Passed: 200 OK")

        # 2. Assert Response is Not Empty
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
        assert isinstance(json_data, (dict, list)), f"Expected JSON dict or list, got {type(json_data).__name__}"
        assert len(json_data) > 0, "Parsed JSON payload is empty!"
        logger.info("✓ Valid JSON Assertion Passed")

    def test_presales_report_schema_and_types(self, api_client: PresalesReportApiClient):
        """
        Validate Response Schema and data structure for report endpoint.
        """
        logger.info("--- Starting Test: Schema & Data Types Validation ---")

        response, json_data = api_client.get_presales_report_filter()

        assert response.status == 200, f"API Request failed with status {response.status}"

        # 1. Schema & Key Assertions using ApiClient validator
        schema_errors = PresalesReportApiClient.validate_schema(json_data)
        assert len(schema_errors) == 0, (
            f"Schema validation failed with {len(schema_errors)} error(s):\n"
            + "\n".join(f" - {err}" for err in schema_errors)
        )
        logger.info("✓ Top-Level & Category Schema Validation Passed")

    def test_presales_report(
        self, api_client: PresalesReportApiClient, unauthenticated_context: APIRequestContext
    ):
        """
        Negative Test Case: Validate unauthenticated request returns 401 Unauthorized.
        """
        logger.info("--- Starting Test: Unauthenticated 401 Negative Case ---")

        response = api_client.get_unauthenticated(unauthenticated_context)

        assert response.status == 401, (
            f"Expected Status 401 Unauthorized for unauthenticated request, got {response.status} ({response.status_text})"
        )
        logger.info("✓ Unauthenticated 401 Negative Test Assertion Passed")
