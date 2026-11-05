import pytest
from pages.dashboard_page import DashboardPage

DASHBOARD_HTML_SNIPPET = """
<!DOCTYPE html>
<html>
<head>
<style>
.css-ph6oyx { width: 554px; height: 294px; }
</style>
</head>
<body>
<div class="css-ph6oyx"><div class="recharts-responsive-container" style="width: 100%; height: 100%; min-width: 0px;"><div class="recharts-wrapper" style="position: relative; cursor: default; width: 100%; height: 100%; max-height: 294px; max-width: 554px;"><svg class="recharts-surface" width="554" height="294" viewBox="0 0 554 294" style="width: 100%; height: 100%;"><title></title><desc></desc><defs><clipPath id="recharts1-clip"><rect x="40" y="10" height="254" width="504"></rect></clipPath></defs><g class="recharts-cartesian-grid"><g class="recharts-cartesian-grid-horizontal"><line stroke-dasharray="4 4" stroke="#E5E7EB" fill="none" x="40" y="10" width="504" height="254" x1="40" y1="264" x2="544" y2="264"></line><line stroke-dasharray="4 4" stroke="#E5E7EB" fill="none" x="40" y="10" width="504" height="254" x1="40" y1="200.5" x2="544" y2="200.5"></line><line stroke-dasharray="4 4" stroke="#E5E7EB" fill="none" x="40" y="10" width="504" height="254" x1="40" y1="137" x2="544" y2="137"></line><line stroke-dasharray="4 4" stroke="#E5E7EB" fill="none" x="40" y="10" width="504" height="254" x1="40" y1="73.5" x2="544" y2="73.5"></line><line stroke-dasharray="4 4" stroke="#E5E7EB" fill="none" x="40" y="10" width="504" height="254" x1="40" y1="10" x2="544" y2="10"></line></g></g><g class="recharts-layer recharts-cartesian-axis recharts-xAxis xAxis"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-line" stroke="#666" fill="none" x1="40" y1="264" x2="544" y2="264"></line><g class="recharts-cartesian-axis-ticks"><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="61" y1="270" x2="61" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="61" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="61" dy="0.71em">Jan</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="103" y1="270" x2="103" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="103" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="103" dy="0.71em">Feb</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="145" y1="270" x2="145" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="145" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="145" dy="0.71em">Mar</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="187" y1="270" x2="187" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="187" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="187" dy="0.71em">Apr</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="229" y1="270" x2="229" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="229" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="229" dy="0.71em">May</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="271" y1="270" x2="271" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="271" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="271" dy="0.71em">Jun</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="313" y1="270" x2="313" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="313" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="313" dy="0.71em">Jul</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="355" y1="270" x2="355" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="355" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="355" dy="0.71em">Aug</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="397" y1="270" x2="397" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="397" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="397" dy="0.71em">Sep</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="439" y1="270" x2="439" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="439" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="439" dy="0.71em">Oct</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="481" y1="270" x2="481" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="481" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="481" dy="0.71em">Nov</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="bottom" width="504" height="30" x="40" y="264" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="523" y1="270" x2="523" y2="264"></line><text orientation="bottom" width="504" height="30" stroke="none" font-size="12" font-weight="500" x="523" y="272" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="middle" fill="#9CA3AF"><tspan x="523" dy="0.71em">Dec</tspan></text></g></g></g><g class="recharts-layer recharts-cartesian-axis recharts-yAxis yAxis"><line orientation="left" width="60" height="254" x="-20" y="10" class="recharts-cartesian-axis-line" stroke="#666" fill="none" x1="40" y1="10" x2="40" y2="264"></line><g class="recharts-cartesian-axis-ticks"><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="left" width="60" height="254" x="-20" y="10" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="34" y1="264" x2="40" y2="264"></line><text orientation="left" width="60" height="254" stroke="none" font-size="12" font-weight="500" x="32" y="264" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="end" fill="#9CA3AF"><tspan x="32" dy="0.355em">0</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="left" width="60" height="254" x="-20" y="10" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="34" y1="200.5" x2="40" y2="200.5"></line><text orientation="left" width="60" height="254" stroke="none" font-size="12" font-weight="500" x="32" y="200.5" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="end" fill="#9CA3AF"><tspan x="32" dy="0.355em">3</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="left" width="60" height="254" x="-20" y="10" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="34" y1="137" x2="40" y2="137"></line><text orientation="left" width="60" height="254" stroke="none" font-size="12" font-weight="500" x="32" y="137" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="end" fill="#9CA3AF"><tspan x="32" dy="0.355em">6</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="left" width="60" height="254" x="-20" y="10" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="34" y1="73.5" x2="40" y2="73.5"></line><text orientation="left" width="60" height="254" stroke="none" font-size="12" font-weight="500" x="32" y="73.5" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="end" fill="#9CA3AF"><tspan x="32" dy="0.355em">9</tspan></text></g><g class="recharts-layer recharts-cartesian-axis-tick"><line orientation="left" width="60" height="254" x="-20" y="10" class="recharts-cartesian-axis-tick-line" stroke="#666" fill="none" x1="34" y1="10" x2="40" y2="10"></line><text orientation="left" width="60" height="254" stroke="none" font-size="12" font-weight="500" x="32" y="10" class="recharts-text recharts-cartesian-axis-tick-value" text-anchor="end" fill="#9CA3AF"><tspan x="32" dy="0.355em">12</tspan></text></g></g></g><g class="recharts-layer recharts-bar"><g class="recharts-layer recharts-bar-rectangles"><g class="recharts-layer"><g class="recharts-layer recharts-bar-rectangle"></g><g class="recharts-layer recharts-bar-rectangle"></g><g class="recharts-layer recharts-bar-rectangle"></g><g class="recharts-layer recharts-bar-rectangle"></g><g class="recharts-layer recharts-bar-rectangle"></g><g class="recharts-layer recharts-bar-rectangle"></g><g class="recharts-layer recharts-bar-rectangle"></g><g class="recharts-layer recharts-bar-rectangle"></g><g class="recharts-layer recharts-bar-rectangle"><path x="388" y="73.5" width="18" height="190.5" radius="4,4,0,0" fill="#4346DB" class="recharts-rectangle" d="M388,77.5A 4,4,0,0,1,392,73.5L 402,73.5A 4,4,0,0,1,406,77.5L 406,264L 388,264Z"></path></g><g class="recharts-layer recharts-bar-rectangle"></g><g class="recharts-layer recharts-bar-rectangle"></g><g class="recharts-layer recharts-bar-rectangle"></g></g></g><g class="recharts-layer"></g></g></svg><div tabindex="-1" class="recharts-tooltip-wrapper recharts-tooltip-wrapper-left recharts-tooltip-wrapper-top" style="visibility: visible; pointer-events: none; position: absolute; top: 0px; left: 0px; transform: translate(376.391px, 134px);"><div class="recharts-default-tooltip" style="margin: 0px; padding: 10px; background-color: white; border: 1px solid rgb(234, 236, 240); white-space: nowrap; border-radius: 8px; box-shadow: rgba(0, 0, 0, 0.08) 0px 2px 8px;"><p class="recharts-tooltip-label" style="margin: 0px; color: rgb(74, 85, 104); font-weight: 600;">Sep</p></div></div></div></div></div>
</body>
</html>
"""


@pytest.fixture
def dashboard_page_isolated(page):
    """Render the Dashboard bar chart snippet in a fresh page context."""
    page.set_content(DASHBOARD_HTML_SNIPPET)
    return DashboardPage(page)


# ---------------------------------------------------------------------------
# Isolated DOM Component Tests
# ---------------------------------------------------------------------------

def test_dashboard_chart_rendering_isolated(dashboard_page_isolated):
    """Verify chart container and SVG surface render correctly."""
    dp = dashboard_page_isolated
    assert dp.is_chart_visible(), "Recharts monthly bar chart container should be visible"
    assert dp.get_bar_count() == 12, f"Expected 12 month bar rectangle slots, found {dp.get_bar_count()}"


def test_dashboard_chart_x_axis_months_isolated(dashboard_page_isolated):
    """Verify all 12 month labels exist on the X-axis."""
    dp = dashboard_page_isolated
    expected_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    x_labels = dp.get_x_axis_labels()
    
    for month in expected_months:
        assert month in x_labels, f"Expected month label '{month}' on X-axis, found labels: {x_labels}"


def test_dashboard_chart_y_axis_scale_isolated(dashboard_page_isolated):
    """Verify Y-axis numerical scale ticks."""
    dp = dashboard_page_isolated
    expected_scale = ["0", "3", "6", "9", "12"]
    y_labels = dp.get_y_axis_labels()
    
    for val in expected_scale:
        assert val in y_labels, f"Expected Y-axis scale tick '{val}', found ticks: {y_labels}"


def test_dashboard_chart_bar_rectangles_isolated(dashboard_page_isolated):
    """Verify active bar styling and fill color for September data point."""
    dp = dashboard_page_isolated
    colors = dp.get_active_bar_colors()
    assert "#4346DB" in colors or "rgb(67, 70, 219)" in colors, (
        f"Active September bar should have fill color #4346DB, found colors: {colors}"
    )


def test_dashboard_chart_tooltip_isolated(dashboard_page_isolated):
    """Verify tooltip display label for September data point."""
    dp = dashboard_page_isolated
    tooltip_text = dp.get_tooltip_text()
    assert "Sep" in tooltip_text, f"Tooltip label should contain 'Sep', got '{tooltip_text}'"


# ---------------------------------------------------------------------------
# Live Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.ui
def test_dashboard_chart_rendering_live(logged_in_page):
    """Verify the Recharts monthly bar chart on the live Admin Dashboard."""
    dp = DashboardPage(logged_in_page)
    dp.go_to_dashboard()
    
    assert dp.is_chart_visible(), "Dashboard chart container is not visible on live page"
    labels = dp.get_x_axis_labels()
    assert len(labels) > 0, "X-axis labels should be populated on live chart"
