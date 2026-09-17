import time
import base64
import json
import logging
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BASE_API_URL", os.getenv("BASE_API_URL_STG", "https://infusive-back.jobvritta.com/api/"))
STG_BASE_API_URL = os.getenv("BASE_API_URL_STG", "https://infusive-back.jobvritta.com/api/")
PROD_BASE_API_URL = os.getenv("BASE_API_URL_PROD", "https://crmapi.infusivemedia.com/api/")

USERS = {
    "admin": {
        "email": os.getenv("EMAIL", "Admin@infusive.com"),
        "password": os.getenv("PASSWORD", "123456")
    }
}

_token_cache: dict = {}


def get_stg_api_baseurl(role_id: int = 1) -> str:
    """Return Stage Page Permission API endpoint URL using BASE_API_URL_STG or stg_api_baseurl from .env."""
    load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)
    base_stg = (
        os.getenv("BASE_API_URL_STG")
        or os.getenv("STG_API_BASEURL")
        or os.getenv("stg_api_baseurl")
        or "https://infusive-back.jobvritta.com/api/"
    ).rstrip("/")
    if "/page/permission" in base_stg:
        return base_stg
    return f"{base_stg}/page/permission/{role_id}"


def get_prod_api_baseurl(role_id: int = 1) -> str:
    """Return Production Page Permission API endpoint URL using BASE_API_URL_PROD or prod_api_baseurl from .env."""
    load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)
    base_prod = (
        os.getenv("BASE_API_URL_PROD")
        or os.getenv("PROD_API_BASEURL")
        or os.getenv("prod_api_baseurl")
        or "https://crmapi.infusivemedia.com/api/"
    ).rstrip("/")
    if "/page/permission" in base_prod:
        return base_prod
    return f"{base_prod}/page/permission/{role_id}"


def _is_token_expired(token: str) -> bool:
    """Check whether a JWT bearer token is expired or within 30s of expiration."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        exp = json.loads(base64.b64decode(payload)).get("exp", 0)
        return time.time() >= exp - 30
    except Exception:
        return True


def get_token(user: str = "admin", base_url: str = None) -> str:
    """
    Reusable API Login method.
    Logs in via API and caches the bearer token per target base_url.
    Reuses cached token for all subsequent requests as long as session is valid.
    """
    target_base = (base_url or BASE_URL).rstrip("/")
    cache_key = f"{user}_{target_base}"

    if cache_key not in _token_cache or _is_token_expired(_token_cache[cache_key]):
        creds = USERS.get(user)
        if not creds or not creds.get("email"):
            creds = {
                "email": os.getenv("EMAIL", "Admin@infusive.com"),
                "password": os.getenv("PASSWORD", "123456")
            }

        login_url = f"{target_base}/user/login"
        payload = {
            "email": creds["email"],
            "password": creds["password"]
        }
        logger.info(f"Attempting API login for '{user}' to: {login_url}")
        response = requests.post(login_url, json=payload)
        logger.info(f"API Login Response [{response.status_code}]: {response.text}")
        if response.status_code != 200:
            logger.error(f"API Login failed for '{user}': {response.status_code} - {response.text}")
            response.raise_for_status()

        token_val = response.json().get("token")
        if not token_val:
            raise ValueError(f"No token received in login response for '{user}'")

        _token_cache[cache_key] = token_val
        logger.info(f"API Login successful for {target_base}. Token cached for session.")
    return _token_cache[cache_key]


def clear_token_cache():
    """Clear cached authentication tokens."""
    _token_cache.clear()


def create_playwright_api_context(playwright, user: str = "admin", base_url: str = None, extra_headers: dict = None):
    """
    Create a Playwright APIRequestContext pre-authenticated with valid session token.
    Uses reusable API login token session for specified base_url (Stage or Prod).
    """
    token = get_token(user=user, base_url=base_url)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    if extra_headers:
        headers.update(extra_headers)
    return playwright.request.new_context(extra_http_headers=headers)


def _headers(user: str = "admin", base_url: str = None) -> dict:
    return {
        "Authorization": f"Bearer {get_token(user, base_url)}",
        "Content-Type": "application/json"
    }


def _fmt(data) -> str:
    return json.dumps(data, indent=2, default=str)


def get(endpoint: str, user: str = "admin", params: dict = None, base_url: str = None) -> dict:
    target_base = (base_url or BASE_URL).rstrip("/")
    logger.info("GET %s/%s | user: %s\nparams:\n%s", target_base, endpoint, user, _fmt(params))
    response = requests.get(f"{target_base}/{endpoint.lstrip('/')}", headers=_headers(user, target_base), params=params)
    response.raise_for_status()
    body = response.json()
    logger.info("GET %s/%s → %s\n%s", target_base, endpoint, response.status_code, _fmt(body))
    return body


def post(endpoint: str, user: str = "admin", payload: dict = None, base_url: str = None) -> dict:
    target_base = (base_url or BASE_URL).rstrip("/")
    logger.info("POST %s/%s | user: %s\npayload:\n%s", target_base, endpoint, user, _fmt(payload))
    response = requests.post(f"{target_base}/{endpoint.lstrip('/')}", headers=_headers(user, target_base), json=payload)
    if response.status_code == 400:
        body = response.json() if response.text else {"message": response.text}
        logger.warning("POST %s/%s → 400\n%s", target_base, endpoint, _fmt(body))
        return body
    response.raise_for_status()
    body = response.json()
    logger.info("POST %s/%s → %s\n%s", target_base, endpoint, response.status_code, _fmt(body))
    return body
