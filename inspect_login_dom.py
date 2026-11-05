import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

BASE_URL = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)
    print("Page Title:", page.title())
    print("Inputs found:")
    inputs = page.locator("input").all()
    for i, inp in enumerate(inputs):
        print(f"Input {i}: name='{inp.get_attribute('name')}', id='{inp.get_attribute('id')}', placeholder='{inp.get_attribute('placeholder')}', type='{inp.get_attribute('type')}', aria-label='{inp.get_attribute('aria-label')}'")
    browser.close()
