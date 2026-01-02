"""SQLite database operations for Family Budget."""

import sqlite3
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

DB_PATH = Path(__file__).parent.parent / "data" / "budget.db"

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


@dataclass
class Income:
    id: int
    person: str
    amount_monthly: float


@dataclass
class Expense:
    id: int
    name: str
    category: str
    amount: float
    frequency: str  # 'monthly' or 'yearly'

    @property
    def monthly_amount(self) -> float:
        """Return the monthly equivalent amount."""
        if self.frequency == "yearly":
            return self.amount / 12
        return self.amount


@dataclass
class Category:
    id: int
    name: str
    icon: str


def get_connection() -> sqlite3.Connection:
    """Get database connection."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with schema and default data."""
    conn = get_connection()
    cur = conn.cursor()

    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT NOT NULL UNIQUE,
            amount_monthly REAL NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT NOT NULL CHECK(frequency IN ('monthly', 'yearly')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT
        )
    """)

    # Insert default incomes (Søren and Anne)
    cur.execute("""
        INSERT OR IGNORE INTO income (person, amount_monthly)
        VALUES ('Søren', 0), ('Anne', 0)
    """)

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

def get_all_income() -> list[Income]:
    """Get all income entries."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, person, amount_monthly FROM income ORDER BY person")
    rows = cur.fetchall()
    conn.close()
    return [Income(**dict(row)) for row in rows]


def get_income_by_person(person: str) -> Optional[Income]:
    """Get income for a specific person."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, person, amount_monthly FROM income WHERE person = ?",
        (person,)
    )
    row = cur.fetchone()
    conn.close()
    return Income(**dict(row)) if row else None


def update_income(person: str, amount: float):
    """Update income for a person."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE income SET amount_monthly = ? WHERE person = ?",
        (amount, person)
    )
    conn.commit()
    conn.close()


def get_total_income() -> float:
    """Get total monthly income."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount_monthly), 0) FROM income")
    total = cur.fetchone()[0]
    conn.close()
    return total


# =============================================================================
# Expense operations
# =============================================================================

def get_all_expenses() -> list[Expense]:
    """Get all expenses."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, category, amount, frequency
        FROM expenses
        ORDER BY category, name
    """)
    rows = cur.fetchall()
    conn.close()
    return [Expense(**dict(row)) for row in rows]


def get_expense_by_id(expense_id: int) -> Optional[Expense]:
    """Get a specific expense."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, category, amount, frequency FROM expenses WHERE id = ?",
        (expense_id,)
    )
    row = cur.fetchone()
    conn.close()
    return Expense(**dict(row)) if row else None


def add_expense(name: str, category: str, amount: float, frequency: str) -> int:
    """Add a new expense. Returns the new expense ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO expenses (name, category, amount, frequency)
           VALUES (?, ?, ?, ?)""",
        (name, category, amount, frequency)
    )
    expense_id = cur.lastrowid
    conn.commit()
    conn.close()
    return expense_id


def update_expense(expense_id: int, name: str, category: str, amount: float, frequency: str):
    """Update an existing expense."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE expenses
           SET name = ?, category = ?, amount = ?, frequency = ?
           WHERE id = ?""",
        (name, category, amount, frequency, expense_id)
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id: int):
    """Delete an expense."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


def get_total_monthly_expenses() -> float:
    """Get total monthly expenses (yearly divided by 12)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(
            CASE
                WHEN frequency = 'yearly' THEN amount / 12
                ELSE amount
            END
        ), 0) FROM expenses
    """)
    total = cur.fetchone()[0]
    conn.close()
    return total


def get_expenses_by_category() -> dict[str, list[Expense]]:
    """Get expenses grouped by category."""
    expenses = get_all_expenses()
    grouped = {}
    for exp in expenses:
        if exp.category not in grouped:
            grouped[exp.category] = []
        grouped[exp.category].append(exp)
    return grouped


def get_category_totals() -> dict[str, float]:
    """Get total monthly amount per category."""
    expenses = get_all_expenses()
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
    """Delete a category. Returns False if category is in use."""
    conn = get_connection()
    cur = conn.cursor()
    # Check if any expenses use this category
    cat = get_category_by_id(category_id)
    if cat:
        cur.execute("SELECT COUNT(*) FROM expenses WHERE category = ?", (cat.name,))
        count = cur.fetchone()[0]
        if count > 0:
            conn.close()
            return False
    cur.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()
    return True


def get_category_usage_count(category_name: str) -> int:
    """Get number of expenses using a category."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM expenses WHERE category = ?", (category_name,))
    count = cur.fetchone()[0]
    conn.close()
    return count


# Initialize database on import
init_db()
