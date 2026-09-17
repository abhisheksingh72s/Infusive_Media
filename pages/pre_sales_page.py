import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utilities.locator_fetcher import get_locator

class PreSalesPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def login(self):
        # credentials from .env via environment variables (already loaded by pytest)
        username = os.getenv('USER_01_EMAIL') or os.getenv('USER_11_EMAIL')
        password = os.getenv('USER_01_PASSWORD') or os.getenv('USER_11_PASSWORD')
        # locate elements using fetched locators
        loc_username = get_locator('login_username')
        loc_password = get_locator('login_password')
        loc_login_btn = get_locator('login_button')

        self._type(loc_username, username)
        self._type(loc_password, password)
        self._click(loc_login_btn)
        # wait for dashboard to load (e.g., lead module visible)
        lead_module_locator = get_locator('lead_module')
        self.wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR if lead_module_locator['type'] == 'css' else By.XPATH,
            lead_module_locator['selector']
        )))
        return self

    def open_company_module(self):
        locator = get_locator('company_module')
        self._click(locator)
        return self

    def click_add_new_company(self):
        locator = get_locator('add_new_company_button')
        self._click(locator)
        return self

    def click_add_quick_lead(self):
        locator = get_locator('add_quick_lead_option')
        self._click(locator)
        return self

    def fill_quick_lead_form(self, company_name, contact_person, mobile, email):
        fields = {
            'company_name': company_name,
            'contact_person': contact_person,
            'mobile': mobile,
            'email': email,
        }
        for key, value in fields.items():
            loc = get_locator(key)
            self._type(loc, value)
        # submit
        self._click(get_locator('submit_button'))
        return self

    def open_lead_module(self):
        self._click(get_locator('lead_module'))
        return self

    def open_my_leads(self):
        self._click(get_locator('my_leads_submodule'))
        return self

    def search_lead(self, query):
        self._type(get_locator('search_box'), query)
        # wait for results
        time.sleep(2)
        return self

    def logout(self):
        self._click(get_locator('profile_menu'))
        self._click(get_locator('logout_button'))
        return self

    # internal helpers
    def _click(self, locator):
        by = By.CSS_SELECTOR if locator['type'] == 'css' else By.XPATH
        elem = self.wait.until(EC.element_to_be_clickable((by, locator['selector'])))
        elem.click()
        return self

    def _type(self, locator, text):
        by = By.CSS_SELECTOR if locator['type'] == 'css' else By.XPATH
        elem = self.wait.until(EC.visibility_of_element_located((by, locator['selector'])))
        elem.clear()
        elem.send_keys(text)
        return self
