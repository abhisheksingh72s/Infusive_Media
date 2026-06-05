import time
import random
import pytest

from pages.users_page import UsersPage

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
    # Dynamic Test Data Generation
    timestamp = int(time.time())
    user_id = "134"
    name = f"AutoUser_{timestamp}"
    email = f"autouser_{timestamp}@test.com"
    password = "Abhi1234"
    mobile = f"9{random.randint(100000000, 999999999)}"
    role = "Team Lead"

    # Action
    users_page.click_add_new_user()
    users_page.fill_user_details(user_id, name, email, password, mobile)
    users_page.select_role(role)
    users_page.click_submit()

    # Assertions
    assert users_page.is_notification_visible(), "Success notification was not displayed."
    
    # Optional wait to allow backend to persist and grid to reload
    users_page.page.wait_for_timeout(1000)
    try:
        assert users_page.is_user_row_visible(email), f"Newly created user '{email}' not found in the grid."
    except AssertionError:
        users_page.page.screenshot(path="screenshots/test_create_user_grid_failure.png")
        raise


def test_search_user(users_page):
    """7. Verify user search after creation."""
    # Note: We rely on a previously created user or a known static user for reliable standalone searching
    # In a fully stateless suite, you would create a user first within this test, then search for it.
    
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

    # Search for the created user
    users_page.search_user(email)
    assert users_page.is_user_row_visible(email), f"Search result for '{email}' not found."


# ---------------------------------------------------------------------------
# Negative Test Scenarios
# ---------------------------------------------------------------------------

def test_create_user_without_user_id(users_page):
    """1. Create user without User ID - dialog should remain open (validation blocks submission)."""
    users_page.click_add_new_user()
    dialog = users_page.page.get_by_role("dialog", name="Add New User")
    dialog.get_by_label("User Id", exact=False).fill("")
    dialog.get_by_role("button", name="Submit").click()
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
    # Skipping role selection intentionally
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
    # Assuming '1234' is a duplicate User ID as per the codegen script
    users_page.click_add_new_user()
    users_page.fill_user_details("1234", "AutoUser", "unique@test.com", "Abhi1234", "9999999999")
    users_page.select_role("Team Lead")
    users_page.click_submit()
    assert False, "Pending Locator Confirmation"


def test_create_user_duplicate_email(users_page):
    """9. Create user with duplicate Email."""
    # Assuming 'shreya@' is a duplicate prefix or we mock a known duplicate
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


# ---------------------------------------------------------------------------
# DEBUG: Inspect dialog DOM - REMOVE AFTER LOCATORS ARE CONFIRMED
# ---------------------------------------------------------------------------

def test_find_valid_id(users_page):
    """Temporary test to find an ID that is valid but not registered."""
    users_page.click_add_new_user()
    for i in range(135, 200):
        users_page.page.get_by_placeholder("Enter User Id").fill(str(i))
        users_page.page.get_by_role("button", name="Submit").first.click()
        try:
            users_page.page.wait_for_timeout(1500)
            text = users_page.page.locator("li[role='status'] div").first.inner_text()
            print(f"ID {i}: {text}")
            if "already exists" in text:
                pass
            elif "found for" in text:
                # It's valid and we can go to step 2!
                assert False, f"FOUND VALID UNREGISTERED ID: {i}"
        except Exception:
            pass

def test_debug_dump_dialog_dom(users_page):
    """Temporary: reveal step-2 form fields after submitting User Id."""
    users_page.click_add_new_user()
    users_page.page.wait_for_timeout(1000)

    # --- Step 1: fill User Id and click Submit to advance to step 2 ---
    dialog = users_page.page.get_by_role("dialog", name="Add New User")
    dialog.locator("input[name='userId']").fill("1234")
    users_page.page.get_by_role("button", name="Submit").click()
    # Wait for step 2 to render
    users_page.page.wait_for_timeout(3000)

    inputs = users_page.page.evaluate("""
        () => {
            const dialog = document.querySelector('[role="dialog"]');
            if (!dialog) return [{error: 'No dialog found'}];
            const els = dialog.querySelectorAll('input, textarea, select');
            return Array.from(els).map((el, i) => ({
                index: i,
                tag: el.tagName,
                type: el.type,
                name: el.name,
                id: el.id,
                placeholder: el.placeholder,
                ariaLabel: el.getAttribute('aria-label'),
                ariaLabelledBy: el.getAttribute('aria-labelledby'),
            }));
        }
    """)

    labels = users_page.page.evaluate("""
        () => {
            const dialog = document.querySelector('[role="dialog"]');
            if (!dialog) return [{error: 'No dialog found'}];
            return Array.from(dialog.querySelectorAll('label')).map((el, i) => ({
                index: i,
                text: el.textContent.trim(),
                forAttr: el.getAttribute('for'),
            }));
        }
    """)

    dialog_text = users_page.page.evaluate("""
        () => {
            const d = document.querySelector('[role="dialog"]');
            return d ? d.innerText : 'No dialog';
        }
    """)

    users_page.page.screenshot(path="screenshots/debug_dialog_step2.png")

    assert False, (
        f"\n\n=== STEP 2 DIALOG TEXT ===\n{dialog_text}"
        f"\n\n=== INPUTS ({len(inputs)}) ===\n" + "\n".join(str(i) for i in inputs) +
        f"\n\n=== LABELS ({len(labels)}) ===\n" + "\n".join(str(l) for l in labels)
    )

