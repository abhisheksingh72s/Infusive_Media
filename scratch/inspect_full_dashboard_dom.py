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
    dump_data = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Login
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.get_by_role("textbox", name="Email").fill(EMAIL)
        page.get_by_role("textbox", name="Password").fill(PASSWORD)
        page.get_by_role("button", name="Login").click()
        page.wait_for_url("**/dashboard**", timeout=20000)
        page.wait_for_timeout(4000)

        # 1. Page text snippet
        dump_data["body_text"] = page.inner_text("body")[:3000]

        # 2. Cards Extraction
        cards_data = []
        cards = page.locator(".chakra-stat, [class*='stat'], [class*='card'], .css-1kw2596, div[class*='Card']").all()
        for idx, card in enumerate(cards, 1):
            txt = card.inner_text().strip()
            if txt:
                cards_data.append({"index": idx, "text": txt})
        dump_data["cards"] = cards_data

        # 3. Tables Extraction
        tables_data = []
        tables = page.locator("table").all()
        for idx, table in enumerate(tables, 1):
            headers = [th.inner_text().strip() for th in table.locator("th").all()]
            rows = []
            for r in table.locator("tbody tr").all():
                cells = [td.inner_text().strip() for td in r.locator("td").all()]
                rows.append(cells)
            tables_data.append({
                "table_index": idx,
                "headers": headers,
                "rows": rows
            })
        dump_data["tables"] = tables_data

        # 4. Recharts Charts Extraction
        charts_data = []
        charts = page.locator(".recharts-responsive-container").all()
        for idx, chart in enumerate(charts, 1):
            x_ticks = [t.text_content().strip() for t in chart.locator(".recharts-xAxis text").all()]
            y_ticks = [t.text_content().strip() for t in chart.locator(".recharts-yAxis text").all()]
            bar_count = chart.locator(".recharts-bar-rectangle").count()
            charts_data.append({
                "chart_index": idx,
                "x_axis_ticks": x_ticks,
                "y_axis_ticks": y_ticks,
                "bar_count": bar_count
            })
        dump_data["charts"] = charts_data

        browser.close()

    out_file = ROOT_DIR / "scratch" / "dashboard_dom_dump.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dump_data, f, indent=2, ensure_ascii=False)
    print(f"Dashboard DOM dump saved to {out_file}")

if __name__ == "__main__":
    main()
