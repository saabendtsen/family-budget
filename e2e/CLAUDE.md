# E2E Tests Module - AI Agent Guide

Guide to end-to-end testing with Playwright in Family Budget.

## E2E Test Files

| File | Lines | Purpose |
|------|-------|---------|
| `test_auth.py` | 135 | Login/register user flows |
| `test_budget.py` | 159 | Budget operations (income, expenses, categories) |
| `test_frequency.py` | 395 | Frequency handling across all features |
| `test_charts.py` | 96 | Chart rendering and calculations |
| `test_demo.py` | 76 | Demo mode functionality |
| `conftest.py` | ~50 | Playwright fixtures |

**Total**: ~900 lines of E2E tests

## Running E2E Tests

```bash
# All E2E tests (requires browser)
pytest e2e/

# Specific file
pytest e2e/test_auth.py

# Specific test
pytest e2e/test_auth.py::test_login_flow

# Headful (see browser)
pytest e2e/ --headed

# Slow motion (for debugging)
pytest e2e/ --headed --slowmo 1000

# Specific browser
pytest e2e/ --browser=chromium  # or firefox, webkit
```

## Fixtures (`conftest.py`)

### Browser

```python
@pytest.fixture(scope="session")
def browser():
    """Playwright browser instance."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()
```

### Page

```python
@pytest.fixture
def page(browser):
    """New browser page for each test."""
    page = browser.new_page()
    yield page
    page.close()
```

### Base URL

```python
@pytest.fixture
def base_url():
    """Application base URL."""
    return "http://localhost:8086"
```

## Common E2E Patterns

### Registration and Login

```python
def test_user_registration(page, base_url):
    """Test complete registration flow."""
    # Navigate to register page
    page.goto(f"{base_url}/budget/register")

    # Fill form
    page.fill('input[name="username"]', "newuser")
    page.fill('input[name="password"]', "password123")
    page.fill('input[name="confirm_password"]', "password123")

    # Submit
    page.click('button[type="submit"]')

    # Should redirect to dashboard
    page.wait_for_url(f"{base_url}/budget/")
    assert page.is_visible('text=Dashboard')
```

### Adding Expense

```python
def test_add_expense_flow(page, base_url):
    """Test adding expense through UI."""
    # Register and login first
    register_and_login(page, base_url)

    # Go to expenses
    page.goto(f"{base_url}/budget/expenses")

    # Open modal
    page.click('text=Tilføj udgift')

    # Fill form
    page.fill('input[name="name"]', "Test Expense")
    page.select_option('select[name="category"]', "Andet")
    page.fill('input[name="amount"]', "1000")
    page.select_option('select[name="frequency"]', "monthly")

    # Submit
    page.click('form button[type="submit"]')

    # Wait for modal to close
    page.wait_for_selector('#modal.hidden')

    # Verify expense appears
    assert page.is_visible('text=Test Expense')
    assert page.is_visible('text=1.000,00 kr.')
```

### Testing Frequency Conversion

```python
def test_yearly_expense_shows_monthly_amount(page, base_url):
    """Test yearly expense displays monthly equivalent."""
    register_and_login(page, base_url)

    # Add yearly expense
    page.goto(f"{base_url}/budget/expenses")
    page.click('text=Tilføj udgift')

    page.fill('input[name="name"]', "Yearly Expense")
    page.select_option('select[name="category"]', "Andet")
    page.fill('input[name="amount"]', "12000")  # 12000/year
    page.select_option('select[name="frequency"]', "yearly")

    page.click('form button[type="submit"]')
    page.wait_for_selector('#modal.hidden')

    # Should show monthly amount (12000/12 = 1000)
    assert page.is_visible('text=1.000,00 kr.')  # Monthly
    assert page.is_visible('text=12.000,00 kr./år')  # Original
```

### Testing Modal Interactions

```python
def test_modal_closes_on_escape(page, base_url):
    """Test modal closes when Escape key pressed."""
    register_and_login(page, base_url)

    page.goto(f"{base_url}/budget/expenses")

    # Open modal
    page.click('text=Tilføj udgift')
    assert page.is_visible('#modal:not(.hidden)')

    # Press Escape
    page.keyboard.press('Escape')

    # Modal should close
    assert page.is_visible('#modal.hidden')
```

## Page Object Pattern (Optional)

For complex flows, consider page objects:

```python
class DashboardPage:
    """Dashboard page object."""

    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self):
        self.page.goto(f"{self.base_url}/budget/")

    def get_total_income(self) -> str:
        return self.page.inner_text('.total-income')

    def get_total_expenses(self) -> str:
        return self.page.inner_text('.total-expenses')

    def get_leftover(self) -> str:
        return self.page.inner_text('.leftover')

# Usage
def test_dashboard_calculations(page, base_url):
    dashboard = DashboardPage(page, base_url)
    dashboard.navigate()

    income = dashboard.get_total_income()
    assert "kr." in income
```

## Playwright Selectors

### By Text

```python
page.click('text=Tilføj udgift')
page.click('text=Log ind')
```

### By Name Attribute

```python
page.fill('input[name="username"]', "user")
page.fill('input[name="password"]', "pass")
```

### By ID

```python
page.click('#modal')
page.fill('#expense-name', "Expense")
```

### By CSS Selector

```python
page.click('.btn-primary')
page.fill('form input[type="text"]', "value")
```

### By Role (accessible)

```python
page.click('role=button[name="Submit"]')
page.fill('role=textbox[name="Username"]', "user")
```

## Common Actions

### Navigation

```python
page.goto("http://localhost:8086/budget/")
page.go_back()
page.reload()
```

### Clicking

```python
page.click('text=Button')
page.dblclick('text=Item')  # Double click
```

### Filling Forms

```python
page.fill('input[name="field"]', "value")
page.type('input[name="field"]', "value", delay=100)  # Slower typing
```

### Selecting

```python
page.select_option('select[name="category"]', "Andet")
page.select_option('select[name="category"]', label="Andet")  # By label
page.select_option('select[name="category"]', value="andet")  # By value
```

### Checking Visibility

```python
assert page.is_visible('text=Expected')
assert not page.is_visible('text=Should not appear')
```

### Waiting

```python
page.wait_for_selector('text=Loaded')
page.wait_for_url("http://localhost:8086/budget/")
page.wait_for_timeout(1000)  # Wait 1 second (avoid if possible)
```

## Screenshots and Videos

### Take Screenshot

```python
def test_dashboard_appearance(page, base_url):
    register_and_login(page, base_url)
    page.goto(f"{base_url}/budget/")

    # Take screenshot
    page.screenshot(path="dashboard.png")
```

### Full Page Screenshot

```python
page.screenshot(path="full-page.png", full_page=True)
```

### Enable Video Recording

In `conftest.py`:

```python
@pytest.fixture
def page(browser):
    context = browser.new_context(record_video_dir="videos/")
    page = context.new_page()
    yield page
    page.close()
    context.close()
```

## Helper Functions

### Register and Login Helper

```python
def register_and_login(page, base_url, username="testuser", password="password123"):
    """Helper to register and login a test user."""
    # Register
    page.goto(f"{base_url}/budget/register")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.fill('input[name="confirm_password"]', password)
    page.click('button[type="submit"]')

    # Wait for dashboard
    page.wait_for_url(f"{base_url}/budget/")
```

### Add Sample Data Helper

```python
def add_sample_income(page, base_url):
    """Add sample income data."""
    page.goto(f"{base_url}/budget/income")

    page.fill('input[name="person_0"]', "Person 1")
    page.fill('input[name="amount_0"]', "30000")
    page.select_option('select[name="frequency_0"]', "monthly")

    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/budget/income")
```

## Testing Best Practices

### ✅ DO

- **Test complete user workflows**: Registration → Add data → View results
- **Use stable selectors**: Prefer text content or `data-testid` over CSS classes
- **Wait for elements**: Use `wait_for_selector` instead of `wait_for_timeout`
- **Clean up after tests**: Each test should be independent
- **Test happy and unhappy paths**: Both success and error scenarios

### ❌ DON'T

- **Don't test implementation details**: Focus on user-visible behavior
- **Don't use brittle selectors**: Avoid complex CSS selectors that break easily
- **Don't hardcode waits**: Use Playwright's auto-waiting instead of timeouts
- **Don't test what units cover**: E2E for workflows, not individual functions
- **Don't run E2E in CI** (currently): Browser setup is complex, unit tests are faster

## Debugging E2E Tests

### Run Headful

```bash
pytest e2e/ --headed
```

### Slow Motion

```bash
pytest e2e/ --headed --slowmo 1000  # 1 second delay between actions
```

### Debug Mode

```python
page.pause()  # Opens Playwright Inspector
```

### Screenshots on Failure

```python
def test_something(page):
    try:
        # Test code
        assert page.is_visible('text=Expected')
    except AssertionError:
        page.screenshot(path="failure.png")
        raise
```

## Why Not in CI?

E2E tests are **not run in CI** currently because:
1. Require browser installation
2. Slower than unit tests (30+ seconds)
3. More flaky (network, timing issues)
4. Unit tests provide good coverage

**Run E2E tests locally** before major changes or releases.

## Related Documentation

- **Testing Guide**: `../docs/guides/testing-strategy.md`
- **Unit Tests**: `../tests/CLAUDE.md`
- **Playwright Docs**: https://playwright.dev/python/
