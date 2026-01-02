"""Unit tests for database operations."""

import pytest


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_hash_and_salt(self, db_module):
        """hash_password should return a hash and salt."""
        password_hash, salt = db_module.hash_password("testpassword")

        assert password_hash is not None
        assert salt is not None
        assert len(password_hash) == 64  # SHA-256 hex = 64 chars
        assert len(salt) == 64  # 32 bytes hex = 64 chars

    def test_hash_password_with_same_salt_produces_same_hash(self, db_module):
        """Same password + salt should produce identical hash."""
        _, salt = db_module.hash_password("testpassword")
        salt_bytes = bytes.fromhex(salt)

        hash1, _ = db_module.hash_password("testpassword", salt_bytes)
        hash2, _ = db_module.hash_password("testpassword", salt_bytes)

        assert hash1 == hash2

    def test_different_passwords_produce_different_hashes(self, db_module):
        """Different passwords should produce different hashes."""
        _, salt = db_module.hash_password("password1")
        salt_bytes = bytes.fromhex(salt)

        hash1, _ = db_module.hash_password("password1", salt_bytes)
        hash2, _ = db_module.hash_password("password2", salt_bytes)

        assert hash1 != hash2

    def test_verify_password_correct(self, db_module):
        """verify_password should return True for correct password."""
        password_hash, salt = db_module.hash_password("mypassword")

        assert db_module.verify_password("mypassword", password_hash, salt) is True

    def test_verify_password_incorrect(self, db_module):
        """verify_password should return False for wrong password."""
        password_hash, salt = db_module.hash_password("mypassword")

        assert db_module.verify_password("wrongpassword", password_hash, salt) is False


class TestIncomeOperations:
    """Tests for income CRUD operations."""

    def test_get_all_income_returns_default_entries(self, db_module):
        """Database should have default income entries for Soeren and Anne."""
        incomes = db_module.get_all_income()

        assert len(incomes) == 2
        persons = {i.person for i in incomes}
        assert "Søren" in persons
        assert "Anne" in persons

    def test_update_income(self, db_module):
        """update_income should change the amount."""
        db_module.update_income("Søren", 35000)

        income = db_module.get_income_by_person("Søren")
        assert income.amount_monthly == 35000

    def test_get_total_income(self, db_module):
        """get_total_income should sum all income entries."""
        db_module.update_income("Søren", 30000)
        db_module.update_income("Anne", 25000)

        total = db_module.get_total_income()
        assert total == 55000

    def test_get_income_by_person_not_found(self, db_module):
        """get_income_by_person should return None for unknown person."""
        income = db_module.get_income_by_person("Unknown")
        assert income is None


class TestExpenseOperations:
    """Tests for expense CRUD operations."""

    def test_add_expense(self, db_module):
        """add_expense should create a new expense."""
        expense_id = db_module.add_expense("Husleje", "Bolig", 10000, "monthly")

        assert expense_id is not None
        expense = db_module.get_expense_by_id(expense_id)
        assert expense.name == "Husleje"
        assert expense.category == "Bolig"
        assert expense.amount == 10000
        assert expense.frequency == "monthly"

    def test_expense_monthly_amount_for_monthly(self, db_module):
        """monthly_amount should return same amount for monthly expenses."""
        expense_id = db_module.add_expense("Test", "Bolig", 1000, "monthly")
        expense = db_module.get_expense_by_id(expense_id)

        assert expense.monthly_amount == 1000

    def test_expense_monthly_amount_for_yearly(self, db_module):
        """monthly_amount should divide by 12 for yearly expenses."""
        expense_id = db_module.add_expense("Forsikring", "Forsikring", 12000, "yearly")
        expense = db_module.get_expense_by_id(expense_id)

        assert expense.monthly_amount == 1000  # 12000 / 12

    def test_update_expense(self, db_module):
        """update_expense should modify existing expense."""
        expense_id = db_module.add_expense("Old Name", "Bolig", 5000, "monthly")
        db_module.update_expense(expense_id, "New Name", "Transport", 6000, "yearly")

        expense = db_module.get_expense_by_id(expense_id)
        assert expense.name == "New Name"
        assert expense.category == "Transport"
        assert expense.amount == 6000
        assert expense.frequency == "yearly"

    def test_delete_expense(self, db_module):
        """delete_expense should remove the expense."""
        expense_id = db_module.add_expense("To Delete", "Bolig", 1000, "monthly")
        db_module.delete_expense(expense_id)

        expense = db_module.get_expense_by_id(expense_id)
        assert expense is None

    def test_get_total_monthly_expenses(self, db_module):
        """get_total_monthly_expenses should calculate correct total."""
        db_module.add_expense("Monthly", "Bolig", 1000, "monthly")
        db_module.add_expense("Yearly", "Bolig", 1200, "yearly")  # 100/month

        total = db_module.get_total_monthly_expenses()
        assert total == 1100  # 1000 + 100

    def test_get_expenses_by_category(self, db_module):
        """get_expenses_by_category should group expenses correctly."""
        db_module.add_expense("Expense 1", "Bolig", 1000, "monthly")
        db_module.add_expense("Expense 2", "Bolig", 2000, "monthly")
        db_module.add_expense("Expense 3", "Transport", 500, "monthly")

        grouped = db_module.get_expenses_by_category()

        assert len(grouped["Bolig"]) == 2
        assert len(grouped["Transport"]) == 1

    def test_get_category_totals(self, db_module):
        """get_category_totals should sum monthly amounts per category."""
        db_module.add_expense("Rent", "Bolig", 10000, "monthly")
        db_module.add_expense("Tax", "Bolig", 12000, "yearly")  # 1000/month

        totals = db_module.get_category_totals()

        assert totals["Bolig"] == 11000  # 10000 + 1000


class TestCategoryOperations:
    """Tests for category CRUD operations."""

    def test_default_categories_exist(self, db_module):
        """Database should have default categories."""
        categories = db_module.get_all_categories()

        names = {c.name for c in categories}
        assert "Bolig" in names
        assert "Transport" in names
        assert "Mad" in names

    def test_add_category(self, db_module):
        """add_category should create a new category."""
        category_id = db_module.add_category("Custom", "star")

        category = db_module.get_category_by_id(category_id)
        assert category.name == "Custom"
        assert category.icon == "star"

    def test_update_category(self, db_module):
        """update_category should modify existing category."""
        category_id = db_module.add_category("OldName", "old-icon")
        db_module.update_category(category_id, "NewName", "new-icon")

        category = db_module.get_category_by_id(category_id)
        assert category.name == "NewName"
        assert category.icon == "new-icon"

    def test_update_category_updates_expenses(self, db_module):
        """Renaming a category should update expenses using it."""
        category_id = db_module.add_category("OldCat", "icon")
        db_module.add_expense("Test Expense", "OldCat", 100, "monthly")

        db_module.update_category(category_id, "NewCat", "icon")

        expenses = db_module.get_all_expenses()
        expense = next(e for e in expenses if e.name == "Test Expense")
        assert expense.category == "NewCat"

    def test_delete_category_not_in_use(self, db_module):
        """delete_category should work when category is not in use."""
        category_id = db_module.add_category("Unused", "icon")

        result = db_module.delete_category(category_id)

        assert result is True
        assert db_module.get_category_by_id(category_id) is None

    def test_delete_category_in_use_fails(self, db_module):
        """delete_category should fail when category has expenses."""
        category_id = db_module.add_category("InUse", "icon")
        db_module.add_expense("Uses Category", "InUse", 100, "monthly")

        result = db_module.delete_category(category_id)

        assert result is False
        assert db_module.get_category_by_id(category_id) is not None

    def test_get_category_usage_count(self, db_module):
        """get_category_usage_count should return correct count."""
        db_module.add_category("TestCat", "icon")
        db_module.add_expense("Exp1", "TestCat", 100, "monthly")
        db_module.add_expense("Exp2", "TestCat", 200, "monthly")

        count = db_module.get_category_usage_count("TestCat")
        assert count == 2


class TestUserOperations:
    """Tests for user CRUD and authentication."""

    def test_create_user(self, db_module):
        """create_user should create a new user."""
        user_id = db_module.create_user("newuser", "password123")

        assert user_id is not None
        user = db_module.get_user_by_username("newuser")
        assert user is not None
        assert user.username == "newuser"

    def test_create_user_duplicate_fails(self, db_module):
        """create_user should return None for duplicate username."""
        db_module.create_user("duplicate", "pass1")
        result = db_module.create_user("duplicate", "pass2")

        assert result is None

    def test_create_user_case_insensitive(self, db_module):
        """Username should be case-insensitive for uniqueness."""
        db_module.create_user("TestUser", "pass1")
        result = db_module.create_user("testuser", "pass2")

        assert result is None

    def test_authenticate_user_correct(self, db_module):
        """authenticate_user should return user for correct credentials."""
        db_module.create_user("authuser", "correctpass")

        user = db_module.authenticate_user("authuser", "correctpass")

        assert user is not None
        assert user.username == "authuser"

    def test_authenticate_user_wrong_password(self, db_module):
        """authenticate_user should return None for wrong password."""
        db_module.create_user("authuser", "correctpass")

        user = db_module.authenticate_user("authuser", "wrongpass")

        assert user is None

    def test_authenticate_user_unknown_user(self, db_module):
        """authenticate_user should return None for unknown user."""
        user = db_module.authenticate_user("unknown", "anypass")

        assert user is None

    def test_get_user_count(self, db_module):
        """get_user_count should return correct count."""
        initial_count = db_module.get_user_count()

        db_module.create_user("user1", "pass")
        db_module.create_user("user2", "pass")

        assert db_module.get_user_count() == initial_count + 2


class TestDemoData:
    """Tests for demo data functions."""

    def test_get_demo_income(self, db_module):
        """get_demo_income should return demo income entries."""
        incomes = db_module.get_demo_income()

        assert len(incomes) == 2
        assert all(i.amount_monthly > 0 for i in incomes)

    def test_get_demo_total_income(self, db_module):
        """get_demo_total_income should return positive total."""
        total = db_module.get_demo_total_income()

        assert total > 0
        assert total == sum(i.amount_monthly for i in db_module.get_demo_income())

    def test_get_demo_expenses(self, db_module):
        """get_demo_expenses should return demo expenses."""
        expenses = db_module.get_demo_expenses()

        assert len(expenses) > 0
        assert all(e.amount > 0 for e in expenses)

    def test_get_demo_total_expenses(self, db_module):
        """get_demo_total_expenses should return positive total."""
        total = db_module.get_demo_total_expenses()

        assert total > 0

    def test_demo_data_is_read_only(self, db_module):
        """Demo data should be independent of database state."""
        # Add real expense
        db_module.add_expense("Real Expense", "Bolig", 99999, "monthly")

        # Demo data should not include it
        demo_expenses = db_module.get_demo_expenses()
        names = {e.name for e in demo_expenses}

        assert "Real Expense" not in names
