import re
from typing import Any, Dict, List


class DashboardPage:
    def __init__(self, page):
        self.page = page
        
        # Monthly Chart (Chart 1) Locators
        self.chart_container = self.page.locator(".recharts-responsive-container").first
        self.chart_wrapper = self.chart_container.locator(".recharts-wrapper")
        self.chart_svg = self.chart_container.locator("svg.recharts-surface")
        
        self.x_axis_ticks = self.chart_container.locator(".recharts-xAxis .recharts-cartesian-axis-tick-value, .recharts-xAxis text")
        self.y_axis_ticks = self.chart_container.locator(".recharts-yAxis .recharts-cartesian-axis-tick-value, .recharts-yAxis text")
        
        self.grid_lines = self.chart_container.locator(".recharts-cartesian-grid line")
        self.bar_rectangles = self.chart_container.locator(".recharts-bar-rectangle")
        self.bar_paths = self.chart_container.locator(".recharts-bar-rectangle path, .recharts-rectangle")
        
        self.tooltip_wrapper = self.chart_container.locator(".recharts-tooltip-wrapper")
        self.tooltip_content = self.chart_container.locator(".recharts-default-tooltip")
        self.tooltip_label = self.chart_container.locator(".recharts-tooltip-label")

        # Lead Generation Chart (Chart 2) Locators
        self.lead_gen_chart_container = self.page.locator(".recharts-responsive-container").nth(1)

        # Table Locators
        self.table_locator = self.page.locator("table").first

    def go_to_dashboard(self):
        """Navigate to Dashboard page and wait for load state."""
        if "/dashboard" not in self.page.url:
            dashboard_link = self.page.get_by_role("link", name=re.compile("Dashboard", re.IGNORECASE))
            if dashboard_link.is_visible():
                dashboard_link.click()
            else:
                base_url = self.page.url.split("/admin")[0] if "/admin" in self.page.url else self.page.url
                self.page.goto(f"{base_url.rstrip('/')}/dashboard")
        self.page.wait_for_load_state("networkidle")

    # ---------------------------------------------------------------------------
    # 1. Summary Cards Extraction
    # ---------------------------------------------------------------------------

    def get_all_summary_cards(self) -> Dict[str, int]:
        """Extract title and numerical count for all summary stat cards on UI."""
        body_text = self.page.inner_text("body")
        cards_data = {}
        
        known_titles = [
            "TOTAL LEADS", "ASSIGNED", "CONTACTED", "WON",
            "LOST", "DUPLICATE LEADS", "DUPLICATE CONVERTED"
        ]

        lines = [line.strip() for line in body_text.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            for title in known_titles:
                if line.upper() == title:
                    # Next line usually contains the stat count
                    if idx + 1 < len(lines):
                        val_str = lines[idx + 1]
                        try:
                            cards_data[title] = int(val_str)
                        except ValueError:
                            cards_data[title] = 0

        return cards_data

    # ---------------------------------------------------------------------------
    # 2. Monthly Bar Chart (Lead Trends)
    # ---------------------------------------------------------------------------

    def is_chart_visible(self) -> bool:
        """Check if the Recharts container or SVG is visible."""
        return self.chart_container.is_visible() or self.chart_svg.is_visible()

    def get_x_axis_labels(self) -> List[str]:
        """Extract text content of all X-axis ticks (months) for Monthly Chart."""
        count = self.x_axis_ticks.count()
        labels = []
        for i in range(count):
            text = self.x_axis_ticks.nth(i).text_content()
            if text:
                labels.append(text.strip())
        return labels

    def get_y_axis_labels(self) -> List[str]:
        """Extract text content of all Y-axis ticks (scale values) for Monthly Chart."""
        count = self.y_axis_ticks.count()
        labels = []
        for i in range(count):
            text = self.y_axis_ticks.nth(i).text_content()
            if text:
                labels.append(text.strip())
        return labels

    def get_bar_count(self) -> int:
        """Return the count of bar rectangle elements rendered in the chart."""
        return self.bar_rectangles.count()

    def get_active_bar_colors(self) -> List[str]:
        """Retrieve fill colors of rendered bar paths."""
        count = self.bar_paths.count()
        colors = []
        for i in range(count):
            fill = self.bar_paths.nth(i).get_attribute("fill")
            if fill:
                colors.append(fill)
        return colors

    def hover_bar_by_index(self, index: int):
        """Hover over a specific bar rectangle by index."""
        if index < self.bar_rectangles.count():
            bar = self.bar_rectangles.nth(index)
            bar.hover(force=True)

    def hover_bar_by_month(self, month_name: str):
        """Hover over the bar corresponding to a specific month label."""
        labels = self.get_x_axis_labels()
        if month_name in labels:
            idx = labels.index(month_name)
            self.hover_bar_by_index(idx)

    def is_tooltip_visible(self) -> bool:
        """Check if the chart tooltip wrapper is present or visible."""
        return self.tooltip_wrapper.is_visible() or self.tooltip_content.is_visible()

    def get_tooltip_text(self) -> str:
        """Get the text content of the visible tooltip."""
        if self.tooltip_label.is_visible():
            return self.tooltip_label.text_content().strip()
        if self.tooltip_content.is_visible():
            return self.tooltip_content.text_content().strip()
        return ""

    # ---------------------------------------------------------------------------
    # 3. Lead Generation Chart & Weekly Table
    # ---------------------------------------------------------------------------

    def get_lead_gen_user_ticks(self) -> List[str]:
        """Extract user names from X-axis of Chart 2 (Lead Generation Chart)."""
        if self.lead_gen_chart_container.is_visible():
            ticks = self.lead_gen_chart_container.locator(".recharts-xAxis text").all()
            return [t.text_content().strip() for t in ticks if t.text_content().strip()]
        return []

    def get_weekly_breakdown_table(self) -> Dict[str, Any]:
        """Extract table headers and row dicts from the Weekly Breakdown table."""
        if not self.table_locator.is_visible():
            return {"headers": [], "rows": []}

        headers = [th.text_content().strip() for th in self.table_locator.locator("th").all()]
        rows_data = []

        for row in self.table_locator.locator("tbody tr").all():
            cells = [td.text_content().strip() for td in row.locator("td").all()]
            if len(cells) >= len(headers):
                row_dict = dict(zip(headers, cells))
                rows_data.append(row_dict)

        return {"headers": headers, "rows": rows_data}

    # ---------------------------------------------------------------------------
    # 4. Today's Activities Extraction
    # ---------------------------------------------------------------------------

    def get_todays_activities_status(self) -> Dict[str, str]:
        """Extract status text for Today's Meetings and Reminders."""
        body_text = self.page.inner_text("body")
        return {
            "meetings_empty": "No meetings scheduled for today" in body_text,
            "reminders_empty": "No follow-ups scheduled for today" in body_text
        }
