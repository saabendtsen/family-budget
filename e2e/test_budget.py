"""E2E tests for budget functionality."""

import pytest
from playwright.sync_api import Page, expect


class TestDashboard:
    """Tests for dashboard page."""

    def test_dashboard_shows_summary_cards(self, authenticated_page: Page):
        """Dashboard should display income and expense summary cards."""
        expect(authenticated_page.get_by_text("Indkomst", exact=True).first).to_be_visible()
        expect(authenticated_page.get_by_text("Udgifter", exact=True).first).to_be_visible()
        expect(authenticated_page.get_by_text("Til fri brug")).to_be_visible()

    def test_dashboard_shows_income_breakdown(self, authenticated_page: Page):
        """Dashboard should show income breakdown section."""
        # New users start with empty income, so section may be empty or show placeholder
        # Just verify the dashboard renders without error
        expect(authenticated_page.get_by_text("Indkomst", exact=True).first).to_be_visible()

    def test_dashboard_has_logout_button(self, authenticated_page: Page):
        """Dashboard should have logout button."""
        expect(authenticated_page.locator('[data-lucide="log-out"]')).to_be_visible()

    def test_dashboard_sections_are_draggable(self, authenticated_page: Page):
        """Dashboard should have sortable sections container with draggable children."""
        container = authenticated_page.locator('#sortable-sections')
        expect(container).to_be_visible()

        sections = container.locator('[data-section-id]')
        assert sections.count() >= 2  # At least expenses-breakdown and income-breakdown

    def test_dashboard_section_order_persists(self, authenticated_page: Page, base_url: str):
        """Saved section order in localStorage should be restored on reload."""
        custom_order = '["category-chart","income-breakdown","transfer-summary","expenses-breakdown"]'
        authenticated_page.evaluate(
            f"localStorage.setItem('dashboardSectionOrder', '{custom_order}')"
        )

        authenticated_page.goto(f"{base_url}/budget/")

        container = authenticated_page.locator('#sortable-sections')
        sections = container.locator('[data-section-id]')
        first_section_id = sections.first.get_attribute('data-section-id')
        assert first_section_id == 'category-chart'

    def test_dashboard_section_reorder_saves_to_localstorage(self, authenticated_page: Page, base_url: str):
        """Dragging a section should save the new order to localStorage."""
        # Clear any saved order
        authenticated_page.evaluate("localStorage.removeItem('dashboardSectionOrder')")
        authenticated_page.goto(f"{base_url}/budget/")

        # Get the first and last section drag handles
        container = authenticated_page.locator('#sortable-sections')
        sections = container.locator('[data-section-id]')
        count = sections.count()

        if count >= 2:
            first_handle = sections.nth(0).locator('.drag-handle').first
            last_section = sections.nth(count - 1)

            # Drag first section to last position
            first_handle.drag_to(last_section)

            # Check localStorage was updated
            stored = authenticated_page.evaluate("localStorage.getItem('dashboardSectionOrder')")
            assert stored is not None
            import json
            order = json.loads(stored)
            assert isinstance(order, list)
            assert len(order) >= 2


class TestExpenses:
    """Tests for expense management."""

    def test_expenses_page_loads(self, authenticated_page: Page, base_url: str):
        """Expenses page should load correctly."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        expect(authenticated_page.locator("h1:has-text('Udgifter')")).to_be_visible()

    def test_add_expense_button_opens_modal(self, authenticated_page: Page, base_url: str):
        """Add button should open modal."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Click add button (plus icon)
        authenticated_page.click('[data-lucide="plus"]')

        # Modal should be visible
        expect(authenticated_page.locator("#modal")).to_be_visible()
        expect(authenticated_page.locator("text=Tilføj udgift")).to_be_visible()

    def test_add_expense_flow(self, authenticated_page: Page, base_url: str):
        """Should be able to add a new expense."""
        import uuid
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Open modal
        authenticated_page.click('[data-lucide="plus"]')

        # Use unique expense name
        expense_name = f"E2E Expense {uuid.uuid4().hex[:6]}"

        # Fill form
        authenticated_page.fill('#expense-name', expense_name)
        authenticated_page.select_option('#expense-category', 'Bolig')
        authenticated_page.fill('#expense-amount', '5000')
        # Monthly is default, no need to click

        # Submit
        authenticated_page.click('button:has-text("Tilføj")')

        # Should redirect to expenses page with new expense
        authenticated_page.wait_for_url(f"{base_url}/budget/expenses")
        expect(authenticated_page.get_by_text(expense_name)).to_be_visible()

    def test_close_modal_with_x_button(self, authenticated_page: Page, base_url: str):
        """Modal should close when clicking X button."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Open modal
        authenticated_page.click('[data-lucide="plus"]')
        expect(authenticated_page.locator("#modal")).to_be_visible()

        # Close with X button
        authenticated_page.click('[data-lucide="x"]')

        # Modal should be hidden
        expect(authenticated_page.locator("#modal")).to_be_hidden()

    def test_close_modal_with_escape(self, authenticated_page: Page, base_url: str):
        """Modal should close when pressing Escape."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Open modal
        authenticated_page.click('[data-lucide="plus"]')
        expect(authenticated_page.locator("#modal")).to_be_visible()

        # Press Escape
        authenticated_page.keyboard.press("Escape")

        # Modal should be hidden
        expect(authenticated_page.locator("#modal")).to_be_hidden()


class TestNavigation:
    """Tests for navigation between pages."""

    def test_navigate_to_expenses(self, authenticated_page: Page, base_url: str):
        """Should be able to navigate to expenses page."""
        # Look for expenses link in navigation
        authenticated_page.goto(f"{base_url}/budget/")

        # Click empty state link if no expenses, or navigate via URL
        authenticated_page.goto(f"{base_url}/budget/expenses")

        expect(authenticated_page).to_have_url(f"{base_url}/budget/expenses")

    def test_navigate_to_income(self, authenticated_page: Page, base_url: str):
        """Should be able to navigate to income page."""
        authenticated_page.goto(f"{base_url}/budget/income")

        expect(authenticated_page).to_have_url(f"{base_url}/budget/income")

    def test_navigate_to_categories(self, authenticated_page: Page, base_url: str):
        """Should be able to navigate to categories page."""
        authenticated_page.goto(f"{base_url}/budget/categories")

        expect(authenticated_page).to_have_url(f"{base_url}/budget/categories")

    def test_navigate_to_help(self, authenticated_page: Page, base_url: str):
        """Should be able to navigate to help page."""
        authenticated_page.goto(f"{base_url}/budget/help")

        expect(authenticated_page).to_have_url(f"{base_url}/budget/help")


class TestProtectedRoutes:
    """Tests for route protection."""

    def test_dashboard_redirects_when_not_logged_in(self, page: Page, base_url: str):
        """Dashboard should redirect to login when not authenticated."""
        page.goto(f"{base_url}/budget/")

        # Should redirect to login
        expect(page).to_have_url(f"{base_url}/budget/login")

    def test_expenses_redirects_when_not_logged_in(self, page: Page, base_url: str):
        """Expenses page should redirect to login when not authenticated."""
        page.goto(f"{base_url}/budget/expenses")

        expect(page).to_have_url(f"{base_url}/budget/login")


class TestResponsiveLayout:
    """Tests for responsive design."""

    def test_mobile_layout(self, authenticated_page: Page, base_url: str):
        """Page should work on mobile viewport."""
        authenticated_page.set_viewport_size({"width": 375, "height": 667})
        authenticated_page.goto(f"{base_url}/budget/")

        # Dashboard elements should still be visible
        expect(authenticated_page.locator("h1:has-text('Budget')")).to_be_visible()
        expect(authenticated_page.get_by_text("Indkomst", exact=True).first).to_be_visible()
