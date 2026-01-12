"""E2E tests for chart visualizations."""

from playwright.sync_api import Page, expect


class TestChartRendering:
    """Tests for chart rendering on dashboard."""

    def test_chart_section_renders_for_new_user(self, authenticated_page: Page, base_url: str):
        """Chart section should render even for new users without data."""
        authenticated_page.goto(f"{base_url}/budget/")

        # Visualization section should be visible
        expect(authenticated_page.locator("text=Visualisering")).to_be_visible()

        # Income/Expenses chart should always render (shows 0 values)
        expect(authenticated_page.locator("#chart-income-expenses")).to_be_visible()

        # Empty user shows "Ingen data" for category and top expenses charts
        expect(authenticated_page.locator("text=Ingen data").first).to_be_visible()

    def test_visualisering_section_visible(self, authenticated_page: Page, base_url: str):
        """Visualisering section header should be visible."""
        authenticated_page.goto(f"{base_url}/budget/")

        expect(authenticated_page.locator("text=Visualisering")).to_be_visible()


class TestChartResponsive:
    """Tests for responsive chart behavior."""

    def test_chart_section_renders_on_mobile(self, page: Page, base_url: str):
        """Chart section should render properly on mobile viewport."""
        # Use demo mode to have actual chart data
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")

        page.set_viewport_size({"width": 375, "height": 667})
        page.reload()

        # Charts should be visible with demo data
        expect(page.locator("#chart-categories")).to_be_visible()
        expect(page.locator("#chart-income-expenses")).to_be_visible()
        expect(page.locator("#chart-top-expenses")).to_be_visible()

    def test_chart_section_renders_on_small_viewport(self, page: Page, base_url: str):
        """Chart section should render properly on smallest mobile viewport."""
        # Use demo mode to have actual chart data
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")

        page.set_viewport_size({"width": 320, "height": 568})
        page.reload()

        # Charts should still be visible
        expect(page.locator("#chart-categories")).to_be_visible()


class TestDemoCharts:
    """Tests for charts in demo mode."""

    def test_demo_charts_show_data(self, page: Page, base_url: str):
        """Demo mode should display charts with demo data."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")

        # All chart canvases should be visible
        expect(page.locator("#chart-categories")).to_be_visible()
        expect(page.locator("#chart-income-expenses")).to_be_visible()
        expect(page.locator("#chart-top-expenses")).to_be_visible()

    def test_demo_charts_have_content(self, page: Page, base_url: str):
        """Demo mode charts should have actual rendered content."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")

        # Wait for charts to render (Chart.js needs a moment)
        page.wait_for_timeout(1000)

        # Canvases should have non-zero dimensions (indicating content)
        canvas = page.locator("#chart-categories")
        box = canvas.bounding_box()
        assert box is not None
        assert box["width"] > 0
        assert box["height"] > 0


class TestChartLabels:
    """Tests for chart section labels."""

    def test_income_expenses_label(self, authenticated_page: Page, base_url: str):
        """Income vs Expenses chart should have correct label."""
        authenticated_page.goto(f"{base_url}/budget/")

        expect(authenticated_page.locator("text=Indkomst vs Udgifter")).to_be_visible()

    def test_category_chart_label(self, authenticated_page: Page, base_url: str):
        """Category chart should have correct label."""
        authenticated_page.goto(f"{base_url}/budget/")

        expect(authenticated_page.locator("h3:has-text('Udgifter per kategori')")).to_be_visible()

    def test_top_expenses_label(self, authenticated_page: Page, base_url: str):
        """Top expenses chart should have correct label."""
        authenticated_page.goto(f"{base_url}/budget/")

        expect(authenticated_page.locator("text=Top 5 udgifter")).to_be_visible()
