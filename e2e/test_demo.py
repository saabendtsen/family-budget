"""E2E tests for demo mode functionality."""

from playwright.sync_api import Page, expect


class TestDemoModeAccess:
    """Tests for accessing demo mode."""

    def test_demo_link_visible_on_login(self, page: Page, base_url: str):
        """Demo link should be visible on login page."""
        page.goto(f"{base_url}/budget/login")
        expect(page.get_by_text("Prøv demo")).to_be_visible()

    def test_demo_mode_sets_cookie(self, page: Page, base_url: str):
        """Demo mode should set a demo session cookie."""
        page.goto(f"{base_url}/budget/demo")
        cookies = page.context.cookies()
        budget_cookie = next((c for c in cookies if c["name"] == "budget_session"), None)
        assert budget_cookie is not None
        assert budget_cookie["value"] == "demo"


class TestDemoDashboard:
    """Tests for demo dashboard content."""

    def test_demo_banner_visible(self, page: Page, base_url: str):
        """Demo mode should show banner."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        expect(page.get_by_text("Demo-tilstand")).to_be_visible()

    def test_demo_shows_example_income(self, page: Page, base_url: str):
        """Demo should show Person 1 and Person 2 income."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        expect(page.get_by_text("Person 1")).to_be_visible()
        expect(page.get_by_text("Person 2")).to_be_visible()

    def test_demo_shows_expense_categories(self, page: Page, base_url: str):
        """Demo should show expense categories."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        expect(page.get_by_text("Bolig", exact=True).first).to_be_visible()

    def test_demo_shows_remaining_amount(self, page: Page, base_url: str):
        """Demo should show remaining amount."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        expect(page.get_by_text("Til fri brug")).to_be_visible()


class TestDemoReadOnly:
    """Tests for demo mode read-only restrictions."""

    def test_demo_hides_navigation(self, page: Page, base_url: str):
        """Demo mode should hide bottom navigation."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        expect(page.locator("nav.fixed.bottom-0")).to_have_count(0)

    def test_demo_logout_clears_session(self, page: Page, base_url: str):
        """Logging out from demo should clear session."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        page.goto(f"{base_url}/budget/logout")
        expect(page).to_have_url(f"{base_url}/budget/login")


class TestDemoDataIntegrity:
    """Tests ensuring demo data is correct."""

    def test_demo_income_total_is_50000(self, page: Page, base_url: str):
        """Demo total income should be 50,000 kr."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        expect(page.get_by_text("50.000")).to_be_visible()
