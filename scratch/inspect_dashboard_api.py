import os
import json
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)

EMAIL = os.getenv("EMAIL", "Admin@infusive.com")
PASSWORD = os.getenv("PASSWORD", "123456")
BASE_URL = os.getenv("BASE_URL", "https://infusive-front.jobvritta.com/login")

def main():
    print(f"Connecting to UI at {BASE_URL} as {EMAIL}...")
    captured_api_responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Listen to response events
        def handle_response(response):
            if "/api/" in response.url.lower():
                try:
                    data = response.json()
                    captured_api_responses.append({
                        "url": response.url,
                        "status": response.status,
                        "data": data
                    })
                    print(f"\n[API RESP] {response.status} {response.url}")
                    print(f"Data snippet: {json.dumps(data)[:300]}...")
                except Exception:
                    print(f"\n[API RESP (non-json)] {response.status} {response.url}")

        page.on("response", handle_response)

        # Login
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.get_by_role("textbox", name="Email").fill(EMAIL)
        page.get_by_role("textbox", name="Password").fill(PASSWORD)
        page.get_by_role("button", name="Login").click()
        page.wait_for_url("**/dashboard**", timeout=20000)
        page.wait_for_timeout(5000)

        # Print all captured API calls
        print("\n" + "="*80)
        print(f"Total API responses captured on Dashboard: {len(captured_api_responses)}")
        print("="*80)
        for idx, res in enumerate(captured_api_responses, 1):
            print(f"\n--- API Response #{idx} ---")
            print(f"URL: {res['url']}")
            print(f"Payload JSON: {json.dumps(res['data'], indent=2)}")

        browser.close()

if __name__ == "__main__":
    main()
