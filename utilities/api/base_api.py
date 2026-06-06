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

BASE_URL = os.getenv("BASE_API_URL")

USERS = {
    "admin": {
        "email": os.getenv("EMAIL"),
        "password": os.getenv("PASSWORD")
    }
}

_token_cache: dict = {}


def _is_token_expired(token: str) -> bool:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        exp = json.loads(base64.b64decode(payload)).get("exp", 0)
        return time.time() >= exp - 30
    except Exception:
        return True


def get_token(user: str = "admin") -> str:
    if user not in _token_cache or _is_token_expired(_token_cache[user]):
        creds = USERS[user]
        login_url = f"{BASE_URL}user/login"
        payload = {
            "email": creds["email"],
            "password": creds["password"]
        }
        logger.info(f"Attempting login to: {login_url}")
        response = requests.post(login_url, json=payload)
        if response.status_code != 200:
            logger.error(f"Login failed: {response.status_code} - {response.text}")
            response.raise_for_status()
        _token_cache[user] = response.json()["token"]
    return _token_cache[user]


def clear_token_cache():
    _token_cache.clear()


def _headers(user: str = "admin") -> dict:
    return {
        "Authorization": f"Bearer {get_token(user)}",
        "Content-Type": "application/json"
    }


def _fmt(data) -> str:
    return json.dumps(data, indent=2, default=str)


def get(endpoint: str, user: str = "admin", params: dict = None) -> dict:
    logger.info("GET %s | user: %s\nparams:\n%s", endpoint, user, _fmt(params))
    response = requests.get(f"{BASE_URL}{endpoint}", headers=_headers(user), params=params)
    response.raise_for_status()
    body = response.json()
    logger.info("GET %s → %s\n%s", endpoint, response.status_code, _fmt(body))
    return body


def post(endpoint: str, user: str = "admin", payload: dict = None) -> dict:
    logger.info("POST %s | user: %s\npayload:\n%s", endpoint, user, _fmt(payload))
    response = requests.post(f"{BASE_URL}{endpoint}", headers=_headers(user), json=payload)
    if response.status_code == 400:
        body = response.json() if response.text else {"message": response.text}
        logger.warning("POST %s → 400\n%s", endpoint, _fmt(body))
        return body
    response.raise_for_status()
    body = response.json()
    logger.info("POST %s → %s\n%s", endpoint, response.status_code, _fmt(body))
    return body


def put(endpoint: str, user: str = "admin", payload: dict = None) -> dict:
    logger.info("PUT %s | user: %s\npayload:\n%s", endpoint, user, _fmt(payload))
    response = requests.put(f"{BASE_URL}{endpoint}", headers=_headers(user), json=payload)
    if response.status_code == 400:
        body = response.json() if response.text else {"message": response.text}
        logger.warning("PUT %s → 400\n%s", endpoint, _fmt(body))
        return body
    response.raise_for_status()
    body = response.json()
    logger.info("PUT %s → %s\n%s", endpoint, response.status_code, _fmt(body))
    return body


def patch(endpoint: str, user: str = "admin", payload: dict = None) -> dict:
    logger.info("PATCH %s | user: %s\npayload:\n%s", endpoint, user, _fmt(payload))
    response = requests.patch(f"{BASE_URL}{endpoint}", headers=_headers(user), json=payload)
    if response.status_code == 400:
        body = response.json() if response.text else {"message": response.text}
        logger.warning("PATCH %s → 400\n%s", endpoint, _fmt(body))
        return body
    response.raise_for_status()
    body = response.json()
    logger.info("PATCH %s → %s\n%s", endpoint, response.status_code, _fmt(body))
    return body


def delete(endpoint: str, user: str = "admin") -> dict:
    logger.info("DELETE %s | user: %s", endpoint, user)
    response = requests.delete(f"{BASE_URL}{endpoint}", headers=_headers(user))
    if response.status_code == 400:
        body = response.json() if response.text else {"message": response.text}
        logger.warning("DELETE %s → 400\n%s", endpoint, _fmt(body))
        return body
    response.raise_for_status()
    body = response.json()
    logger.info("DELETE %s → %s\n%s", endpoint, response.status_code, _fmt(body))
    return body
