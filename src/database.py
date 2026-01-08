"""SQLite database operations for Family Budget."""

import hashlib
import os
import secrets
import sqlite3
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

DB_PATH = Path(os.environ.get("BUDGET_DB_PATH", Path(__file__).parent.parent / "data" / "budget.db"))


# =============================================================================
# Password hashing (using PBKDF2 for simplicity, no extra dependencies)
# =============================================================================

# OWASP recommends 600,000 iterations for PBKDF2-HMAC-SHA256 (2023)
# https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
PBKDF2_ITERATIONS = 600_000


def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """Hash password with PBKDF2. Returns (hash, salt) as hex strings."""
    if salt is None:
        salt = secrets.token_bytes(32)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, PBKDF2_ITERATIONS)
    return hashed.hex(), salt.hex()


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password against stored hash."""
    new_hash, _ = hash_password(password, bytes.fromhex(salt))
    return secrets.compare_digest(new_hash, stored_hash)

# Pre-defined categories with icons
DEFAULT_CATEGORIES = [
    ("Bolig", "house"),
    ("Forbrug", "zap"),
    ("Transport", "car"),
    ("Børn", "baby"),
    ("Mad", "utensils"),
    ("Forsikring", "shield"),
    ("Abonnementer", "tv"),
    ("Opsparing", "piggy-bank"),
    ("Andet", "more-horizontal"),
]

# Demo data - typical Danish household budget
DEMO_INCOME = [
    # (person, amount, frequency)
    ("Person 1", 28000, "monthly"),
    ("Person 2", 22000, "monthly"),
    ("Bonus", 30000, "semi-annual"),  # Example: semi-annual bonus
]

DEMO_EXPENSES = [
    # (name, category, amount, frequency)
    ("Husleje/boliglån", "Bolig", 12000, "monthly"),
    ("Ejendomsskat", "Bolig", 18000, "yearly"),
    ("Varme", "Forbrug", 800, "monthly"),
    ("El", "Forbrug", 600, "monthly"),
    ("Vand", "Forbrug", 2400, "quarterly"),  # Example: quarterly water bill
    ("Internet", "Forbrug", 299, "monthly"),
    ("Bil - lån", "Transport", 2500, "monthly"),
    ("Benzin", "Transport", 1500, "monthly"),
    ("Vægtafgift", "Transport", 3600, "yearly"),
    ("Bilforsikring", "Transport", 6000, "yearly"),
    ("Bilservice", "Transport", 4500, "semi-annual"),  # Example: semi-annual service
    ("Institution", "Børn", 3200, "monthly"),
    ("Fritidsaktiviteter", "Børn", 400, "monthly"),
    ("Dagligvarer", "Mad", 6000, "monthly"),
    ("Indboforsikring", "Forsikring", 1800, "yearly"),
    ("Ulykkesforsikring", "Forsikring", 1200, "yearly"),
    ("Tandlægeforsikring", "Forsikring", 600, "quarterly"),  # Example: quarterly dental
    ("Netflix", "Abonnementer", 129, "monthly"),
    ("Spotify", "Abonnementer", 99, "monthly"),
    ("Fitness", "Abonnementer", 299, "monthly"),
    ("Opsparing", "Opsparing", 3000, "monthly"),
    ("Telefon", "Andet", 199, "monthly"),
]


@dataclass
class Income:
    id: int
    user_id: int
    person: str
    amount: float
    frequency: str = 'monthly'  # 'monthly', 'quarterly', 'semi-annual', or 'yearly'

    @property
    def monthly_amount(self) -> float:
        """Return the monthly equivalent amount."""
        divisors = {'monthly': 1, 'quarterly': 3, 'semi-annual': 6, 'yearly': 12}
        return self.amount / divisors.get(self.frequency, 1)


@dataclass
class Expense:
    id: int
    user_id: int
    name: str
    category: str
    amount: float
    frequency: str  # 'monthly', 'quarterly', 'semi-annual', or 'yearly'

    @property
    def monthly_amount(self) -> float:
        """Return the monthly equivalent amount."""
        divisors = {'monthly': 1, 'quarterly': 3, 'semi-annual': 6, 'yearly': 12}
        return self.amount / divisors.get(self.frequency, 1)


@dataclass
class Category:
    id: int
    name: str
    icon: str


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    salt: str


def get_connection() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_db_directory():
    """Ensure database directory exists. Called once at init."""
    DB_PATH.parent.mkdir(exist_ok=True)


def init_db():
    """Initialize database with schema and default data."""
    ensure_db_directory()
    conn = get_connection()
    cur = conn.cursor()

    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            person TEXT NOT NULL,
            amount REAL NOT NULL DEFAULT 0,
            frequency TEXT NOT NULL DEFAULT 'monthly' CHECK(frequency IN ('monthly', 'quarterly', 'semi-annual', 'yearly')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, person)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT NOT NULL CHECK(frequency IN ('monthly', 'quarterly', 'semi-annual', 'yearly')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # Migration: Add last_login column to existing databases
    cur.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cur.fetchall()]
    if "last_login" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")

    # Migration: Add frequency column to income table
    cur.execute("PRAGMA table_info(income)")
    income_columns = [col[1] for col in cur.fetchall()]
    if "frequency" not in income_columns:
        if "amount_monthly" in income_columns:
            # Old schema: migrate from amount_monthly to amount + frequency
            cur.execute("ALTER TABLE income ADD COLUMN amount REAL NOT NULL DEFAULT 0")
            cur.execute("ALTER TABLE income ADD COLUMN frequency TEXT NOT NULL DEFAULT 'monthly'")
            cur.execute("UPDATE income SET amount = amount_monthly")
        else:
            # Schema has amount but no frequency: just add frequency column
            cur.execute("ALTER TABLE income ADD COLUMN frequency TEXT NOT NULL DEFAULT 'monthly'")

    # Insert default categories
    for name, icon in DEFAULT_CATEGORIES:
        cur.execute(
            "INSERT OR IGNORE INTO categories (name, icon) VALUES (?, ?)",
            (name, icon)
        )

    conn.commit()
    conn.close()


# =============================================================================
# Income operations
# =============================================================================

def get_all_income(user_id: int) -> list[Income]:
    """Get all income entries for a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, person, amount, frequency FROM income WHERE user_id = ? ORDER BY person",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [Income(**dict(row)) for row in rows]


def add_income(user_id: int, person: str, amount: float, frequency: str = 'monthly') -> int:
    """Add income entry for a user. Returns the new income ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO income (user_id, person, amount, frequency) VALUES (?, ?, ?, ?)",
        (user_id, person, amount, frequency)
    )
    income_id = cur.lastrowid
    conn.commit()
    conn.close()
    return income_id


def update_income(user_id: int, person: str, amount: float, frequency: str = 'monthly'):
    """Update or insert income for a user.

    Uses INSERT ... ON CONFLICT for atomic upsert operation,
    which is thread-safe and more efficient than check-then-act.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO income (user_id, person, amount, frequency)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(user_id, person) DO UPDATE SET amount = excluded.amount, frequency = excluded.frequency""",
        (user_id, person, amount, frequency)
    )
    conn.commit()
    conn.close()


def get_total_income(user_id: int) -> float:
    """Get total monthly income for a user (converted to monthly equivalent)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(
            CASE
                WHEN frequency = 'monthly' THEN amount
                WHEN frequency = 'quarterly' THEN amount / 3
                WHEN frequency = 'semi-annual' THEN amount / 6
                WHEN frequency = 'yearly' THEN amount / 12
                ELSE amount
            END
        ), 0) FROM income WHERE user_id = ?
    """, (user_id,))
    total = cur.fetchone()[0]
    conn.close()
    return total


def delete_all_income(user_id: int):
    """Delete all income entries for a user."""
    conn = get_connection()
    conn.execute("DELETE FROM income WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# =============================================================================
# Expense operations
# =============================================================================

def get_all_expenses(user_id: int) -> list[Expense]:
    """Get all expenses for a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, user_id, name, category, amount, frequency
        FROM expenses
        WHERE user_id = ?
        ORDER BY category, name
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [Expense(**dict(row)) for row in rows]


def get_expense_by_id(expense_id: int, user_id: int) -> Optional[Expense]:
    """Get a specific expense for a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, name, category, amount, frequency FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id)
    )
    row = cur.fetchone()
    conn.close()
    return Expense(**dict(row)) if row is not None else None


def add_expense(user_id: int, name: str, category: str, amount: float, frequency: str) -> int:
    """Add a new expense for a user. Returns the new expense ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO expenses (user_id, name, category, amount, frequency)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, name, category, amount, frequency)
    )
    expense_id = cur.lastrowid
    conn.commit()
    conn.close()
    return expense_id


def update_expense(expense_id: int, user_id: int, name: str, category: str, amount: float, frequency: str):
    """Update an existing expense for a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE expenses
           SET name = ?, category = ?, amount = ?, frequency = ?
           WHERE id = ? AND user_id = ?""",
        (name, category, amount, frequency, expense_id, user_id)
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id: int, user_id: int):
    """Delete an expense for a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
    conn.commit()
    conn.close()


def get_total_monthly_expenses(user_id: int) -> float:
    """Get total monthly expenses for a user (converted to monthly equivalent)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(
            CASE
                WHEN frequency = 'monthly' THEN amount
                WHEN frequency = 'quarterly' THEN amount / 3
                WHEN frequency = 'semi-annual' THEN amount / 6
                WHEN frequency = 'yearly' THEN amount / 12
                ELSE amount
            END
        ), 0) FROM expenses WHERE user_id = ?
    """, (user_id,))
    total = cur.fetchone()[0]
    conn.close()
    return total


def get_expenses_by_category(user_id: int) -> dict[str, list[Expense]]:
    """Get expenses grouped by category for a user."""
    expenses = get_all_expenses(user_id)
    grouped = {}
    for exp in expenses:
        if exp.category not in grouped:
            grouped[exp.category] = []
        grouped[exp.category].append(exp)
    return grouped


def get_category_totals(user_id: int) -> dict[str, float]:
    """Get total monthly amount per category for a user."""
    expenses = get_all_expenses(user_id)
    totals = {}
    for exp in expenses:
        if exp.category not in totals:
            totals[exp.category] = 0
        totals[exp.category] += exp.monthly_amount
    return totals


# =============================================================================
# Category operations
# =============================================================================

def get_all_categories() -> list[Category]:
    """Get all categories."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, icon FROM categories ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [Category(**dict(row)) for row in rows]


def get_category_by_id(category_id: int) -> Optional[Category]:
    """Get a specific category."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, icon FROM categories WHERE id = ?", (category_id,))
    row = cur.fetchone()
    conn.close()
    return Category(**dict(row)) if row else None


def add_category(name: str, icon: str) -> int:
    """Add a new category. Returns the new category ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO categories (name, icon) VALUES (?, ?)", (name, icon))
    category_id = cur.lastrowid
    conn.commit()
    conn.close()
    return category_id


def update_category(category_id: int, name: str, icon: str):
    """Update an existing category."""
    conn = get_connection()
    cur = conn.cursor()
    # Also update expenses that use this category
    old_cat = get_category_by_id(category_id)
    if old_cat and old_cat.name != name:
        cur.execute(
            "UPDATE expenses SET category = ? WHERE category = ?",
            (name, old_cat.name)
        )
    cur.execute(
        "UPDATE categories SET name = ?, icon = ? WHERE id = ?",
        (name, icon, category_id)
    )
    conn.commit()
    conn.close()


def delete_category(category_id: int) -> bool:
    """Delete a category. Returns False if category is in use.

    Uses a single connection to avoid race conditions between
    checking for usage and deleting.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Get category name first
        cur.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
        row = cur.fetchone()
        if not row:
            return False

        cat_name = row[0]

        # Check if any expenses use this category
        cur.execute("SELECT COUNT(*) FROM expenses WHERE category = ?", (cat_name,))
        count = cur.fetchone()[0]
        if count > 0:
            return False

        # Delete the category
        cur.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def get_category_usage_count(category_name: str) -> int:
    """Get number of expenses using a category."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM expenses WHERE category = ?", (category_name,))
    count = cur.fetchone()[0]
    conn.close()
    return count


# =============================================================================
# User operations
# =============================================================================

def create_user(username: str, password: str) -> Optional[int]:
    """Create a new user. Returns user ID or None if username exists.

    Uses try/except for IntegrityError to handle race conditions where
    another process might insert the same username between check and insert.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Hash password and attempt to create user
    # The UNIQUE constraint on username will raise IntegrityError if duplicate
    password_hash, salt = hash_password(password)
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, password_hash, salt)
        )
        user_id = cur.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        # Username already exists (caught via UNIQUE constraint)
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, password_hash, salt FROM users WHERE username = ?",
        (username,)
    )
    row = cur.fetchone()
    conn.close()
    return User(**dict(row)) if row else None


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user. Returns User if successful, None otherwise."""
    user = get_user_by_username(username)
    if user and verify_password(password, user.password_hash, user.salt):
        return user
    return None


def update_last_login(user_id: int):
    """Update last_login timestamp for a user."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
        (user_id,)
    )
    conn.commit()
    conn.close()


def get_user_count() -> int:
    """Get total number of registered users."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    conn.close()
    return count


# =============================================================================
# Demo data functions (returns in-memory data, not from database)
# =============================================================================

def get_demo_income() -> list[Income]:
    """Get demo income data."""
    return [Income(id=i+1, user_id=0, person=person, amount=amount, frequency=freq)
            for i, (person, amount, freq) in enumerate(DEMO_INCOME)]


def get_demo_total_income() -> float:
    """Get total demo income (converted to monthly equivalent)."""
    return sum(inc.monthly_amount for inc in get_demo_income())


def get_demo_expenses() -> list[Expense]:
    """Get demo expense data."""
    return [Expense(id=i+1, user_id=0, name=name, category=cat, amount=amount, frequency=freq)
            for i, (name, cat, amount, freq) in enumerate(DEMO_EXPENSES)]


def get_demo_expenses_by_category() -> dict[str, list[Expense]]:
    """Get demo expenses grouped by category."""
    expenses = get_demo_expenses()
    grouped = {}
    for exp in expenses:
        if exp.category not in grouped:
            grouped[exp.category] = []
        grouped[exp.category].append(exp)
    return grouped


def get_demo_category_totals() -> dict[str, float]:
    """Get demo total monthly amount per category."""
    expenses = get_demo_expenses()
    totals = {}
    for exp in expenses:
        if exp.category not in totals:
            totals[exp.category] = 0
        totals[exp.category] += exp.monthly_amount
    return totals


def get_demo_total_expenses() -> float:
    """Get demo total monthly expenses."""
    return sum(exp.monthly_amount for exp in get_demo_expenses())


# Initialize database when run directly (for testing/setup)
# For production, api.py calls init_db() explicitly at startup
if __name__ == "__main__":
    init_db()
