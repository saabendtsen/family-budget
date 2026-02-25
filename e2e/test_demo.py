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

    def test_demo_shows_navigation_for_exploration(self, page: Page, base_url: str):
        """Demo mode shows navigation so users can explore the app."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        expect(page.locator("nav.fixed.bottom-0")).to_be_visible()

    def test_demo_logout_clears_session(self, page: Page, base_url: str):
        """Logging out from demo should clear session."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        page.goto(f"{base_url}/budget/logout")
        expect(page).to_have_url(f"{base_url}/budget/login")


class TestDemoDataIntegrity:
    """Tests ensuring demo data is correct."""

    def test_demo_income_total_is_55000(self, page: Page, base_url: str):
        """Demo total monthly income should be 55,000 kr (28K + 22K + 5K from semi-annual bonus)."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        expect(page.get_by_text("55.000")).to_be_visible()


class TestDemoToggle:
    """Tests for simple/advanced demo toggle."""

    def test_toggle_visible_in_demo_banner(self, page: Page, base_url: str):
        """Toggle should be visible in demo banner."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        expect(page.get_by_text("Avanceret")).to_be_visible()

    def test_toggle_switches_to_advanced(self, page: Page, base_url: str):
        """Clicking toggle should switch to advanced mode."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        page.get_by_role("link", name="Avanceret").click()
        page.wait_for_load_state("networkidle")
        # In advanced mode, accounts should appear
        expect(page.get_by_text("Budgetkonto")).to_be_visible()

    def test_toggle_switches_back_to_simple(self, page: Page, base_url: str):
        """Clicking toggle again should switch back to simple."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        # Switch to advanced
        page.get_by_role("link", name="Avanceret").click()
        page.wait_for_load_state("networkidle")
        # Switch back to simple
        page.get_by_role("link", name="Simpel").click()
        page.wait_for_load_state("networkidle")
        # Accounts should be gone
        expect(page.get_by_text("Budgetkonto")).not_to_be_visible()

    def test_advanced_persists_across_pages(self, page: Page, base_url: str):
        """Advanced mode should persist when navigating to other pages."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        page.get_by_role("link", name="Avanceret").click()
        page.wait_for_load_state("networkidle")
        # Navigate to income page
        page.goto(f"{base_url}/budget/income")
        # Should still be in advanced mode — extra income visible (value in input field)
        expect(page.locator("input[value='Børnepenge']")).to_be_visible()
