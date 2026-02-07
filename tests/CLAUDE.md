# Tests Module - AI Agent Guide

Guide to unit and integration testing in Family Budget.

## Test Files Overview

| File | Lines | Purpose | Test Count |
|------|-------|---------|------------|
| `test_api.py` | 913 | Route/endpoint tests | 50+ tests |
| `test_database.py` | 805 | Database function tests | 40+ tests |
| `test_charts.py` | ~100 | Chart calculation tests | 10+ tests |
| `conftest.py` | ~100 | Fixtures and setup | N/A |

**Total**: ~1,900 lines of test code

## Running Tests

```bash
# All unit tests (fast, ~5-10 seconds)
pytest tests/

# Specific file
pytest tests/test_api.py

# Specific test class
pytest tests/test_api.py::TestAuthentication

# Specific test
pytest tests/test_api.py::TestAuthentication::test_login_success

# With verbose output
pytest -v

# With coverage
pytest --cov=src tests/

# Stop on first failure
pytest -x
```

## Test Organization (`test_api.py`)

Tests organized by feature:

```python
class TestAuthentication:
    """Login, register, password reset tests."""

class TestPasswordReset:
    """Password reset flow tests."""

class TestProtectedEndpoints:
    """Access control tests."""

class TestDashboard:
    """Dashboard calculations and display."""

class TestIncomeEndpoints:
    """Income CRUD tests."""

class TestExpenseEndpoints:
    """Expense CRUD tests."""

class TestCategoryEndpoints:
    """Category CRUD tests."""

class TestHelpers:
    """Utility function tests."""

class TestFeedback:
    """Feedback form tests."""

class TestRateLimiting:
    """Rate limit enforcement tests."""
```

## Fixtures (`conftest.py`)

### Test Client

```python
@pytest.fixture
def client():
    """Test client for making requests."""
    from src.api import app
    return TestClient(app)
```

**Usage**:
```python
def test_route(client):
    response = client.get("/budget/login")
    assert response.status_code == 200
```

### Authenticated Client

```python
@pytest.fixture
def authenticated_client(client):
    """Client with valid session cookie."""
    # Create user
    db.create_user("testuser", "password123")

    # Login
    response = client.post("/budget/login", data={
        "username": "testuser",
        "password": "password123"
    })

    # Client now has session cookie
    return client
```

**Usage**:
```python
def test_protected_route(authenticated_client):
    response = authenticated_client.get("/budget/expenses")
    assert response.status_code == 200
```

### Database Reset

```python
@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test."""
    # Executed automatically before every test
    db.init_db()
```

## Common Test Patterns

### Testing Authentication Requirements

```python
def test_route_requires_login(client):
    """Test that protected route redirects to login."""
    response = client.get("/budget/expenses")

    assert response.status_code == 303
    assert response.headers["location"] == "/budget/login"
```

### Testing Successful Access

```python
def test_route_authenticated_access(authenticated_client):
    """Test authenticated user can access route."""
    response = authenticated_client.get("/budget/expenses")

    assert response.status_code == 200
    assert b"Udgifter" in response.content
```

### Testing Form Submission

```python
def test_add_expense(authenticated_client):
    """Test adding expense via form."""
    # Submit form
    response = authenticated_client.post("/budget/expenses/add", data={
        "name": "Test Expense",
        "category": "Andet",
        "amount": "1.000,50",
        "frequency": "monthly"
    })

    # Check redirect
    assert response.status_code == 303
    assert response.headers["location"] == "/budget/expenses"

    # Verify expense was added
    response = authenticated_client.get("/budget/expenses")
    assert b"Test Expense" in response.content
    assert b"1.000,50" in response.content
```

### Testing Input Validation

```python
def test_invalid_input(authenticated_client):
    """Test form validation."""
    response = authenticated_client.post("/budget/expenses/add", data={
        "name": "",  # Invalid: empty name
        "category": "Andet",
        "amount": "100",
        "frequency": "monthly"
    })

    # Should not redirect (shows error)
    assert response.status_code == 200
    assert b"error" in response.content.lower()
```

### Testing Database Operations

```python
def test_create_and_retrieve_expense():
    """Test expense CRUD."""
    # Create user
    user_id = db.create_user("testuser", "password123")
    db.ensure_default_categories(user_id)

    # Add expense
    expense_id = db.add_expense(
        user_id=user_id,
        name="Test Expense",
        category="Andet",
        amount=100.50,
        frequency="monthly"
    )

    assert expense_id > 0

    # Retrieve
    expenses = db.get_all_expenses(user_id)

    assert len(expenses) == 1
    assert expenses[0].name == "Test Expense"
    assert expenses[0].amount == 100.50
    assert expenses[0].monthly_amount == 100.50
```

### Testing User Isolation

```python
def test_users_cannot_see_each_other_data():
    """Test user data isolation."""
    # Create two users
    user1 = db.create_user("user1", "password")
    user2 = db.create_user("user2", "password")

    db.ensure_default_categories(user1)

    # User 1 adds expense
    expense_id = db.add_expense(user1, "Expense 1", "Andet", 100, "monthly")

    # User 2 shouldn't see it
    expenses = db.get_all_expenses(user2)
    assert len(expenses) == 0

    # User 2 can't delete it
    db.delete_expense(expense_id, user2)

    # Still exists for user 1
    expenses = db.get_all_expenses(user1)
    assert len(expenses) == 1
```

## Test Naming Conventions

**Format**: `test_[feature]_[scenario]`

**Examples**:
- `test_login_success` - Successful login
- `test_login_invalid_password` - Login fails with wrong password
- `test_add_expense_requires_auth` - Adding expense requires authentication
- `test_delete_expense_user_isolation` - Can't delete other user's expense

## Assertions

### Status Codes

```python
assert response.status_code == 200  # OK
assert response.status_code == 303  # Redirect (POST-Redirect-GET)
assert response.status_code == 404  # Not Found
assert response.status_code == 422  # Validation Error
```

### Content Checks

```python
assert b"Expected Text" in response.content
assert b"Error Message" not in response.content
```

### Headers

```python
assert response.headers["location"] == "/budget/expected-url"
assert "budget_session" in response.cookies
```

### Database State

```python
expenses = db.get_all_expenses(user_id)
assert len(expenses) == 2
assert expenses[0].name == "Expected Name"
```

## Mocking External Services

For external APIs (e.g., GitHub API for feedback):

```python
from unittest.mock import patch

def test_feedback_submission(authenticated_client):
    """Test feedback creates GitHub issue."""
    with patch('httpx.AsyncClient.post') as mock_post:
        # Mock successful API response
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"number": 123}

        response = authenticated_client.post("/budget/feedback", data={
            "feedback_type": "bug",
            "message": "Test feedback"
        })

        assert response.status_code == 200
        assert b"Tak for din feedback" in response.content

        # Verify API was called
        mock_post.assert_called_once()
```

## Test Data Helpers

### Creating Test User with Data

```python
def create_test_user_with_data():
    """Create user with sample data for testing."""
    user_id = db.create_user("testuser", "password123")
    db.ensure_default_categories(user_id)

    # Add test income
    db.add_income(user_id, "Salary", 30000, "monthly")

    # Add test expenses
    db.add_expense(user_id, "Rent", "Bolig", 10000, "monthly")
    db.add_expense(user_id, "Food", "Mad", 5000, "monthly")

    return user_id
```

## Coverage

Check test coverage:

```bash
pytest --cov=src --cov-report=html tests/

# Open htmlcov/index.html in browser
```

**Current coverage**: ~85% (good coverage of core functionality)

**Areas with less coverage**:
- Error handling edge cases
- Some admin/settings routes
- Demo mode edge cases

## Debugging Tests

### Print debugging

```bash
pytest -s  # Shows print() statements
```

```python
def test_something():
    print(f"Debug: {variable}")
    assert condition
```

### Breakpoint

```python
def test_something():
    result = function_to_test()
    import pdb; pdb.set_trace()  # Debugger
    assert result == expected
```

### Verbose failure output

```bash
pytest -vv  # Very verbose
pytest --tb=long  # Full tracebacks
```

## CI Integration

Tests run automatically on:
- Every pull request
- Every push to master
- Via GitHub Actions (`.github/workflows/ci.yml`)

**Only unit tests run in CI** (no E2E tests - they require a browser).

## Best Practices

### ✅ DO

- Test one thing per test function
- Use descriptive test names
- Arrange-Act-Assert pattern
- Test both success and failure cases
- Use fixtures for common setup
- Keep tests independent
- Test edge cases

### ❌ DON'T

- Don't test framework code
- Don't depend on test execution order
- Don't share state between tests
- Don't skip cleanup (use fixtures)
- Don't hardcode test data that could change
- Don't test implementation details

## Related Documentation

- **Testing Guide**: `../docs/guides/testing-strategy.md`
- **Patterns**: `../PATTERNS.md` → Testing Patterns
- **E2E Tests**: `../e2e/CLAUDE.md`
- **CI Config**: `../.github/workflows/ci.yml`
