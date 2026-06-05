import os

import pytest
import requests

from utilities.api import base_api

BASE_API_URL = os.getenv("BASE_API_URL")
LOGIN_URL = f"{BASE_API_URL}user/login"
VALID_EMAIL = os.getenv("EMAIL")
VALID_PASSWORD = os.getenv("PASSWORD")


# ---------------------------------------------------------------------------
# Happy Path
# ---------------------------------------------------------------------------

def test_login_valid_credentials():
    """Valid admin credentials must return a non-empty token."""
    token = base_api.get_token(user="admin")
    assert token, "Token should not be empty for valid credentials"


# ---------------------------------------------------------------------------
# Invalid Credentials
# ---------------------------------------------------------------------------

def test_login_invalid_email():
    """Login with an unregistered email must return a 4xx status code."""
    response = requests.post(LOGIN_URL, json={
        "email": "invalid_user@notexist.com",
        "password": VALID_PASSWORD,
    })
    assert response.status_code in (400, 401, 403, 404), (
        f"Expected 4xx for invalid email, got {response.status_code}"
    )


def test_login_invalid_password():
    """Login with a wrong password must return a 4xx status code."""
    response = requests.post(LOGIN_URL, json={
        "email": VALID_EMAIL,
        "password": "wrongpassword_xyz",
    })
    assert response.status_code in (400, 401, 403, 404), (
        f"Expected 4xx for invalid password, got {response.status_code}"
    )


def test_login_invalid_email_and_password():
    """Login with both email and password wrong must return a 4xx status code."""
    response = requests.post(LOGIN_URL, json={
        "email": "nobody@notexist.com",
        "password": "wrongpassword_xyz",
    })
    assert response.status_code in (400, 401, 403, 404), (
        f"Expected 4xx for invalid email and password, got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# Empty Field Validation
# ---------------------------------------------------------------------------

def test_login_empty_email():
    """Login with an empty email field must return a 4xx status code."""
    response = requests.post(LOGIN_URL, json={
        "email": "",
        "password": VALID_PASSWORD,
    })
    assert response.status_code in (400, 401, 422), (
        f"Expected 4xx for empty email, got {response.status_code}"
    )


def test_login_empty_password():
    """Login with an empty password field must return a 4xx status code."""
    response = requests.post(LOGIN_URL, json={
        "email": VALID_EMAIL,
        "password": "",
    })
    assert response.status_code in (400, 401, 422), (
        f"Expected 4xx for empty password, got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# Missing Field Validation
# ---------------------------------------------------------------------------

def test_login_missing_email_field():
    """Payload without an email key must return a 4xx status code."""
    response = requests.post(LOGIN_URL, json={
        "password": VALID_PASSWORD,
    })
    assert response.status_code in (400, 422), (
        f"Expected 4xx for missing email field, got {response.status_code}"
    )


def test_login_missing_password_field():
    """Payload without a password key must return a 4xx status code."""
    response = requests.post(LOGIN_URL, json={
        "email": VALID_EMAIL,
    })
    assert response.status_code in (400, 422), (
        f"Expected 4xx for missing password field, got {response.status_code}"
    )


def test_login_empty_payload():
    """Empty payload must return a 4xx status code."""
    response = requests.post(LOGIN_URL, json={})
    assert response.status_code in (400, 422), (
        f"Expected 4xx for empty payload, got {response.status_code}"
    )
