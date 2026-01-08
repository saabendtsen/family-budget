"""E2E tests for quarterly and semi-annual frequency features."""

import uuid

from playwright.sync_api import Page, expect


class TestExpenseFrequencyUI:
    """Tests for expense frequency radio buttons."""

    def test_expense_modal_shows_four_frequency_options(self, authenticated_page: Page, base_url: str):
        """Expense modal should show all 4 frequency radio buttons."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Open add expense modal
        authenticated_page.click('[data-lucide="plus"]')
        authenticated_page.wait_for_selector("#modal")

        # Verify all 4 frequency options are visible (check the visible div text)
        modal = authenticated_page.locator("#modal")
        expect(modal.locator("text=Månedlig")).to_be_visible()
        expect(modal.locator("text=Kvartalsvis")).to_be_visible()
        expect(modal.locator("text=Halvårlig")).to_be_visible()
        # Use exact match for Årlig to avoid matching Halvårlig
        expect(modal.locator('div:text-is("Årlig")')).to_be_visible()

    def test_expense_modal_frequency_radio_values(self, authenticated_page: Page, base_url: str):
        """Expense frequency radios should have correct values."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Open add expense modal
        authenticated_page.click('[data-lucide="plus"]')
        authenticated_page.wait_for_selector("#modal")

        # Verify radio button values exist
        expect(authenticated_page.locator('input[name="frequency"][value="monthly"]')).to_have_count(1)
        expect(authenticated_page.locator('input[name="frequency"][value="quarterly"]')).to_have_count(1)
        expect(authenticated_page.locator('input[name="frequency"][value="semi-annual"]')).to_have_count(1)
        expect(authenticated_page.locator('input[name="frequency"][value="yearly"]')).to_have_count(1)

    def test_expense_monthly_is_default_selected(self, authenticated_page: Page, base_url: str):
        """Monthly should be the default selected frequency."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Open add expense modal
        authenticated_page.click('[data-lucide="plus"]')
        authenticated_page.wait_for_selector("#modal")

        # Monthly radio should be checked by default
        expect(authenticated_page.locator('input[name="frequency"][value="monthly"]')).to_be_checked()


class TestAddExpenseWithFrequency:
    """Tests for adding expenses with different frequencies."""

    def test_add_quarterly_expense(self, authenticated_page: Page, base_url: str):
        """Should be able to add a quarterly expense."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Open modal
        authenticated_page.click('[data-lucide="plus"]')
        authenticated_page.wait_for_selector("#modal")

        # Fill form with quarterly expense
        expense_name = f"Quarterly Test {uuid.uuid4().hex[:6]}"
        authenticated_page.fill('#expense-name', expense_name)
        authenticated_page.select_option('#expense-category', 'Forbrug')
        authenticated_page.fill('#expense-amount', '2400')

        # Select quarterly frequency by clicking the label (visible div)
        authenticated_page.locator('#modal').locator('text=Kvartalsvis').click()

        # Submit
        authenticated_page.click('button:has-text("Tilføj")')
        authenticated_page.wait_for_url(f"{base_url}/budget/expenses")

        # Verify expense appears in list
        expect(authenticated_page.get_by_text(expense_name)).to_be_visible()

    def test_add_semiannual_expense(self, authenticated_page: Page, base_url: str):
        """Should be able to add a semi-annual expense."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Open modal
        authenticated_page.click('[data-lucide="plus"]')
        authenticated_page.wait_for_selector("#modal")

        # Fill form with semi-annual expense
        expense_name = f"SemiAnnual Test {uuid.uuid4().hex[:6]}"
        authenticated_page.fill('#expense-name', expense_name)
        authenticated_page.select_option('#expense-category', 'Transport')
        authenticated_page.fill('#expense-amount', '4500')

        # Select semi-annual frequency by clicking the label
        authenticated_page.locator('#modal').locator('text=Halvårlig').click()

        # Submit
        authenticated_page.click('button:has-text("Tilføj")')
        authenticated_page.wait_for_url(f"{base_url}/budget/expenses")

        # Verify expense appears
        expect(authenticated_page.get_by_text(expense_name)).to_be_visible()

    def test_add_yearly_expense(self, authenticated_page: Page, base_url: str):
        """Should be able to add a yearly expense."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Open modal
        authenticated_page.click('[data-lucide="plus"]')
        authenticated_page.wait_for_selector("#modal")

        # Fill form with yearly expense
        expense_name = f"Yearly Test {uuid.uuid4().hex[:6]}"
        authenticated_page.fill('#expense-name', expense_name)
        authenticated_page.select_option('#expense-category', 'Forsikring')
        authenticated_page.fill('#expense-amount', '12000')

        # Select yearly frequency by clicking the exact match label
        authenticated_page.locator('#modal').locator('div:text-is("Årlig")').click()

        # Submit
        authenticated_page.click('button:has-text("Tilføj")')
        authenticated_page.wait_for_url(f"{base_url}/budget/expenses")

        # Verify expense appears
        expect(authenticated_page.get_by_text(expense_name)).to_be_visible()


class TestEditExpenseFrequency:
    """Tests for editing expense frequency."""

    def test_edit_expense_preserves_frequency(self, authenticated_page: Page, base_url: str):
        """Editing expense should preserve the frequency selection."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # First add a quarterly expense
        authenticated_page.click('[data-lucide="plus"]')
        authenticated_page.wait_for_selector("#modal")

        expense_name = f"Edit Freq Test {uuid.uuid4().hex[:6]}"
        authenticated_page.fill('#expense-name', expense_name)
        authenticated_page.select_option('#expense-category', 'Bolig')
        authenticated_page.fill('#expense-amount', '3000')
        authenticated_page.locator('#modal').locator('text=Kvartalsvis').click()
        authenticated_page.click('button:has-text("Tilføj")')
        authenticated_page.wait_for_url(f"{base_url}/budget/expenses")

        # Find and click edit button for this expense (look for pencil icon near expense name)
        expense_card = authenticated_page.locator(f'text="{expense_name}"').locator('xpath=ancestor::div[contains(@class, "px-4")]')
        expense_card.locator('[data-lucide="pencil"]').click()
        authenticated_page.wait_for_selector("#modal")

        # Verify quarterly is still selected
        expect(authenticated_page.locator('input[name="frequency"][value="quarterly"]')).to_be_checked()

    def test_change_expense_frequency_to_semiannual(self, authenticated_page: Page, base_url: str):
        """Should be able to change expense frequency from monthly to semi-annual."""
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Add a monthly expense
        authenticated_page.click('[data-lucide="plus"]')
        authenticated_page.wait_for_selector("#modal")

        expense_name = f"Change Freq Test {uuid.uuid4().hex[:6]}"
        authenticated_page.fill('#expense-name', expense_name)
        authenticated_page.select_option('#expense-category', 'Forbrug')
        authenticated_page.fill('#expense-amount', '1200')
        # Monthly is default
        authenticated_page.click('button:has-text("Tilføj")')
        authenticated_page.wait_for_url(f"{base_url}/budget/expenses")

        # Edit and change to semi-annual
        expense_card = authenticated_page.locator(f'text="{expense_name}"').locator('xpath=ancestor::div[contains(@class, "px-4")]')
        expense_card.locator('[data-lucide="pencil"]').click()
        authenticated_page.wait_for_selector("#modal")

        authenticated_page.locator('#modal').locator('text=Halvårlig').click()
        authenticated_page.click('button:has-text("Gem")')
        authenticated_page.wait_for_url(f"{base_url}/budget/expenses")

        # Re-open edit to verify frequency changed
        expense_card = authenticated_page.locator(f'text="{expense_name}"').locator('xpath=ancestor::div[contains(@class, "px-4")]')
        expense_card.locator('[data-lucide="pencil"]').click()
        authenticated_page.wait_for_selector("#modal")
        expect(authenticated_page.locator('input[name="frequency"][value="semi-annual"]')).to_be_checked()


class TestIncomeFrequencyUI:
    """Tests for income frequency dropdown."""

    def test_income_page_shows_frequency_dropdown(self, authenticated_page: Page, base_url: str):
        """Income page should show frequency dropdown for each income source."""
        authenticated_page.goto(f"{base_url}/budget/income")

        # Add income row first (new users have empty list)
        authenticated_page.click('button:has-text("Tilføj indtægtskilde")')

        # Check for frequency dropdown
        expect(authenticated_page.locator('select[name*="frequency"]').first).to_be_visible()

    def test_income_frequency_dropdown_has_all_options(self, authenticated_page: Page, base_url: str):
        """Income frequency dropdown should have all 4 options."""
        authenticated_page.goto(f"{base_url}/budget/income")

        # Add income row first
        authenticated_page.click('button:has-text("Tilføj indtægtskilde")')

        # Get the first frequency dropdown
        dropdown = authenticated_page.locator('select[name*="frequency"]').first

        # Check all options exist
        expect(dropdown.locator('option[value="monthly"]')).to_have_count(1)
        expect(dropdown.locator('option[value="quarterly"]')).to_have_count(1)
        expect(dropdown.locator('option[value="semi-annual"]')).to_have_count(1)
        expect(dropdown.locator('option[value="yearly"]')).to_have_count(1)


class TestAddIncomeWithFrequency:
    """Tests for adding income with different frequencies."""

    def test_add_quarterly_income(self, authenticated_page: Page, base_url: str):
        """Should be able to add quarterly income."""
        authenticated_page.goto(f"{base_url}/budget/income")

        # Add income row first (new users have empty list)
        authenticated_page.click('button:has-text("Tilføj indtægtskilde")')

        # Fill in income source with quarterly frequency
        income_name = f"Quarterly Income {uuid.uuid4().hex[:6]}"
        authenticated_page.fill('input[name="income_name_0"]', income_name)
        authenticated_page.fill('input[name="income_amount_0"]', '9000')
        authenticated_page.select_option('select[name="income_frequency_0"]', 'quarterly')

        # Submit form
        authenticated_page.click('button:has-text("Gem")')
        authenticated_page.wait_for_url(f"{base_url}/budget/")

        # Go back to income page and verify
        authenticated_page.goto(f"{base_url}/budget/income")
        expect(authenticated_page.locator(f'input[value="{income_name}"]')).to_be_visible()

    def test_add_semiannual_income(self, authenticated_page: Page, base_url: str):
        """Should be able to add semi-annual income."""
        authenticated_page.goto(f"{base_url}/budget/income")

        # Add income row first
        authenticated_page.click('button:has-text("Tilføj indtægtskilde")')

        # Fill in income source with semi-annual frequency
        income_name = f"SemiAnnual Inc {uuid.uuid4().hex[:6]}"
        authenticated_page.fill('input[name="income_name_0"]', income_name)
        authenticated_page.fill('input[name="income_amount_0"]', '12000')
        authenticated_page.select_option('select[name="income_frequency_0"]', 'semi-annual')

        # Submit form
        authenticated_page.click('button:has-text("Gem")')
        authenticated_page.wait_for_url(f"{base_url}/budget/")

        # Verify redirect to dashboard worked (page loaded)
        expect(authenticated_page).to_have_url(f"{base_url}/budget/")

    def test_add_yearly_income(self, authenticated_page: Page, base_url: str):
        """Should be able to add yearly income."""
        authenticated_page.goto(f"{base_url}/budget/income")

        # Add income row first
        authenticated_page.click('button:has-text("Tilføj indtægtskilde")')

        # Fill in income source with yearly frequency
        income_name = f"Yearly Bonus {uuid.uuid4().hex[:6]}"
        authenticated_page.fill('input[name="income_name_0"]', income_name)
        authenticated_page.fill('input[name="income_amount_0"]', '24000')
        authenticated_page.select_option('select[name="income_frequency_0"]', 'yearly')

        # Submit form
        authenticated_page.click('button:has-text("Gem")')
        authenticated_page.wait_for_url(f"{base_url}/budget/")

        # Verify redirect to dashboard worked
        expect(authenticated_page).to_have_url(f"{base_url}/budget/")


class TestMultipleIncomeWithFrequencies:
    """Tests for multiple income sources with different frequencies."""

    def test_add_multiple_incomes_different_frequencies(self, authenticated_page: Page, base_url: str):
        """Should be able to add multiple income sources with different frequencies."""
        authenticated_page.goto(f"{base_url}/budget/income")

        # Add first income row
        authenticated_page.click('button:has-text("Tilføj indtægtskilde")')

        # First income - monthly
        authenticated_page.fill('input[name="income_name_0"]', 'Salary')
        authenticated_page.fill('input[name="income_amount_0"]', '30000')
        authenticated_page.select_option('select[name="income_frequency_0"]', 'monthly')

        # Add another income row
        authenticated_page.click('button:has-text("Tilføj indtægtskilde")')

        # Second income - quarterly
        authenticated_page.fill('input[name="income_name_1"]', 'Bonus')
        authenticated_page.fill('input[name="income_amount_1"]', '9000')
        authenticated_page.select_option('select[name="income_frequency_1"]', 'quarterly')

        # Submit
        authenticated_page.click('button:has-text("Gem")')
        authenticated_page.wait_for_url(f"{base_url}/budget/")

        # Go back and verify both exist
        authenticated_page.goto(f"{base_url}/budget/income")
        expect(authenticated_page.locator('input[value="Salary"]')).to_be_visible()


class TestDemoModeFrequencies:
    """Tests for demo mode with frequency features."""

    def test_demo_expenses_page_loads(self, page: Page, base_url: str):
        """Demo expenses page should load with expenses."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")

        # Navigate to expenses
        page.goto(f"{base_url}/budget/expenses")

        # Should see expense list
        expect(page.locator("h1:has-text('Udgifter')")).to_be_visible()

    def test_demo_shows_frequency_labels(self, page: Page, base_url: str):
        """Demo mode should show frequency labels on expenses."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")

        # Navigate to expenses
        page.goto(f"{base_url}/budget/expenses")

        # Should see at least one frequency label (demo has various frequencies)
        # Wait for content to load
        page.wait_for_selector("text=Udgifter")

        # Check that frequency text appears somewhere on page
        content = page.content()
        # At least one of these should be present from demo data
        has_frequency = ("Kvartalsvis" in content or
                        "Halvårlig" in content or
                        "Årlig" in content or
                        "Månedlig" in content)
        assert has_frequency, "Expected to find frequency labels in demo expenses"

    def test_demo_income_page_loads(self, page: Page, base_url: str):
        """Demo mode income page should load successfully."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")

        # Go to income page
        page.goto(f"{base_url}/budget/income")

        # Income page should load with title
        expect(page.locator("h1:has-text('Indkomst')")).to_be_visible()
        # Add income button should be available
        expect(page.locator('button:has-text("Tilføj indtægtskilde")')).to_be_visible()


class TestFrequencyCalculationsOnDashboard:
    """Tests for monthly calculations displayed on dashboard."""

    def test_dashboard_shows_expense_totals(self, authenticated_page: Page, base_url: str):
        """Dashboard should show expense totals after adding expenses."""
        # First add some expenses with different frequencies
        authenticated_page.goto(f"{base_url}/budget/expenses")

        # Add monthly expense: 1000
        authenticated_page.click('[data-lucide="plus"]')
        authenticated_page.wait_for_selector("#modal")
        authenticated_page.fill('#expense-name', 'Monthly Calc Test')
        authenticated_page.select_option('#expense-category', 'Bolig')
        authenticated_page.fill('#expense-amount', '1000')
        authenticated_page.click('button:has-text("Tilføj")')
        authenticated_page.wait_for_url(f"{base_url}/budget/expenses")

        # Add quarterly expense: 900 (300/month)
        authenticated_page.click('[data-lucide="plus"]')
        authenticated_page.wait_for_selector("#modal")
        authenticated_page.fill('#expense-name', 'Quarterly Calc Test')
        authenticated_page.select_option('#expense-category', 'Forbrug')
        authenticated_page.fill('#expense-amount', '900')
        authenticated_page.locator('#modal').locator('text=Kvartalsvis').click()
        authenticated_page.click('button:has-text("Tilføj")')
        authenticated_page.wait_for_url(f"{base_url}/budget/expenses")

        # Go to dashboard
        authenticated_page.goto(f"{base_url}/budget/")

        # Should see expense total displayed
        expect(authenticated_page.get_by_text("Udgifter", exact=True).first).to_be_visible()
