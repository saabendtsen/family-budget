"""SQLite database operations for Family Budget."""

import hashlib
import os
import secrets
import sqlite3
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

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


# =============================================================================
# Email encryption (AES-256-GCM with PIN-derived key)
# =============================================================================

def _derive_email_key(pin: str, salt: bytes) -> bytes:
    """Derive AES-256 key from PIN + salt using PBKDF2."""
    return hashlib.pbkdf2_hmac('sha256', pin.encode(), salt, PBKDF2_ITERATIONS)


def hash_email(email: str) -> str:
    """Hash email for lookup (case-insensitive). Returns hex string."""
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()


def encrypt_email(email: str, pin: str) -> tuple[str, str, str]:
    """Encrypt email with PIN. Returns (encrypted_hex, salt_hex, email_hash)."""
    email_lower = email.lower().strip()
    salt = secrets.token_bytes(32)
    key = _derive_email_key(pin, salt)

    # AES-GCM encryption
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, email_lower.encode(), None)

    # Store nonce + ciphertext together
    encrypted = nonce + ciphertext
    email_hash = hash_email(email_lower)

    return encrypted.hex(), salt.hex(), email_hash


def decrypt_email(encrypted_hex: str, salt_hex: str, pin: str) -> Optional[str]:
    """Decrypt email with PIN. Returns email or None if PIN is wrong."""
    try:
        encrypted = bytes.fromhex(encrypted_hex)
        salt = bytes.fromhex(salt_hex)
        key = _derive_email_key(pin, salt)

        # Extract nonce and ciphertext
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]

        # AES-GCM decryption
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
    except Exception:
        # Wrong PIN or corrupted data
        return None

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
    ("Person 1", 28000),
    ("Person 2", 22000),
]

DEMO_EXPENSES = [
    # (name, category, amount, frequency)
    ("Husleje/boliglån", "Bolig", 12000, "monthly"),
    ("Ejendomsskat", "Bolig", 18000, "yearly"),
    ("Varme", "Forbrug", 800, "monthly"),
    ("El", "Forbrug", 600, "monthly"),
    ("Vand", "Forbrug", 400, "monthly"),
    ("Internet", "Forbrug", 299, "monthly"),
    ("Bil - lån", "Transport", 2500, "monthly"),
    ("Benzin", "Transport", 1500, "monthly"),
    ("Vægtafgift", "Transport", 3600, "yearly"),
    ("Bilforsikring", "Transport", 6000, "yearly"),
    ("Institution", "Børn", 3200, "monthly"),
    ("Fritidsaktiviteter", "Børn", 400, "monthly"),
    ("Dagligvarer", "Mad", 6000, "monthly"),
    ("Indboforsikring", "Forsikring", 1800, "yearly"),
    ("Ulykkesforsikring", "Forsikring", 1200, "yearly"),
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
    amount_monthly: float

    @property
    def monthly_amount(self) -> float:
        """Alias for amount_monthly for template compatibility."""
        return self.amount_monthly


@dataclass
class Expense:
    id: int
    user_id: int
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


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    salt: str
    email_encrypted: str = None
    email_salt: str = None
    email_hash: str = None

    def has_email(self) -> bool:
        """Check if user has an encrypted email set."""
        return bool(self.email_encrypted and self.email_salt)


@dataclass
class PasswordResetToken:
    id: int
    user_id: int
    token_hash: str
    expires_at: str
    used: bool = False


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
            amount_monthly REAL NOT NULL DEFAULT 0,
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
            frequency TEXT NOT NULL CHECK(frequency IN ('monthly', 'yearly')),
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
            email_encrypted TEXT,
            email_salt TEXT,
            email_hash TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Migration: Add encrypted email columns to existing databases
    cur.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cur.fetchall()]
    if "email_encrypted" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN email_encrypted TEXT")
    if "email_salt" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN email_salt TEXT")
    if "email_hash" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN email_hash TEXT")
    # Clean up old email column if it exists (from previous version)
    if "email" in columns:
        # SQLite doesn't support DROP COLUMN in older versions, so we leave it
        # but stop using it. New code will not read/write this column.
        pass

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
        "SELECT id, user_id, person, amount_monthly FROM income WHERE user_id = ? ORDER BY person",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [Income(**dict(row)) for row in rows]


def add_income(user_id: int, person: str, amount: float) -> int:
    """Add income entry for a user. Returns the new income ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO income (user_id, person, amount_monthly) VALUES (?, ?, ?)",
        (user_id, person, amount)
    )
    income_id = cur.lastrowid
    conn.commit()
    conn.close()
    return income_id


def update_income(user_id: int, person: str, amount: float):
    """Update or insert income for a user.

    Uses INSERT ... ON CONFLICT for atomic upsert operation,
    which is thread-safe and more efficient than check-then-act.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO income (user_id, person, amount_monthly)
           VALUES (?, ?, ?)
           ON CONFLICT(user_id, person) DO UPDATE SET amount_monthly = excluded.amount_monthly""",
        (user_id, person, amount)
    )
    conn.commit()
    conn.close()


def get_total_income(user_id: int) -> float:
    """Get total monthly income for a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(SUM(amount_monthly), 0) FROM income WHERE user_id = ?",
        (user_id,)
    )
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
    return Expense(**dict(row)) if row else None


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
    """Get total monthly expenses for a user (yearly divided by 12)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(
            CASE
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

def create_user(
    username: str,
    password: str,
    email: str = None,
    email_pin: str = None
) -> Optional[int]:
    """Create a new user. Returns user ID or None if username exists.

    If email is provided, email_pin must also be provided. The email will be
    encrypted with the PIN and cannot be recovered without it.

    Uses try/except for IntegrityError to handle race conditions where
    another process might insert the same username between check and insert.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Hash password
    password_hash, salt = hash_password(password)

    # Encrypt email if provided
    email_encrypted = None
    email_salt = None
    email_hash_val = None
    if email and email_pin:
        email_encrypted, email_salt, email_hash_val = encrypt_email(email, email_pin)

    try:
        cur.execute(
            """INSERT INTO users
               (username, password_hash, salt, email_encrypted, email_salt, email_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username, password_hash, salt, email_encrypted, email_salt, email_hash_val)
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
        """SELECT id, username, password_hash, salt,
                  email_encrypted, email_salt, email_hash
           FROM users WHERE username = ?""",
        (username,)
    )
    row = cur.fetchone()
    conn.close()
    return User(**dict(row)) if row else None


def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email hash (for lookup).

    Note: The actual email is encrypted and requires PIN to decrypt.
    This function finds the user by their email hash.
    """
    email_hash_val = hash_email(email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, username, password_hash, salt,
                  email_encrypted, email_salt, email_hash
           FROM users WHERE email_hash = ?""",
        (email_hash_val,)
    )
    row = cur.fetchone()
    conn.close()
    return User(**dict(row)) if row else None


def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, username, password_hash, salt,
                  email_encrypted, email_salt, email_hash
           FROM users WHERE id = ?""",
        (user_id,)
    )
    row = cur.fetchone()
    conn.close()
    return User(**dict(row)) if row else None


def update_user_email(user_id: int, email: str, email_pin: str):
    """Update encrypted email for a user.

    Both email and email_pin are required. The email will be encrypted
    with the PIN and cannot be recovered without it.
    """
    if not email or not email_pin:
        # Clear email if not provided
        conn = get_connection()
        conn.execute(
            "UPDATE users SET email_encrypted = NULL, email_salt = NULL, email_hash = NULL WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        conn.close()
        return

    email_encrypted, email_salt, email_hash_val = encrypt_email(email, email_pin)
    conn = get_connection()
    conn.execute(
        """UPDATE users
           SET email_encrypted = ?, email_salt = ?, email_hash = ?
           WHERE id = ?""",
        (email_encrypted, email_salt, email_hash_val, user_id)
    )
    conn.commit()
    conn.close()


def update_user_password(user_id: int, password: str):
    """Update password for a user."""
    password_hash, salt = hash_password(password)
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
        (password_hash, salt, user_id)
    )
    conn.commit()
    conn.close()


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user. Returns User if successful, None otherwise."""
    user = get_user_by_username(username)
    if user and verify_password(password, user.password_hash, user.salt):
        return user
    return None


def get_user_count() -> int:
    """Get total number of registered users."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    conn.close()
    return count


# =============================================================================
# Password reset token operations
# =============================================================================

def create_password_reset_token(user_id: int, token_hash: str, expires_at: str) -> int:
    """Create a password reset token. Returns token ID."""
    conn = get_connection()
    cur = conn.cursor()
    # Invalidate any existing tokens for this user
    cur.execute("UPDATE password_reset_tokens SET used = 1 WHERE user_id = ?", (user_id,))
    # Create new token
    cur.execute(
        """INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
           VALUES (?, ?, ?)""",
        (user_id, token_hash, expires_at)
    )
    token_id = cur.lastrowid
    conn.commit()
    conn.close()
    return token_id


def get_valid_reset_token(token_hash: str) -> Optional[PasswordResetToken]:
    """Get a valid (unused, not expired) reset token."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, user_id, token_hash, expires_at, used
           FROM password_reset_tokens
           WHERE token_hash = ? AND used = 0 AND expires_at > datetime('now')""",
        (token_hash,)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return PasswordResetToken(
            id=row[0], user_id=row[1], token_hash=row[2],
            expires_at=row[3], used=bool(row[4])
        )
    return None


def mark_reset_token_used(token_id: int):
    """Mark a reset token as used."""
    conn = get_connection()
    conn.execute("UPDATE password_reset_tokens SET used = 1 WHERE id = ?", (token_id,))
    conn.commit()
    conn.close()


# =============================================================================
# Demo data functions (returns in-memory data, not from database)
# =============================================================================

def get_demo_income() -> list[Income]:
    """Get demo income data."""
    return [Income(id=i+1, user_id=0, person=person, amount_monthly=amount)
            for i, (person, amount) in enumerate(DEMO_INCOME)]


def get_demo_total_income() -> float:
    """Get total demo income."""
    return sum(amount for _, amount in DEMO_INCOME)


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
