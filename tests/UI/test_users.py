import time
import random
import pytest
from faker import Faker

from pages.users_page import UsersPage

fake = Faker("en_IN")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def users_page(logged_in_page):
    """Navigate to Users section after login and return UsersPage."""
    up = UsersPage(logged_in_page)
    up.go_to_users()
    return up


# ---------------------------------------------------------------------------
# Positive Test Scenarios
# ---------------------------------------------------------------------------

def test_add_new_user_modal_opens(users_page):
    """1. Verify Add New User modal opens successfully."""
    users_page.click_add_new_user()
    assert users_page.is_add_user_dialog_visible(), "Add New User dialog did not open."


def test_create_user_with_valid_data(users_page):
    """
    3. Verify user creation with valid data.
    4. Verify role selection functionality.
    5. Verify success notification after user creation.
    6. Verify newly created user appears in the user grid.
    8. Verify dynamic user creation using unique email and user id.
    """
    timestamp = int(time.time())
    user_id = "134"
    name = fake.name()
    email = f"{fake.user_name()}_{timestamp}@test.com"
    password = "Abhi1234"
    mobile = (
        f"{fake.random_element(elements=('6', '7', '8', '9'))}"
        f"{fake.random_number(digits=9, fix_len=True)}"
    )
    role = "Team Lead"

    users_page.click_add_new_user()
    users_page.fill_user_details(user_id, name, email, password, mobile)
    users_page.select_role(role)
    users_page.click_submit()

    assert users_page.is_notification_visible(), "Success notification was not displayed."

    users_page.page.wait_for_timeout(1000)
    try:
        assert users_page.is_user_row_visible(email), f"Newly created user '{email}' not found in the grid."
    except AssertionError:
        users_page.page.screenshot(path="reports/users/screenshot/test_create_user_grid_failure.png")
        raise


def test_search_user(users_page):
    """7. Verify user search after creation."""
    timestamp = int(time.time())
    user_id = "134"
    name = f"SearchUser_{timestamp}"
    email = f"search_{timestamp}@test.com"
    mobile = f"9{random.randint(100000000, 999999999)}"

    users_page.click_add_new_user()
    users_page.fill_user_details(user_id, name, email, "Abhi1234", mobile)
    users_page.select_role("Admin")
    users_page.click_submit()
    users_page.is_notification_visible()
    users_page.page.wait_for_timeout(1000)

    users_page.search_user(email)
    assert users_page.is_user_row_visible(email), f"Search result for '{email}' not found."


# ---------------------------------------------------------------------------
# Negative Test Scenarios
# ---------------------------------------------------------------------------

def test_create_user_without_user_id(users_page):
    """1. Create user without User ID - dialog should remain open (validation blocks submission)."""
    users_page.click_add_new_user()
    users_page.submit_empty_user_id()
    assert users_page.is_add_user_dialog_visible(), "Dialog should stay open when User ID is missing."


def test_create_user_without_name(users_page):
    """2. Create user without Name - dialog should remain open (validation blocks submission)."""
    users_page.click_add_new_user()
    users_page.fill_user_details("1234", "", "test@test.com", "Abhi1234", "9999999999")
    users_page.select_role("Team Lead")
    users_page.click_submit()
    assert users_page.is_add_user_dialog_visible(), "Dialog should stay open when Name is missing."


def test_create_user_without_email(users_page):
    """3. Create user without Email - dialog should remain open (validation blocks submission)."""
    users_page.click_add_new_user()
    users_page.fill_user_details("1234", "AutoUser", "", "Abhi1234", "9999999999")
    users_page.select_role("Team Lead")
    users_page.click_submit()
    assert users_page.is_add_user_dialog_visible(), "Dialog should stay open when Email is missing."


def test_create_user_without_password(users_page):
    """4. Create user without Password - dialog should remain open (validation blocks submission)."""
    users_page.click_add_new_user()
    users_page.fill_user_details("1234", "AutoUser", "test@test.com", "", "9999999999")
    users_page.select_role("Team Lead")
    users_page.click_submit()
    assert users_page.is_add_user_dialog_visible(), "Dialog should stay open when Password is missing."


def test_create_user_without_mobile(users_page):
    """5. Create user without Mobile Number - dialog should remain open (validation blocks submission)."""
    users_page.click_add_new_user()
    users_page.fill_user_details("1234", "AutoUser", "test@test.com", "Abhi1234", "")
    users_page.select_role("Team Lead")
    users_page.click_submit()
    assert users_page.is_add_user_dialog_visible(), "Dialog should stay open when Mobile is missing."


def test_create_user_without_role(users_page):
    """6. Create user without Role."""
    users_page.click_add_new_user()
    users_page.fill_user_details("USR123", "AutoUser", "test@test.com", "Abhi1234", "9999999999")
    users_page.click_submit()
    assert False, "Pending Locator Confirmation"


def test_create_user_invalid_email_format(users_page):
    """7. Create user with invalid email format."""
    users_page.click_add_new_user()
    users_page.fill_user_details("USR123", "AutoUser", "invalidemail.com", "Abhi1234", "9999999999")
    users_page.select_role("Team Lead")
    users_page.click_submit()
    assert False, "Pending Locator Confirmation"


def test_create_user_duplicate_user_id(users_page):
    """8. Create user with duplicate User ID."""
    users_page.click_add_new_user()
    users_page.fill_user_details("1234", "AutoUser", "unique@test.com", "Abhi1234", "9999999999")
    users_page.select_role("Team Lead")
    users_page.click_submit()
    assert False, "Pending Locator Confirmation"


def test_create_user_duplicate_email(users_page):
    """9. Create user with duplicate Email."""
    users_page.click_add_new_user()
    users_page.fill_user_details(f"USR_{int(time.time())}", "AutoUser", "Admin@infusive.com", "Abhi1234", "9999999999")
    users_page.select_role("Team Lead")
    users_page.click_submit()
    assert False, "Pending Locator Confirmation"


def test_create_user_invalid_mobile_length(users_page):
    """10. Create user with invalid mobile number length."""
    users_page.click_add_new_user()
    users_page.fill_user_details("USR123", "AutoUser", "test@test.com", "Abhi1234", "123")
    users_page.select_role("Team Lead")
    users_page.click_submit()
    assert False, "Pending Locator Confirmation"
