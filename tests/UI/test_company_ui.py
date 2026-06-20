import pytest
import logging
from pages.company_page import CompanyPage

# Configure logging
logger = logging.getLogger(__name__)

@pytest.fixture
def company_page(logged_in_page):
    logger.info("Initializing CompanyPage POM...")
    cp = CompanyPage(logged_in_page)
    logger.info("Navigating to Company page...")
    cp.go_to_company()
    return cp

@pytest.mark.login_as("PreSales2@mailinator.com")
def test_add_company_button_ui_styles(company_page):
    logger.info("--- STARTING: TEST ADD COMPANY BUTTON UI STYLES ---")
    
    # Get the "Add New Company" button locator
    btn = company_page.get_add_company_button()
    btn.wait_for(state="visible", timeout=10000)
    
    logger.info("Step 1: Retrieving bounding box dimensions (width, height)...")
    box = company_page.get_element_dimensions(btn)
    logger.info(f"Button Dimensions: Width = {box['width']}px, Height = {box['height']}px")
    
    # Assert dimensions are within a reasonable range for a standard desktop action button
    assert 100 <= box['width'] <= 350, f"Unexpected button width: {box['width']}px"
    assert 25 <= box['height'] <= 75, f"Unexpected button height: {box['height']}px"
    
    logger.info("Step 2: Retrieving computed CSS styling properties (colors, cursor, fonts)...")
    bg_color = company_page.get_element_css_property(btn, "background-color")
    text_color = company_page.get_element_css_property(btn, "color")
    cursor = company_page.get_element_css_property(btn, "cursor")
    font_weight = company_page.get_element_css_property(btn, "font-weight")
    
    logger.info(f"Button CSS Styles: background-color = '{bg_color}', color = '{text_color}', cursor = '{cursor}', font-weight = '{font_weight}'")
    
    # Assert background color is defined (usually rgb or rgba or hex)
    assert bg_color and bg_color != "rgba(0, 0, 0, 0)", "Button background-color should not be transparent"
    # Assert pointer cursor for interactive buttons
    assert cursor == "pointer", f"Expected pointer cursor, got '{cursor}'"
    # Font weight assertions (bold or numeric >= 500)
    assert font_weight in ["500", "600", "700", "bold"], f"Expected a bold/medium font weight, got '{font_weight}'"
    
    logger.info("TEST ADD COMPANY BUTTON UI STYLES verified successfully!")

@pytest.mark.login_as("PreSales2@mailinator.com")
def test_company_page_header_ui_styles(company_page):
    logger.info("--- STARTING: TEST COMPANY PAGE HEADER UI STYLES ---")
    
    # Let's locate the page heading. On the company page, it should have a heading containing 'Company' or similar.
    # Let's look for a level-1/2 heading or standard header text.
    header_loc = company_page.page.get_by_role("heading", name="Company")
    if header_loc.count() == 0:
        header_loc = company_page.page.get_by_text("Company List").first
    if header_loc.count() == 0:
        header_loc = company_page.page.locator("h2, h3, h1").first
        
    header_loc.wait_for(state="visible", timeout=10000)
    
    logger.info("Step 1: Retrieving header layout dimensions...")
    box = company_page.get_element_dimensions(header_loc)
    logger.info(f"Header Dimensions: Width = {box['width']}px, Height = {box['height']}px")
    assert box['width'] > 0, "Header width should be greater than 0"
    assert box['height'] > 0, "Header height should be greater than 0"
    
    logger.info("Step 2: Retrieving header text styles...")
    font_size = company_page.get_element_css_property(header_loc, "font-size")
    font_family = company_page.get_element_css_property(header_loc, "font-family")
    text_color = company_page.get_element_css_property(header_loc, "color")
    
    logger.info(f"Header CSS Styles: font-size = '{font_size}', color = '{text_color}', font-family = '{font_family}'")
    
    # Typically font size for headers is at least 16px/1rem
    # Parse size numeric value
    size_px = float(font_size.replace("px", "").strip()) if "px" in font_size else 16.0
    assert size_px >= 14.0, f"Expected header font size to be at least 14px, got '{font_size}'"
    
    logger.info("TEST COMPANY PAGE HEADER UI STYLES verified successfully!")

@pytest.mark.login_as("PreSales2@mailinator.com")
def test_invalid_fields_highlight_ui_styles(company_page):
    logger.info("--- STARTING: TEST INVALID FIELDS HIGHLIGHT UI STYLES ---")
    
    logger.info("Step 1: Opening Add New Company form...")
    company_page.click_add_new_company()
    
    # Locate the Company Name input field
    name_input = company_page.page.locator("input[name='companyName']")
    name_input.wait_for(state="visible", timeout=10000)
    
    logger.info("Step 2: Retrieving normal/initial style of Company Name input border...")
    initial_border = company_page.get_element_css_property(name_input, "border-color")
    logger.info(f"Initial input border-color: '{initial_border}'")
    
    logger.info("Step 3: Clicking Save with empty required fields to trigger validation error...")
    company_page.page.get_by_role("button", name="Save").click()
    
    # Wait for the validation state to trigger
    company_page.page.wait_for_timeout(1000)
    
    logger.info("Step 4: Retrieving style of Company Name input border after error trigger...")
    error_border = company_page.get_element_css_property(name_input, "border-color")
    aria_invalid = name_input.get_attribute("aria-invalid")
    
    logger.info(f"Error input border-color: '{error_border}', aria-invalid = '{aria_invalid}'")
    
    # Cleanup page state to avoid pollution
    company_page.navigate_to_company_list_if_needed()
    
    # Assert validation indicators
    assert aria_invalid == "true", "Expected input to have aria-invalid='true' attribute"
    
    # Typically, error border colors contain a red tone (high red value in rgb/rgba, or has hex matching red)
    # Check if border changed, and check if it contains red components or is different from initial
    assert error_border != initial_border, "Border color should change to highlight the error state"
    
    logger.info("TEST INVALID FIELDS HIGHLIGHT UI STYLES verified successfully!")
