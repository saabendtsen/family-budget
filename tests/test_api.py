"""Integration tests for API endpoints."""

import pytest


class TestAuthentication:
    """Tests for authentication endpoints."""

    def test_login_page_accessible(self, client):
        """Login page should be accessible without auth."""
        response = client.get("/budget/login")

        assert response.status_code == 200
        assert "login" in response.text.lower()

    def test_login_page_contains_app_description(self, client):
        """Login page should contain app description and features."""
        response = client.get("/budget/login")

        assert response.status_code == 200
        # Check tagline
        assert "Hold styr på familiens økonomi" in response.text
        # Check feature bullets
        assert "Overblik over indkomst" in response.text
        assert "Organiser udgifter" in response.text
        assert "hvad der er tilbage" in response.text
        # Check demo link exists
        assert "/budget/demo" in response.text

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


class TestPasswordReset:
    """Tests for password reset endpoints."""

    def test_forgot_password_page_accessible(self, client):
        """Forgot password page should be accessible without auth."""
        response = client.get("/budget/forgot-password")

        assert response.status_code == 200
        assert "Glemt adgangskode" in response.text

    def test_forgot_password_shows_success_for_any_email(self, client):
        """Forgot password should show success even for unknown email (prevent enumeration)."""
        response = client.post(
            "/budget/forgot-password",
            data={"email": "unknown@example.com"}
        )

        assert response.status_code == 200
        assert "sendt et link" in response.text

    def test_forgot_password_creates_token_for_valid_user(self, client, db_module):
        """Forgot password should create token for user with email."""
        user_id = db_module.create_user("resetuser1", "oldpass")
        db_module.update_user_email(user_id, "reset@example.com")

        response = client.post(
            "/budget/forgot-password",
            data={"email": "reset@example.com"}
        )

        assert response.status_code == 200
        # Token should be created (we can't easily check this without mocking email)

    def test_reset_password_invalid_token(self, client):
        """Reset password with invalid token should show error."""
        response = client.get("/budget/reset-password/invalidtoken123")

        assert response.status_code == 200
        assert "ugyldigt" in response.text.lower() or "udløbet" in response.text.lower()

    def test_reset_password_valid_token_shows_form(self, client, db_module):
        """Reset password with valid token should show password form."""
        import hashlib
        from datetime import datetime, timedelta

        user_id = db_module.create_user("resetuser2", "oldpass")
        token = "validtoken123"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        db_module.create_password_reset_token(user_id, token_hash, expires_at)

        response = client.get(f"/budget/reset-password/{token}")

        assert response.status_code == 200
        assert "Ny adgangskode" in response.text

    def test_reset_password_changes_password(self, client, db_module):
        """Reset password should update user's password."""
        import hashlib
        from datetime import datetime, timedelta

        user_id = db_module.create_user("resetuser3", "oldpassword")
        token = "changetoken123"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        db_module.create_password_reset_token(user_id, token_hash, expires_at)

        response = client.post(
            f"/budget/reset-password/{token}",
            data={"password": "newpassword", "password_confirm": "newpassword"}
        )

        assert response.status_code == 200
        assert "nulstillet" in response.text.lower()

        # Verify old password no longer works, new does
        assert db_module.authenticate_user("resetuser3", "oldpassword") is None
        assert db_module.authenticate_user("resetuser3", "newpassword") is not None

    def test_reset_password_validates_password_length(self, client, db_module):
        """Reset password should require minimum password length."""
        import hashlib
        from datetime import datetime, timedelta

        user_id = db_module.create_user("resetuser4", "oldpass")
        token = "shorttoken123"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        db_module.create_password_reset_token(user_id, token_hash, expires_at)

        response = client.post(
            f"/budget/reset-password/{token}",
            data={"password": "short", "password_confirm": "short"}
        )

        assert response.status_code == 200
        assert "mindst 6" in response.text

    def test_reset_password_validates_password_match(self, client, db_module):
        """Reset password should require passwords to match."""
        import hashlib
        from datetime import datetime, timedelta

        user_id = db_module.create_user("resetuser5", "oldpass")
        token = "matchtoken123"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        db_module.create_password_reset_token(user_id, token_hash, expires_at)

        response = client.post(
            f"/budget/reset-password/{token}",
            data={"password": "password1", "password_confirm": "password2"}
        )

        assert response.status_code == 200
        assert "matcher ikke" in response.text

    def test_reset_password_token_single_use(self, client, db_module):
        """Reset password token should only work once."""
        import hashlib
        from datetime import datetime, timedelta

        user_id = db_module.create_user("resetuser6", "oldpass")
        token = "singleusetoken"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        db_module.create_password_reset_token(user_id, token_hash, expires_at)

        # First use should work
        response1 = client.post(
            f"/budget/reset-password/{token}",
            data={"password": "newpass1", "password_confirm": "newpass1"}
        )
        assert "nulstillet" in response1.text.lower()

        # Second use should fail
        response2 = client.post(
            f"/budget/reset-password/{token}",
            data={"password": "newpass2", "password_confirm": "newpass2"}
        )
        assert "ugyldigt" in response2.text.lower() or "udløbet" in response2.text.lower()


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
                "income_name_0": "Alice",
                "income_amount_0": "35000",
                "income_frequency_0": "monthly",
                "income_name_1": "Bob",
                "income_amount_1": "28000",
                "income_frequency_1": "monthly"
            },
            follow_redirects=False
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/budget/"

    def test_update_income_with_frequency(self, authenticated_client, db_module):
        """POST to income with different frequencies should save correctly."""
        response = authenticated_client.post(
            "/budget/income",
            data={
                "income_name_0": "Monthly Salary",
                "income_amount_0": "30000",
                "income_frequency_0": "monthly",
                "income_name_1": "Quarterly Bonus",
                "income_amount_1": "9000",
                "income_frequency_1": "quarterly",
                "income_name_2": "Annual Bonus",
                "income_amount_2": "24000",
                "income_frequency_2": "yearly"
            },
            follow_redirects=False
        )

        assert response.status_code == 303
        # Verify income was saved with correct frequencies
        user_id = authenticated_client.user_id
        incomes = db_module.get_all_income(user_id)

        monthly = next((i for i in incomes if i.person == "Monthly Salary"), None)
        quarterly = next((i for i in incomes if i.person == "Quarterly Bonus"), None)
        yearly = next((i for i in incomes if i.person == "Annual Bonus"), None)

        assert monthly is not None and monthly.frequency == "monthly"
        assert quarterly is not None and quarterly.frequency == "quarterly"
        assert quarterly.monthly_amount == 3000  # 9000 / 3
        assert yearly is not None and yearly.frequency == "yearly"
        assert yearly.monthly_amount == 2000  # 24000 / 12

    def test_update_income_semiannual(self, authenticated_client, db_module):
        """POST to income with semi-annual frequency should work."""
        response = authenticated_client.post(
            "/budget/income",
            data={
                "income_name_0": "Semi-Annual Payment",
                "income_amount_0": "12000",
                "income_frequency_0": "semi-annual"
            },
            follow_redirects=False
        )

        assert response.status_code == 303
        user_id = authenticated_client.user_id
        incomes = db_module.get_all_income(user_id)
        semiannual = next((i for i in incomes if i.person == "Semi-Annual Payment"), None)

        assert semiannual is not None
        assert semiannual.frequency == "semi-annual"
        assert semiannual.monthly_amount == 2000  # 12000 / 6


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

    def test_add_expense_quarterly(self, authenticated_client, db_module):
        """POST to add expense with quarterly frequency should work."""
        response = authenticated_client.post(
            "/budget/expenses/add",
            data={
                "name": "Quarterly Expense",
                "category": "Forbrug",
                "amount": "2400",
                "frequency": "quarterly"
            },
            follow_redirects=False
        )

        assert response.status_code == 303
        # Verify expense was created with correct frequency
        user_id = authenticated_client.user_id
        expenses = db_module.get_all_expenses(user_id)
        quarterly_expense = next((e for e in expenses if e.name == "Quarterly Expense"), None)
        assert quarterly_expense is not None
        assert quarterly_expense.frequency == "quarterly"
        assert quarterly_expense.monthly_amount == 800  # 2400 / 3

    def test_add_expense_semiannual(self, authenticated_client, db_module):
        """POST to add expense with semi-annual frequency should work."""
        response = authenticated_client.post(
            "/budget/expenses/add",
            data={
                "name": "Semi-Annual Expense",
                "category": "Transport",
                "amount": "4500",
                "frequency": "semi-annual"
            },
            follow_redirects=False
        )

        assert response.status_code == 303
        # Verify expense was created with correct frequency
        user_id = authenticated_client.user_id
        expenses = db_module.get_all_expenses(user_id)
        semiannual_expense = next((e for e in expenses if e.name == "Semi-Annual Expense"), None)
        assert semiannual_expense is not None
        assert semiannual_expense.frequency == "semi-annual"
        assert semiannual_expense.monthly_amount == 750  # 4500 / 6

    def test_add_expense_invalid_frequency(self, authenticated_client):
        """POST to add expense with invalid frequency should reject."""
        response = authenticated_client.post(
            "/budget/expenses/add",
            data={
                "name": "Invalid Expense",
                "category": "Bolig",
                "amount": "1000",
                "frequency": "invalid_frequency"
            },
            follow_redirects=False
        )

        # Should reject with 400 Bad Request (invalid frequency validation)
        assert response.status_code == 400

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
        category_id = db_module.add_category(authenticated_client.user_id, "OldName", "old-icon")

        response = authenticated_client.post(
            f"/budget/categories/{category_id}/edit",
            data={"name": "NewName", "icon": "new-icon"},
            follow_redirects=False
        )

        assert response.status_code == 303

    def test_delete_category(self, authenticated_client, db_module):
        """POST to delete unused category should remove it."""
        category_id = db_module.add_category(authenticated_client.user_id, "Unused", "icon")

        response = authenticated_client.post(
            f"/budget/categories/{category_id}/delete",
            follow_redirects=False
        )

        assert response.status_code == 303


class TestAccountEndpoints:
    """Tests for account management endpoints."""

    def test_add_account_json_success(self, authenticated_client):
        """POST to add-json should create account and return JSON."""
        response = authenticated_client.post(
            "/budget/accounts/add-json",
            data={"name": "Nordea"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["name"] == "Nordea"

    def test_add_account_json_duplicate(self, authenticated_client):
        """POST to add-json with duplicate name should return error."""
        authenticated_client.post(
            "/budget/accounts/add-json",
            data={"name": "Nordea"},
        )
        response = authenticated_client.post(
            "/budget/accounts/add-json",
            data={"name": "Nordea"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "findes allerede" in data["error"]

    def test_add_account_json_empty_name(self, authenticated_client):
        """POST to add-json with empty name should return error."""
        response = authenticated_client.post(
            "/budget/accounts/add-json",
            data={"name": "   "},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    def test_add_account_json_requires_auth(self, client):
        """POST to add-json without auth should return 401."""
        response = client.post(
            "/budget/accounts/add-json",
            data={"name": "Test"},
        )

        assert response.status_code in (401, 303)

    def test_add_account_json_demo_mode(self, client):
        """POST to add-json in demo mode should be rejected."""
        # Enter demo mode (sets demo cookie)
        client.get("/budget/demo")
        client.cookies.set("budget_session", "demo")
        response = client.post(
            "/budget/accounts/add-json",
            data={"name": "Test"},
        )

        # Demo mode: check_auth passes but is_demo_mode blocks with 403
        assert response.status_code == 403
        assert response.json()["success"] is False


class TestHelpers:
    """Tests for helper functions."""

    def test_format_currency(self):
        """format_currency should format Danish-style currency with 2 decimal places."""
        from src.api import format_currency

        assert format_currency(1000) == "1.000,00 kr"
        assert format_currency(1000000) == "1.000.000,00 kr"
        assert format_currency(0) == "0,00 kr"


class TestFeedback:
    """Tests for feedback functionality."""

    def test_feedback_page_requires_auth(self, client):
        """Feedback page should require authentication."""
        response = client.get("/budget/feedback", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/budget/login"

    def test_feedback_page_loads(self, authenticated_client):
        """Feedback page should load for authenticated users."""
        response = authenticated_client.get("/budget/feedback")
        assert response.status_code == 200
        assert "feedback" in response.text.lower()

    def test_feedback_submit_requires_auth(self, client):
        """Feedback submission should require authentication."""
        response = client.post(
            "/budget/feedback",
            data={
                "feedback_type": "feedback",
                "description": "This is test feedback.",
            },
            follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/budget/login"

    def test_feedback_submit_validates_description(self, authenticated_client):
        """Feedback should require minimum description length."""
        response = authenticated_client.post(
            "/budget/feedback",
            data={
                "feedback_type": "feedback",
                "description": "Short",
            }
        )
        assert response.status_code == 200
        assert "mindst 10 tegn" in response.text

    def test_feedback_submit_success(self, authenticated_client):
        """Valid feedback should be accepted."""
        response = authenticated_client.post(
            "/budget/feedback",
            data={
                "feedback_type": "feature",
                "description": "This is a valid feature request with enough text.",
            }
        )
        assert response.status_code == 200
        assert "Tak for din feedback" in response.text

    def test_feedback_honeypot_rejects_bots(self, authenticated_client):
        """Honeypot field should silently reject bot submissions."""
        response = authenticated_client.post(
            "/budget/feedback",
            data={
                "feedback_type": "feedback",
                "description": "This is spam from a bot.",
                "website": "http://spam.com",  # Honeypot filled = bot
            }
        )
        # Should pretend success to fool bots
        assert response.status_code == 200
        assert "Tak for din feedback" in response.text

    def test_help_page_has_feedback_link(self, authenticated_client):
        """Help page should have a link to feedback."""
        response = authenticated_client.get("/budget/help")
        assert response.status_code == 200
        assert "/budget/feedback" in response.text

    def test_help_page_shows_donation_section(self, authenticated_client):
        """Help page should show donation buttons for authenticated users."""
        response = authenticated_client.get("/budget/help")
        assert response.status_code == 200
        assert "Køb mig en kaffe" in response.text
        assert "buy.stripe.com" in response.text
        assert "10 kr." in response.text
        assert "25 kr." in response.text
        assert "50 kr." in response.text

    def test_help_page_hides_donation_in_demo_mode(self, client):
        """Help page should not show donation buttons in demo mode."""
        client.get("/budget/demo")
        response = client.get("/budget/help")
        assert response.status_code == 200
        assert "Støt projektet" not in response.text


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


class TestAmountParsing:
    """Tests for Danish amount format parsing."""

    def test_parse_danish_amount_with_comma(self):
        """Should parse comma as decimal separator."""
        from src.api import parse_danish_amount
        assert parse_danish_amount("1234,50") == 1234.50

    def test_parse_danish_amount_with_thousands_and_comma(self):
        """Should handle thousands separator with comma."""
        from src.api import parse_danish_amount
        assert parse_danish_amount("1.234,50") == 1234.50
        assert parse_danish_amount("12.345,67") == 12345.67

    def test_parse_danish_amount_whole_number(self):
        """Should handle whole numbers."""
        from src.api import parse_danish_amount
        assert parse_danish_amount("1234") == 1234.00

    def test_parse_danish_amount_single_decimal(self):
        """Should handle single decimal place."""
        from src.api import parse_danish_amount
        assert parse_danish_amount("1234,5") == 1234.50

    def test_parse_danish_amount_with_whitespace(self):
        """Should trim whitespace."""
        from src.api import parse_danish_amount
        assert parse_danish_amount("  1234,50  ") == 1234.50

    def test_parse_danish_amount_zero(self):
        """Should handle zero."""
        from src.api import parse_danish_amount
        assert parse_danish_amount("0") == 0.00
        assert parse_danish_amount("0,00") == 0.00

    def test_parse_danish_amount_invalid_empty(self):
        """Should raise ValueError for empty string."""
        from src.api import parse_danish_amount
        with pytest.raises(ValueError):
            parse_danish_amount("")

    def test_parse_danish_amount_invalid_text(self):
        """Should raise ValueError for invalid text."""
        from src.api import parse_danish_amount
        with pytest.raises(ValueError):
            parse_danish_amount("abc")

    def test_parse_danish_amount_invalid_multiple_commas(self):
        """Should raise ValueError for multiple commas."""
        from src.api import parse_danish_amount
        with pytest.raises(ValueError):
            parse_danish_amount("12,34,56")


class TestCurrencyFormatting:
    """Tests for currency display formatting."""

    def test_format_currency_with_decimals(self):
        """Should format with 2 decimal places."""
        from src.api import format_currency
        assert format_currency(1234.50) == "1.234,50 kr"

    def test_format_currency_whole_number(self):
        """Should show .00 for whole numbers."""
        from src.api import format_currency
        assert format_currency(1234.0) == "1.234,00 kr"

    def test_format_currency_large_amount(self):
        """Should handle large amounts with thousands separator."""
        from src.api import format_currency
        assert format_currency(123456.78) == "123.456,78 kr"

    def test_format_currency_small_amount(self):
        """Should handle amounts less than 1 kr."""
        from src.api import format_currency
        assert format_currency(0.50) == "0,50 kr"

    def test_format_currency_zero(self):
        """Should format zero correctly."""
        from src.api import format_currency
        assert format_currency(0.00) == "0,00 kr"


class TestExpensesWithDecimals:
    """Tests for decimal amounts in expenses."""

    def test_add_expense_with_decimals(self, authenticated_client, db_module):
        """Should accept decimal amounts in Danish format."""
        response = authenticated_client.post(
            "/budget/expenses/add",
            data={
                "name": "Test Expense",
                "category": "Bolig",
                "amount": "1234,50",
                "frequency": "monthly"
            },
            follow_redirects=False
        )
        assert response.status_code == 303

    def test_add_expense_with_thousands_separator(self, authenticated_client, db_module):
        """Should accept thousands separator."""
        response = authenticated_client.post(
            "/budget/expenses/add",
            data={
                "name": "Expensive Item",
                "category": "Bolig",
                "amount": "12.345,67",
                "frequency": "monthly"
            },
            follow_redirects=False
        )
        assert response.status_code == 303

    def test_add_expense_rejects_invalid_format(self, authenticated_client, db_module):
        """Should reject invalid amount format."""
        response = authenticated_client.post(
            "/budget/expenses/add",
            data={
                "name": "Test",
                "category": "Bolig",
                "amount": "abc",
                "frequency": "monthly"
            }
        )
        assert response.status_code == 400

    def test_add_expense_rejects_negative_amount(self, authenticated_client, db_module):
        """Should reject negative amounts."""
        response = authenticated_client.post(
            "/budget/expenses/add",
            data={
                "name": "Test",
                "category": "Bolig",
                "amount": "-100,00",
                "frequency": "monthly"
            }
        )
        assert response.status_code == 400

    def test_edit_expense_with_decimals(self, authenticated_client, db_module):
        """Should accept decimal amounts when editing."""
        # First create an expense
        add_response = authenticated_client.post(
            "/budget/expenses/add",
            data={
                "name": "Test Expense",
                "category": "Bolig",
                "amount": "1000,00",
                "frequency": "monthly"
            }
        )
        # Get the expense ID from the database
        from src.database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM expenses ORDER BY id DESC LIMIT 1")
        expense_id = cur.fetchone()[0]
        conn.close()

        # Now edit it
        response = authenticated_client.post(
            f"/budget/expenses/{expense_id}/edit",
            data={
                "name": "Updated Expense",
                "category": "Bolig",
                "amount": "1234,56",
                "frequency": "monthly"
            },
            follow_redirects=False
        )
        assert response.status_code == 303
