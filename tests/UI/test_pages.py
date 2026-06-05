import time

import pytest

from pages.pages_page import PagesPage

# Named constant — replace with a value guaranteed to exist in the target environment
SEARCH_KEYWORD = "City"


@pytest.fixture
def pages_page(logged_in_page):
    """Navigate to Pages section after login and return PagesPage."""
    pp = PagesPage(logged_in_page)
    pp.go_to_pages()
    return pp


# ---------------------------------------------------------------------------
# Search Tests
# ---------------------------------------------------------------------------

def test_search_page(pages_page):
    pages_page.search(SEARCH_KEYWORD)
    assert pages_page.is_row_visible(SEARCH_KEYWORD), (
        f"Search result for '{SEARCH_KEYWORD}' not found"
    )


def test_search_no_results(pages_page):
    pages_page.search("xyznonexistent123")
    assert pages_page.has_no_results(), "Search should return no results for a non-existent keyword"


# ---------------------------------------------------------------------------
# Add Page
# ---------------------------------------------------------------------------

def test_add_page(pages_page):
    unique_name = f"AutoTestPage_{int(time.time())}_add"

    pages_page.click_add_new()
    pages_page.fill_page_form(name=unique_name, label=unique_name, url=unique_name.lower())
    pages_page.click_save()

    assert pages_page.is_row_visible(unique_name), (
        f"Page '{unique_name}' not found after creation"
    )

    # Cleanup
    row_index = pages_page.get_row_index(unique_name)
    pages_page.click_delete_for_row(row_index)
    pages_page.confirm_delete()


# ---------------------------------------------------------------------------
# Edit Page
# ---------------------------------------------------------------------------

def test_edit_page(pages_page):
    unique_name = f"AutoTestPage_{int(time.time())}_edit"
    updated_name = f"{unique_name}_Updated"

    # Setup: create a page to edit
    pages_page.click_add_new()
    pages_page.fill_page_form(name=unique_name, label=unique_name, url=unique_name.lower())
    pages_page.click_save()

    # Edit
    row_index = pages_page.get_row_index(unique_name)
    pages_page.click_edit_for_row(row_index)
    pages_page.update_page_name(updated_name)
    pages_page.click_update()

    assert pages_page.is_row_visible(updated_name), (
        f"Page '{updated_name}' not found after update"
    )

    # Cleanup
    row_index = pages_page.get_row_index(updated_name)
    pages_page.click_delete_for_row(row_index)
    pages_page.confirm_delete()


# ---------------------------------------------------------------------------
# Delete Page
# ---------------------------------------------------------------------------

def test_delete_page(pages_page):
    unique_name = f"AutoTestPage_{int(time.time())}_del"

    # Setup: create a page to delete
    pages_page.click_add_new()
    pages_page.fill_page_form(name=unique_name, label=unique_name, url=unique_name.lower())
    pages_page.click_save()

    # Delete
    row_index = pages_page.get_row_index(unique_name)
    pages_page.click_delete_for_row(row_index)
    assert pages_page.is_delete_popup_visible(), "Delete confirmation popup not visible"
    pages_page.confirm_delete()

    assert not pages_page.is_row_visible(unique_name), (
        f"Page '{unique_name}' still visible after deletion"
    )
