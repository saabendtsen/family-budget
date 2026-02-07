# Guide: Testing Strategy

How to write and run tests for Family Budget.

## Test Organization

```
tests/
├── test_api.py          # Route/endpoint tests (913 lines)
├── test_database.py     # Database function tests (805 lines)
├── test_charts.py       # Chart calculation tests
└── conftest.py          # Fixtures and setup

e2e/
├── test_auth.py         # Authentication E2E (Playwright)
├── test_budget.py       # Budget operations E2E
├── test_frequency.py    # Frequency handling E2E
├── test_charts.py       # Chart rendering E2E
├── test_demo.py         # Demo mode E2E
└── conftest.py          # Playwright fixtures
```

## Running Tests

```bash
# All unit tests (fast)
pytest tests/

# All E2E tests (slower, requires browser)
pytest e2e/

# All tests
pytest

# Specific file
pytest tests/test_api.py

# Specific test
pytest tests/test_api.py::TestAuthentication::test_login_success

# With coverage
pytest --cov=src tests/

# Verbose output
pytest -v
```

## Unit Testing Patterns

### Test Fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def client():
    """Test client for API."""
    from src.api import app
    return TestClient(app)

@pytest.fixture
def authenticated_client(client):
    """Authenticated test client with session."""
    # Create test user
    db.create_user("testuser", "password123")

    # Login
    response = client.post("/budget/login", data={
        "username": "testuser",
        "password": "password123"
    })

    # Return client with session cookie
    return client
```

### Route Testing (`tests/test_api.py`)

**Test authentication requirement**:
```python
def test_route_requires_auth(client):
    """Test protected route redirects to login."""
    response = client.get("/budget/expenses")
    assert response.status_code == 303
    assert response.headers["location"] == "/budget/login"
```

**Test successful access**:
```python
def test_route_success(authenticated_client):
    """Test authenticated access."""
    response = authenticated_client.get("/budget/expenses")
    assert response.status_code == 200
    assert b"Udgifter" in response.content
```

**Test form submission**:
```python
def test_add_expense(authenticated_client):
    """Test adding expense."""
    response = authenticated_client.post("/budget/expenses/add", data={
        "name": "Test Expense",
        "category": "Andet",
        "amount": "1.000,50",
        "frequency": "monthly"
    })
    assert response.status_code == 303
    assert response.headers["location"] == "/budget/expenses"

    # Verify expense was added
    response = authenticated_client.get("/budget/expenses")
    assert b"Test Expense" in response.content
```

### Database Testing (`tests/test_database.py`)

**Test CRUD operations**:
```python
def test_create_and_get_expense():
    """Test expense creation and retrieval."""
    user_id = db.create_user("testuser", "password123")
    db.ensure_default_categories(user_id)

    expense_id = db.add_expense(
        user_id=user_id,
        name="Test Expense",
        category="Andet",
        amount=100.50,
        frequency="monthly"
    )

    assert expense_id > 0

    expenses = db.get_all_expenses(user_id)
    assert len(expenses) == 1
    assert expenses[0].name == "Test Expense"
    assert expenses[0].amount == 100.50
```

**Test user isolation**:
```python
def test_user_isolation():
    """Test users can't access each other's data."""
    user1 = db.create_user("user1", "password")
    user2 = db.create_user("user2", "password")

    # User 1 adds expense
    expense_id = db.add_expense(user1, "Expense", "Andet", 100, "monthly")

    # User 2 can't see it
    expenses = db.get_all_expenses(user2)
    assert len(expenses) == 0

    # User 2 can't delete it
    db.delete_expense(expense_id, user2)
    expenses = db.get_all_expenses(user1)
    assert len(expenses) == 1  # Still there
```

## E2E Testing with Playwright

### Setup (`e2e/conftest.py`)

```python
@pytest.fixture
def browser():
    """Playwright browser."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    """Browser page."""
    page = browser.new_page()
    yield page
    page.close()
```

### E2E Test Pattern (`e2e/test_budget.py`)

```python
def test_add_expense_flow(page):
    """Test complete expense addition flow."""
    # Register and login
    page.goto("http://localhost:8086/budget/register")
    page.fill('input[name="username"]', "testuser")
    page.fill('input[name="password"]', "password123")
    page.fill('input[name="confirm_password"]', "password123")
    page.click('button[type="submit"]')

    # Navigate to expenses
    page.goto("http://localhost:8086/budget/expenses")

    # Open modal
    page.click('text=Tilføj udgift')

    # Fill form
    page.fill('input[name="name"]', "Test Expense")
    page.select_option('select[name="category"]', "Andet")
    page.fill('input[name="amount"]', "1000")
    page.select_option('select[name="frequency"]', "monthly")

    # Submit
    page.click('button[type="submit"]')

    # Verify
    assert page.is_visible('text=Test Expense')
```

## Writing Good Tests

### ✅ DO

- **Test one thing per test**
- **Use descriptive test names** (`test_login_with_invalid_password`)
- **Arrange-Act-Assert pattern**
- **Clean up after tests** (fixtures handle this)
- **Test edge cases** (empty inputs, special characters, etc.)
- **Test error handling** (what happens when things fail)

### ❌ DON'T

- **Don't test framework code** (e.g., testing that FastAPI redirects work)
- **Don't skip cleanup** (use fixtures)
- **Don't hardcode URLs** in E2E tests (use base_url)
- **Don't depend on test order** (tests should be independent)
- **Don't forget negative tests** (test what should fail)

## Test Categories

### Unit Tests
**What**: Individual functions in isolation
**Speed**: Fast (<1s total)
**Coverage**: Database functions, helpers, calculations
**File**: `tests/test_database.py`, `tests/test_charts.py`

### Integration Tests
**What**: Multiple components together
**Speed**: Medium (1-5s total)
**Coverage**: API routes calling database
**File**: `tests/test_api.py`

### E2E Tests
**What**: Full user workflows
**Speed**: Slow (10-30s total)
**Coverage**: Complete features from user perspective
**File**: `e2e/test_*.py`

## Common Test Patterns

### Testing Danish Amount Parsing

```python
def test_parse_danish_amount():
    """Test Danish number parsing."""
    from src.api import parse_danish_amount

    assert parse_danish_amount("1.000,50") == 1000.50
    assert parse_danish_amount("25.000") == 25000.0
    assert parse_danish_amount("100") == 100.0
```

### Testing Frequency Conversion

```python
def test_monthly_amount_conversion():
    """Test frequency to monthly conversion."""
    expense = db.Expense(
        id=1, user_id=1, name="Test", category="Andet",
        amount=12000, frequency="yearly"
    )
    assert expense.monthly_amount == 1000.0
```

### Testing Authentication

```python
def test_password_hashing():
    """Test password hashing and verification."""
    password = "secret123"
    hash1, salt = db.hash_password(password)

    # Same password, different hash (unique salt)
    hash2, _ = db.hash_password(password)
    assert hash1 != hash2

    # Verify password
    assert db.verify_password(password, hash1, salt)
    assert not db.verify_password("wrong", hash1, salt)
```

## Debugging Failed Tests

### View test output

```bash
pytest -v -s  # -s shows print statements
```

### Run single test with debugging

```python
def test_something():
    result = function_to_test()
    import pdb; pdb.set_trace()  # Debugger
    assert result == expected
```

### Check actual vs expected

```bash
pytest --tb=short  # Shorter traceback
pytest --tb=long   # Full traceback
```

## CI Integration

Tests run automatically on:
- Pull requests
- Pushes to master
- Via GitHub Actions (`.github/workflows/ci.yml`)

**What runs in CI**:
- Unit tests only (`pytest tests/`)
- E2E tests excluded (no browser in CI)

## Related Documentation

- **Pattern Guide**: `../../PATTERNS.md` → Testing Patterns
- **Test Files**: `../../tests/`, `../../e2e/`
- **CI Config**: `../../.github/workflows/ci.yml`
