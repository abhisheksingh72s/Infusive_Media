import json
import os

LOCATORS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'locators.json')

def load_locators():
    """Load locators from locators.json if it exists, otherwise return empty dict."""
    if os.path.exists(LOCATORS_FILE):
        with open(LOCATORS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_locators(locators):
    """Save the locators dict to locators.json with pretty formatting."""
    os.makedirs(os.path.dirname(LOCATORS_FILE), exist_ok=True)
    with open(LOCATORS_FILE, 'w', encoding='utf-8') as f:
        json.dump(locators, f, indent=2, ensure_ascii=False)
