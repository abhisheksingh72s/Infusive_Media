import os

import pytest
from dotenv import load_dotenv

from pages.login_page import LoginPage
from utilities.api import base_api

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")


@pytest.fixture(scope="session", autouse=True)
def authenticate():
    try:
        base_api.get_token(user="admin")
    except Exception as exc:
        pytest.fail(
            f"Session-level authentication failed. "
            f"Verify credentials and API availability. Error: {exc}"
        )


@pytest.fixture(scope="function", autouse=True)
def set_default_timeout(page):
    page.set_default_timeout(10000)
    page.set_default_navigation_timeout(10000)


@pytest.fixture(scope="function")
def logged_in_page(page):
    """Shared login fixture. Returns the authenticated Playwright page instance."""
    lp = LoginPage(page)
    lp.load()
    lp.login(EMAIL, PASSWORD)
    lp.wait_for_dashboard()
    return page
