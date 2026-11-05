import logging
from typing import Any, Dict, List, Tuple
from playwright.sync_api import APIRequestContext, APIResponse
from utilities.api import base_api

logger = logging.getLogger(__name__)


class PresalesReportApiClient:
    """API Client for Presales Report Filter endpoints using Playwright APIRequestContext."""

    ENDPOINT = "https://infusive-back.jobvritta.com/api/Dropdown/PresalesReportFilter"

    def __init__(self, api_context: APIRequestContext):
        self.api_context = api_context

    def get_presales_report_filter(self) -> Tuple[APIResponse, Dict[str, Any]]:
        """
        Execute GET request to PresalesReportFilter API endpoint.
        Returns tuple of (Playwright APIResponse, parsed JSON dict).
        """
        logger.info("Executing GET request to: %s", self.ENDPOINT)
        try:
            response = self.api_context.get(self.ENDPOINT)
            logger.info("Received HTTP Status: %d %s", response.status, response.status_text)
            
            # Verify status code 200
            if response.status != 200:
                logger.error("API GET failed with status %d: %s", response.status, response.text())
            
            # Parse JSON body
            try:
                json_data = response.json()
            except Exception as err:
                logger.error("Failed to parse JSON response: %s", str(err))
                json_data = {}

            return response, json_data

        except Exception as exc:
            logger.error("Exception occurred while calling %s: %s", self.ENDPOINT, str(exc), exc_info=True)
            raise exc

    def get_unauthenticated(self, unauthenticated_context: APIRequestContext) -> APIResponse:
        """Execute GET request without auth headers to verify 401 Unauthorized handling."""
        logger.info("Executing unauthenticated GET request to: %s", self.ENDPOINT)
        return unauthenticated_context.get(self.ENDPOINT)

    @staticmethod
    def validate_schema(json_data: Dict[str, Any]) -> List[str]:
        """
        Validate schema, required keys, and field data types of the PresalesReportFilter response.
        Returns a list of error messages (empty list if schema is valid).
        """
        errors = []

        # 1. Top-Level Schema Validation
        if not isinstance(json_data, dict):
            errors.append(f"Expected top-level response to be dict, got {type(json_data).__name__}")
            return errors

        if "filterOptions" not in json_data:
            errors.append("Top-level key 'filterOptions' missing from response JSON.")
            return errors

        filter_options = json_data.get("filterOptions")
        if not isinstance(filter_options, dict):
            errors.append(f"Expected 'filterOptions' to be dict, got {type(filter_options).__name__}")
            return errors

        # 2. Category Level Validation ("Created By")
        if "Created By" not in filter_options:
            errors.append("'Created By' category key missing under 'filterOptions'.")
            return errors

        created_by_list = filter_options.get("Created By")
        if not isinstance(created_by_list, list):
            errors.append(f"Expected 'Created By' to be list, got {type(created_by_list).__name__}")
            return errors

        if len(created_by_list) == 0:
            errors.append("'Created By' filter options list is empty.")
            return errors

        logger.info("'Created By' list contains %d filter items", len(created_by_list))

        # 3. Item Level Key & Data Type Validation
        required_item_keys = {"id": int, "name": str}

        for idx, item in enumerate(created_by_list):
            if not isinstance(item, dict):
                errors.append(f"Item at index {idx} in 'Created By' is not a dict: {type(item).__name__}")
                continue

            for key, expected_type in required_item_keys.items():
                if key not in item:
                    errors.append(f"Item at index {idx} missing required key '{key}'")
                else:
                    val = item[key]
                    if val is None:
                        errors.append(f"Item at index {idx} key '{key}' is None, expected {expected_type.__name__}")
                    elif not isinstance(val, expected_type):
                        errors.append(
                            f"Item at index {idx} key '{key}' has type {type(val).__name__}, expected {expected_type.__name__}"
                        )

        return errors
