import time

import pytest

from pages.admin_role_page import AdminRolePage


@pytest.fixture
def role_page(logged_in_page):
    """Navigate to Admin Controller after login and return AdminRolePage."""
    rp = AdminRolePage(logged_in_page)
    rp.go_to_admin_controller()
    return rp


# ---------------------------------------------------------------------------
# Search Tests
# ---------------------------------------------------------------------------

def test_search_role(role_page):
    role_page.search("Admin")
    assert role_page.is_role_row_visible("Admin"), "Search result for 'Admin' not found"


def test_search_role_no_results(role_page):
    role_page.search("xyznonexistent123")
    assert role_page.has_no_results(), "Search should return no results for a non-existent keyword"


# ---------------------------------------------------------------------------
# Add Role
# ---------------------------------------------------------------------------

def test_add_role(role_page):
    unique_name = f"Role{int(time.time()) % 100000}_add"

    role_page.click_add_new_role()
    role_page.fill_role_form(name=unique_name, description="test description")
    role_page.click_submit()

    assert role_page.is_role_row_visible(unique_name), (
        f"Role '{unique_name}' not found after creation"
    )

    # Cleanup: remove the created role so tests remain stateless
    role_page.click_delete_for_row_by_name(unique_name)
    role_page.confirm_delete()


# ---------------------------------------------------------------------------
# Edit Role
# ---------------------------------------------------------------------------

def test_edit_role(role_page):
    unique_name = f"Role{int(time.time()) % 100000}_edit"
    updated_name = f"{unique_name}Up"

    # Setup: create a role to edit
    role_page.click_add_new_role()
    role_page.fill_role_form(name=unique_name, description="test description")
    role_page.click_submit()

    # Edit
    role_page.click_edit_for_role(unique_name)
    role_page.update_role_name(updated_name)
    role_page.click_update()

    assert role_page.is_role_row_visible(updated_name), (
        f"Role '{updated_name}' not found after update"
    )

    # Cleanup
    role_page.click_delete_for_row_by_name(updated_name)
    role_page.confirm_delete()


# ---------------------------------------------------------------------------
# Delete Role
# ---------------------------------------------------------------------------

def test_delete_role(role_page):
    unique_name = f"Role{int(time.time()) % 100000}_del"

    # Setup: create a role to delete
    role_page.click_add_new_role()
    role_page.fill_role_form(name=unique_name, description="test description")
    role_page.click_submit()

    # Delete
    role_page.click_delete_for_row_by_name(unique_name)
    assert role_page.is_confirm_delete_visible(), "Delete confirmation popup not visible"
    role_page.confirm_delete()

    assert not role_page.is_role_row_visible(unique_name), (
        f"Role '{unique_name}' still visible after deletion"
    )
