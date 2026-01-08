"""Integration tests for API endpoints."""

import pytest


class TestAuthentication:
    """Tests for authentication endpoints."""

    def test_login_page_accessible(self, client):
        """Login page should be accessible without auth."""
        response = client.get("/budget/login")

        assert response.status_code == 200
        assert "login" in response.text.lower()

    def test_login_redirects_when_authenticated(self, authenticated_client):
        """Login page should redirect if already authenticated."""
        response = authenticated_client.get("/budget/login", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/budget/"

    def test_login_success(self, client, db_module):
        """Successful login should set cookie and redirect."""
        db_module.create_user("loginuser", "password123")

        response = client.post(
            "/budget/login",
            data={"username": "loginuser", "password": "password123"},
            follow_redirects=False
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/budget/"
        assert "budget_session" in response.cookies

    def test_login_failure(self, client, db_module):
        """Failed login should show error."""
        db_module.create_user("loginuser", "password123")

        response = client.post(
            "/budget/login",
            data={"username": "loginuser", "password": "wrongpassword"}
        )

        assert response.status_code == 200
        assert "forkert" in response.text.lower()

    def test_register_page_accessible(self, client):
        """Register page should be accessible without auth."""
        response = client.get("/budget/register")

        assert response.status_code == 200

    def test_register_success(self, client):
        """Successful registration should create user and login."""
        response = client.post(
            "/budget/register",
            data={
                "username": "newuser",
                "password": "password123",
                "password_confirm": "password123"
            },
            follow_redirects=False
        )

        assert response.status_code == 303
        assert "budget_session" in response.cookies

    def test_register_short_username(self, client):
        """Registration should fail with short username."""
        response = client.post(
            "/budget/register",
            data={
                "username": "ab",
                "password": "password123",
                "password_confirm": "password123"
            }
        )

        assert response.status_code == 200
        assert "mindst 3" in response.text.lower()

    def test_register_short_password(self, client):
        """Registration should fail with short password."""
        response = client.post(
            "/budget/register",
            data={
                "username": "validuser",
                "password": "short",
                "password_confirm": "short"
            }
        )

        assert response.status_code == 200
        assert "mindst 6" in response.text.lower()

    def test_register_password_mismatch(self, client):
        """Registration should fail when passwords don't match."""
        response = client.post(
            "/budget/register",
            data={
                "username": "validuser",
                "password": "password123",
                "password_confirm": "different123"
            }
        )

        assert response.status_code == 200
        assert "matcher ikke" in response.text.lower()

    def test_register_duplicate_username(self, client, db_module):
        """Registration should fail for existing username."""
        db_module.create_user("existing", "password123")

        response = client.post(
            "/budget/register",
            data={
                "username": "existing",
                "password": "newpass123",
                "password_confirm": "newpass123"
            }
        )

        assert response.status_code == 200
        assert "allerede" in response.text.lower()

    def test_logout(self, authenticated_client):
        """Logout should clear session and redirect to login."""
        response = authenticated_client.get("/budget/logout", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/budget/login"

    def test_demo_mode(self, client):
        """Demo mode should set special session."""
        response = client.get("/budget/demo", follow_redirects=False)

        assert response.status_code == 303
        assert response.cookies.get("budget_session") == "demo"


class TestProtectedEndpoints:
    """Tests for endpoint authentication requirements."""

    def test_dashboard_requires_auth(self, client):
        """Dashboard should redirect to login without auth."""
        response = client.get("/budget/", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/budget/login"

    def test_income_requires_auth(self, client):
        """Income page should redirect to login without auth."""
        response = client.get("/budget/income", follow_redirects=False)

        assert response.status_code == 303

    def test_expenses_requires_auth(self, client):
        """Expenses page should redirect to login without auth."""
        response = client.get("/budget/expenses", follow_redirects=False)

        assert response.status_code == 303

    def test_categories_requires_auth(self, client):
        """Categories page should redirect to login without auth."""
        response = client.get("/budget/categories", follow_redirects=False)

        assert response.status_code == 303

    def test_help_requires_auth(self, client):
        """Help page should redirect to login without auth."""
        response = client.get("/budget/help", follow_redirects=False)

        assert response.status_code == 303


class TestPrivacyPolicy:
    """Tests for privacy policy page."""

    def test_privacy_accessible_without_auth(self, client):
        """Privacy page should be accessible without authentication."""
        response = client.get("/budget/privacy")

        assert response.status_code == 200

    def test_privacy_contains_required_sections(self, client):
        """Privacy page should contain required GDPR information."""
        response = client.get("/budget/privacy")

        # Required sections for GDPR compliance
        assert "privatlivspolitik" in response.text.lower()
        assert "data" in response.text.lower()
        assert "cookies" in response.text.lower()
        assert "rettigheder" in response.text.lower()
        assert "kontakt" in response.text.lower()

    def test_privacy_accessible_when_authenticated(self, authenticated_client):
        """Privacy page should also be accessible when logged in."""
        response = authenticated_client.get("/budget/privacy")

        assert response.status_code == 200


class TestDashboard:
    """Tests for dashboard functionality."""

    def test_dashboard_accessible_when_authenticated(self, authenticated_client):
        """Dashboard should be accessible when logged in."""
        response = authenticated_client.get("/budget/")

        assert response.status_code == 200

    def test_dashboard_shows_budget_info(self, authenticated_client):
        """Dashboard should display budget information."""
        response = authenticated_client.get("/budget/")

        # Should contain budget-related content
        assert "budget" in response.text.lower() or "overblik" in response.text.lower()

    def test_demo_mode_shows_demo_data(self, client):
        """Demo mode should show demo data."""
        # Enter demo mode
        client.get("/budget/demo")

        response = client.get("/budget/")

        assert response.status_code == 200
        # Demo mode indicator or demo data should be present
        assert "demo" in response.text.lower() or "Person 1" in response.text


class TestIncomeEndpoints:
    """Tests for income management endpoints."""

    def test_income_page_loads(self, authenticated_client):
        """Income page should load for authenticated users."""
        response = authenticated_client.get("/budget/income")

        assert response.status_code == 200

    def test_update_income(self, authenticated_client):
        """POST to income should update values."""
        response = authenticated_client.post(
            "/budget/income",
            data={
                "person1_name": "Alice",
                "person1_amount": "35000",
                "person2_name": "Bob",
                "person2_amount": "28000"
            },
            follow_redirects=False
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/budget/"


class TestExpenseEndpoints:
    """Tests for expense management endpoints."""

    def test_expenses_page_loads(self, authenticated_client):
        """Expenses page should load for authenticated users."""
        response = authenticated_client.get("/budget/expenses")

        assert response.status_code == 200

    def test_add_expense(self, authenticated_client):
        """POST to add expense should create expense."""
        response = authenticated_client.post(
            "/budget/expenses/add",
            data={
                "name": "Test Expense",
                "category": "Bolig",
                "amount": "1000",
                "frequency": "monthly"
            },
            follow_redirects=False
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/budget/expenses"

    def test_delete_expense(self, authenticated_client, db_module):
        """POST to delete expense should remove it."""
        # First add an expense using the authenticated user's ID
        user_id = authenticated_client.user_id
        expense_id = db_module.add_expense(user_id, "ToDelete", "Bolig", 500, "monthly")

        response = authenticated_client.post(
            f"/budget/expenses/{expense_id}/delete",
            follow_redirects=False
        )

        assert response.status_code == 303

    def test_edit_expense(self, authenticated_client, db_module):
        """POST to edit expense should update it."""
        user_id = authenticated_client.user_id
        expense_id = db_module.add_expense(user_id, "Original", "Bolig", 500, "monthly")

        response = authenticated_client.post(
            f"/budget/expenses/{expense_id}/edit",
            data={
                "name": "Updated",
                "category": "Transport",
                "amount": "750",
                "frequency": "yearly"
            },
            follow_redirects=False
        )

        assert response.status_code == 303


class TestCategoryEndpoints:
    """Tests for category management endpoints."""

    def test_categories_page_loads(self, authenticated_client):
        """Categories page should load for authenticated users."""
        response = authenticated_client.get("/budget/categories")

        assert response.status_code == 200

    def test_add_category(self, authenticated_client):
        """POST to add category should create category."""
        response = authenticated_client.post(
            "/budget/categories/add",
            data={"name": "NewCategory", "icon": "star"},
            follow_redirects=False
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/budget/categories"

    def test_edit_category(self, authenticated_client, db_module):
        """POST to edit category should update it."""
        category_id = db_module.add_category("OldName", "old-icon")

        response = authenticated_client.post(
            f"/budget/categories/{category_id}/edit",
            data={"name": "NewName", "icon": "new-icon"},
            follow_redirects=False
        )

        assert response.status_code == 303

    def test_delete_category(self, authenticated_client, db_module):
        """POST to delete unused category should remove it."""
        category_id = db_module.add_category("Unused", "icon")

        response = authenticated_client.post(
            f"/budget/categories/{category_id}/delete",
            follow_redirects=False
        )

        assert response.status_code == 303


class TestHelpers:
    """Tests for helper functions."""

    def test_format_currency(self):
        """format_currency should format Danish-style currency."""
        from src.api import format_currency

        assert format_currency(1000) == "1.000 kr"
        assert format_currency(1000000) == "1.000.000 kr"
        assert format_currency(0) == "0 kr"


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    def test_rate_limit_after_many_attempts(self, client, db_module):
        """Should rate limit after too many failed login attempts."""
        db_module.create_user("ratelimit", "password123")

        # Make 5 failed attempts
        for _ in range(5):
            client.post(
                "/budget/login",
                data={"username": "ratelimit", "password": "wrong"}
            )

        # 6th attempt should be rate limited
        response = client.post(
            "/budget/login",
            data={"username": "ratelimit", "password": "wrong"}
        )

        assert response.status_code == 429
        assert "for mange" in response.text.lower()
