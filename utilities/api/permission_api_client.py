import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from playwright.sync_api import APIRequestContext, APIResponse
from utilities.api import base_api

logger = logging.getLogger(__name__)


class PermissionApiClient:
    """
    Playwright API Client for Page Permission endpoint (stg_api_baseurl).
    Handles page permission checks using Playwright APIRequestContext and reusable login token sessions.
    """

    def __init__(
        self,
        api_context: Optional[APIRequestContext] = None,
        endpoint_url: Optional[str] = None
    ):
        self.api_context = api_context
        self.endpoint_url = endpoint_url or base_api.get_stg_api_baseurl()

    def get_page_permissions(
        self,
        user: str = "admin",
        headers: Optional[Dict[str, str]] = None,
        environment: str = "STAGE"
    ) -> Tuple[APIResponse, Any]:
        """
        Execute GET request to stg_api_baseurl (page permissions API) using Playwright APIRequestContext.
        Uses cached valid token session and outputs specified logger format to terminal.
        """
        target_url = self.endpoint_url or base_api.get_stg_api_baseurl()
        token = base_api.get_token(user=user)

        req_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        if headers:
            req_headers.update(headers)

        if not self.api_context:
            logger.warning("No api_context provided to PermissionApiClient, raising Error.")
            raise RuntimeError("APIRequestContext must be provided for Playwright API testing.")

        response: APIResponse = self.api_context.get(target_url, headers=req_headers)

        json_data = None
        try:
            json_data = response.json()
        except Exception as err:
            logger.warning("Could not parse response body as JSON: %s", str(err))
            json_data = response.text()

        role, page_name, perms = self.extract_permission_details(json_data, user=user)

        # Output exact requested logger format to terminal
        formatted_log = self.format_get_page_permission_log(
            environment=environment,
            method="GET",
            url=target_url,
            status_code=response.status,
            headers=dict(response.headers),
            json_or_text_data=json_data,
            role=role,
            page=page_name,
            parsed_permissions=perms
        )
        logger.info("\n" + formatted_log)

        return response, json_data

    def get_unauthenticated(
        self,
        unauthenticated_context: APIRequestContext
    ) -> APIResponse:
        """
        Execute unauthenticated GET request to verify security enforcement (HTTP 401).
        """
        target_url = self.endpoint_url or base_api.get_stg_api_baseurl()
        response = unauthenticated_context.get(target_url)
        return response

    @staticmethod
    def extract_permission_details(json_data: Any, user: str = "Admin") -> Tuple[str, str, Dict[str, bool]]:
        """
        Extract role, page, and permissions dict from response payload.
        """
        role = user.capitalize() if user else "Admin"
        page = "Lead"
        perms = {"View": False, "Add": False, "Edit": False, "Delete": False}

        if isinstance(json_data, dict):
            page = str(json_data.get("name") or json_data.get("page") or json_data.get("module") or "Lead")

            permissions_list = json_data.get("permissions")
            if isinstance(permissions_list, list):
                for item in permissions_list:
                    if isinstance(item, dict):
                        p_name = str(item.get("name") or item.get("label") or "").strip()
                        p_val = item.get("permission", item.get("isFeature", item.get("value", False)))
                        for target_key in ["View", "Add", "Edit", "Delete"]:
                            if p_name.lower() == target_key.lower():
                                perms[target_key] = bool(p_val)

            # Check direct boolean fields
            for target_key in ["View", "Add", "Edit", "Delete"]:
                key_lower = target_key.lower()
                for field in [key_lower, f"is{target_key}", f"can{target_key}"]:
                    if field in json_data:
                        perms[target_key] = bool(json_data[field])

        return role, page, perms

    @staticmethod
    def format_get_page_permission_log(
        environment: str,
        method: str,
        url: str,
        status_code: int,
        headers: Dict[str, str],
        json_or_text_data: Any,
        role: str = "Admin",
        page: str = "Lead",
        parsed_permissions: Optional[Dict[str, bool]] = None
    ) -> str:
        """
        Format GET Page Permission log according to exact user specification:

        ================================================================================
        STAGE - GET PAGE PERMISSION
        ================================================================================
        METHOD      : GET
        URL         : https://stage-url/api/page/permission/1
        STATUS CODE : 200

        --- RESPONSE HEADERS ---
        content-type: application/json; charset=utf-8
        ...

        --- COMPLETE RESPONSE BODY ---
        {
            "id": 1,
            "name": "Lead",
            "permissions": [
                {
                    "name": "View",
                    "permission": false
                },
                {
                    "name": "Add",
                    "permission": false
                }
            ]
        }

        --- PARSED PERMISSIONS ---
        Role   : Admin
        Page   : Lead
        View   : false
        Add    : false
        Edit   : false
        Delete : false
        ================================================================================
        """
        if parsed_permissions is None:
            parsed_permissions = {"View": False, "Add": False, "Edit": False, "Delete": False}

        headers_str = "\n".join(f"{k}: {v}" for k, v in headers.items()) if isinstance(headers, dict) else str(headers)

        if isinstance(json_or_text_data, (dict, list)):
            body_str = json.dumps(json_or_text_data, indent=4)
        else:
            body_str = str(json_or_text_data)

        v = "true" if parsed_permissions.get("View", False) else "false"
        a = "true" if parsed_permissions.get("Add", False) else "false"
        e = "true" if parsed_permissions.get("Edit", False) else "false"
        d = "true" if parsed_permissions.get("Delete", False) else "false"

        lines = [
            "=" * 80,
            f"{environment.upper()} - GET PAGE PERMISSION",
            "=" * 80,
            f"METHOD      : {method.upper()}",
            f"URL         : {url}",
            f"STATUS CODE : {status_code}",
            "",
            "--- RESPONSE HEADERS ---",
            headers_str,
            "",
            "--- COMPLETE RESPONSE BODY ---",
            body_str,
            "",
            "--- PARSED PERMISSIONS ---",
            f"Role   : {role}",
            f"Page   : {page}",
            f"View   : {v}",
            f"Add    : {a}",
            f"Edit   : {e}",
            f"Delete : {d}",
            "=" * 80
        ]
        return "\n".join(lines)

    @staticmethod
    def format_permission_response(environment: str, role: str, page: str, permissions: Dict[str, bool]) -> str:
        """Format single environment permission response log."""
        env_title = f"{environment.upper()} - PAGE PERMISSION RESPONSE"
        v = "true" if permissions.get("View", False) else "false"
        a = "true" if permissions.get("Add", False) else "false"
        e = "true" if permissions.get("Edit", False) else "false"
        d = "true" if permissions.get("Delete", False) else "false"

        lines = [
            "=" * 80,
            env_title,
            "=" * 80,
            f"Role: {role}",
            f"Page: {page}",
            "Permissions:",
            f"    View   : {v}",
            f"    Add    : {a}",
            f"    Edit   : {e}",
            f"    Delete : {d}",
            "=" * 80
        ]
        return "\n".join(lines)

    @staticmethod
    def compare_permission_logs(role: str, page: str, stage_perms: Dict[str, bool], prod_perms: Dict[str, bool]) -> str:
        """Format permission comparison log between STAGE and PRODUCTION."""
        lines = [
            "                         PERMISSION COMPARISON",
            "=" * 80,
            f"Role       : {role}",
            f"Page       : {page}"
        ]

        for key in ["View", "Add", "Edit", "Delete"]:
            stg_val = bool(stage_perms.get(key, False))
            prod_val = bool(prod_perms.get(key, False))

            stg_str = "true" if stg_val else "false"
            prod_str = "true" if prod_val else "false"

            if stg_val == prod_val:
                status = "PASS"
                comment = ""
            else:
                status = "FAIL"
                comment = f"  <-- Stage={stg_str}, Prod={prod_str}"

            lines.append(f"{key:<11}: {status}{comment}")

        lines.append("=" * 80)
        return "\n".join(lines)

    @staticmethod
    def validate_permission_schema(json_data: Any) -> List[str]:
        """Validate schema structure of page permission API response."""
        errors = []
        if json_data is None:
            errors.append("Permission API response payload is None.")
            return errors

        if not isinstance(json_data, (dict, list)):
            errors.append(f"Expected response to be dict or list, got {type(json_data).__name__}")
            return errors

        if isinstance(json_data, dict):
            if len(json_data) == 0:
                errors.append("Permission API response dict is empty.")
        elif isinstance(json_data, list):
            if len(json_data) == 0:
                errors.append("Permission API response list is empty.")

        return errors
