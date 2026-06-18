import os
import re
import logging
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
ENV_FILE = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=True)
logging.getLogger("faker").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

from pages.login_page import LoginPage

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
REPORTS_ROOT = Path("reports")
MODULE_REPORT_DIRS = ("screenshot", "traceview", "videos", "downloads")


def _safe_name(value):
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value.strip("_") or "artifact"


def _module_name_from_item(item):
    path = Path(str(item.fspath))
    parts = [part.lower() for part in path.parts]

    if "tests" in parts:
        relative_parts = list(path.parts[parts.index("tests") + 1 :])
        meaningful_parts = [
            part
            for part in relative_parts[:-1]
            if part.lower() not in {"ui", "api", "__pycache__"}
        ]
        if meaningful_parts:
            return _safe_name(meaningful_parts[0].lower())

    name = path.stem
    if name.startswith("test_"):
        name = name[5:]
    if name.endswith("_test"):
        name = name[:-5]
    if name.endswith("_api"):
        name = name[:-4]
    return _safe_name(name.lower())


def _module_report_path(item, report_type):
    module_name = _module_name_from_item(item)
    report_path = REPORTS_ROOT / module_name / report_type
    report_path.mkdir(parents=True, exist_ok=True)
    return report_path


def _test_artifact_name(item, extension):
    return f"{_safe_name(item.nodeid)}.{extension}"


def pytest_configure(config):
    REPORTS_ROOT.mkdir(exist_ok=True)


def pytest_collection_modifyitems(items):
    for item in items:
        for report_type in MODULE_REPORT_DIRS:
            _module_report_path(item, report_type)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    setattr(item, f"rep_{call.when}", outcome.get_result())


def _credential_records():
    records = []
    if EMAIL and PASSWORD:
        records.append({"email": EMAIL, "password": PASSWORD, "source": "EMAIL"})

    user_indexes = {
        match.group(1)
        for key in os.environ
        if (match := re.match(r"USER_(\d+)_EMAIL$", key))
    }
    for index in sorted(user_indexes):
        email = os.getenv(f"USER_{index}_EMAIL")
        password = os.getenv(f"USER_{index}_PASSWORD")
        if email and password:
            records.append(
                {
                    "email": email,
                    "password": password,
                    "source": f"USER_{index}",
                }
            )
    return records


def _credentials_for_email(email):
    if not email:
        email = EMAIL

    for record in _credential_records():
        if record["email"].casefold() == email.casefold():
            return record

    known_emails = ", ".join(record["email"] for record in _credential_records())
    pytest.fail(
        f"No .env credentials found for email '{email}'. "
        f"Available emails: {known_emails}"
    )


def _login_email_from_request(request):
    if hasattr(request, "param"):
        return request.param

    marker = request.node.get_closest_marker("login_as")
    if marker:
        if marker.args:
            return marker.args[0]
        return marker.kwargs.get("email")

    return EMAIL


@pytest.fixture(scope="function", autouse=True)
def set_default_timeout(page):
    page.set_default_timeout(30000)
    page.set_default_navigation_timeout(30000)



@pytest.fixture(scope="function", autouse=True)
def monitor_api_failures(page):
    """Monitor and print any API failures (HTTP status >= 400) during UI tests."""
    def handle_response(response):
        if "/api/" in response.url.lower():
            if response.status >= 400:
                logger.warning(
                    "API Error detected: %s %s returned HTTP %s",
                    response.request.method,
                    response.url,
                    response.status
                )
                print(
                    f"\n[API ERROR TRIGGERED] Method: {response.request.method} | "
                    f"URL: {response.url} | Status: {response.status}"
                )
    page.on("response", handle_response)
    yield


@pytest.fixture(scope="function", autouse=True)
def module_reports(request):
    for report_type in MODULE_REPORT_DIRS:
        _module_report_path(request.node, report_type)

    if "page" not in request.fixturenames:
        yield
        return

    page = request.getfixturevalue("page")
    trace_path = _module_report_path(request.node, "traceview") / _test_artifact_name(
        request.node, "zip"
    )

    tracing_started = False
    try:
        page.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        tracing_started = True
    except Exception:
        tracing_started = False

    yield

    report = getattr(request.node, "rep_call", None)
    if report and report.failed:
        screenshot_path = _module_report_path(
            request.node, "screenshot"
        ) / _test_artifact_name(request.node, "png")
        try:
            page.screenshot(path=str(screenshot_path), full_page=True)
        except Exception:
            pass

    if tracing_started:
        try:
            page.context.tracing.stop(path=str(trace_path))
        except Exception:
            pass


@pytest.fixture(scope="function")
def logged_in_page(page, request):
    """UI login fixture. Selects credentials from .env by email."""
    credentials = _credentials_for_email(_login_email_from_request(request))
    logger.info("Logging in through UI as: %s", credentials["email"])

    lp = LoginPage(page)
    lp.load()
    lp.login(credentials["email"], credentials["password"])
    lp.wait_for_dashboard()
    return page
