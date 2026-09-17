import os
import json
from pathlib import Path

# Helper to load locators from the generated locators.json file

def get_locator(name: str):
    """Return the locator dict for a given element name.
    The locator dict has keys: "type" ("css" or "xpath") and "selector".
    """
    locators_path = Path(__file__).parent.parent / "locators.json"
    if not locators_path.is_file():
        raise FileNotFoundError(f"locators.json not found at {locators_path}")
    with open(locators_path, "r", encoding="utf-8") as f:
        locators = json.load(f)
    if name not in locators:
        raise KeyError(f"Locator '{name}' not defined in locators.json")
    return locators[name]
