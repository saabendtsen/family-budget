# Source Code Module - AI Agent Guide

AI-optimized navigation for the `src/` module.

## Files Overview

| File | Lines | Purpose | When to Read |
|------|-------|---------|--------------|
| `api.py` | 1,256 | All FastAPI routes, middleware, business logic | Adding/modifying routes |
| `database.py` | 981 | SQLite operations, CRUD, security | Database queries |
| `__init__.py` | 8 | Package metadata, version info | Version management |

## Architecture Note

This codebase uses a **deliberately simple architecture** with all routes in one file (`api.py`).

**Rationale**: For a single-purpose application with <50 routes, the simplicity of having all routes in one file outweighs the benefits of splitting into multiple modules. This makes it easier to:
- Search for routes (Ctrl+F works)
- Understand request flow
- Avoid circular imports
- Keep related code together

**See**: `docs/adr/004-single-file-architecture.md` for full rationale.

**When to split**: If routes exceed 100 or distinct feature domains emerge (e.g., admin panel, API v2), consider splitting.

---

## Quick Navigation

### Finding Routes
**Instead of reading all 1,256 lines of api.py:**
1. Read `src/API-REFERENCE.md`
2. Find your route in the index
3. Jump to line number

**Example**: Need to modify login?
- Read `API-REFERENCE.md` → POST /budget/login is at line 261
- Jump to `api.py:261`

### Finding Database Functions
**Instead of searching 981 lines of database.py:**
- Use the index below
- Functions grouped by category
- Jump directly to line number

---

## Database Functions Index

### Password & Security

| Function | Line | Purpose |
|----------|------|---------|
| `hash_password(password, salt=None)` | 23 | Hash password with PBKDF2-HMAC-SHA256 (600k iterations) |
| `verify_password(password, stored_hash, salt)` | 31 | Verify password against stored hash (constant-time) |
| `hash_email(email)` | 41 | Hash email with SHA-256 for privacy-preserving lookup |

**Security Notes**:
- PBKDF2: 600,000 iterations (OWASP 2023 standard)
- Salt: 32 random bytes
- Email hashing: Case-insensitive, never stored plaintext
- See: `docs/adr/001-pbkdf2-password-hashing.md`

---

### User Management

| Function | Line | Purpose |
|----------|------|---------|
| `create_user(username, password, email=None)` | 724 | Create new user with hashed password |
| `get_user_by_username(username)` | 769 | Look up user by username |
| `get_user_by_email(email)` | 783 | Look up user by email hash |
| `get_user_by_id(user_id)` | 802 | Look up user by ID |
| `update_user_email(user_id, email)` | 816 | Update user email (hashes automatically) |
| `update_user_password(user_id, password)` | 839 | Update password with new hash |
| `update_last_login(user_id)` | 859 | Update last_login timestamp to current time |
| `get_user_count()` | 870 | Get total number of users |

**User Model** (dataclass, line 134):
```python
@dataclass
class User:
    id: int
    username: str
    password_hash: str
    salt: str
    email_hash: Optional[str] = None
    last_login: Optional[str] = None
```

**Notes**:
- Email is optional (can be NULL)
- Passwords always hashed, never stored plaintext
- Last login updated on successful login

---

### Password Reset Tokens

| Function | Line | Purpose |
|----------|------|---------|
| `create_password_reset_token(user_id, token_hash, expires_at)` | 884 | Create password reset token |
| `get_valid_reset_token(token_hash)` | 902 | Get token if valid and not expired |
| `mark_token_as_used(token_id)` | Line not listed | Mark token as used (implicit in update) |

**PasswordResetToken Model** (dataclass, line 146):
```python
@dataclass
class PasswordResetToken:
    id: int
    user_id: int
    token_hash: str
    expires_at: str
    used: int  # 0 or 1 (boolean)
```

**Token Security**:
- Tokens hashed with SHA-256
- 1 hour expiry
- Single-use (marked as used after reset)
- See password reset flow: `api.py:430-530`

---

### Income Management

| Function | Line | Purpose |
|----------|------|---------|
| `get_all_income(user_id)` | 344 | Get all income sources for user |
| `add_income(user_id, person, amount, frequency)` | 357 | Add income source |
| `update_income(user_id, person, amount, frequency)` | 371 | Update income (used by add, handles upsert) |
| `get_total_income(user_id)` | 389 | Calculate total monthly income |
| `delete_all_income(user_id)` | 409 | Delete all income for user |

**Income Model** (dataclass, line 98):
```python
@dataclass
class Income:
    id: int
    user_id: int
    person: str
    amount: float
    frequency: str  # 'monthly', 'quarterly', 'semi-annual', 'yearly'

    @property
    def monthly_amount(self) -> float:
        """Convert to monthly amount based on frequency."""
        # Calculation logic...
```

**Frequencies**:
- `monthly` - No conversion (×1)
- `quarterly` - ÷3 to get monthly
- `semi-annual` - ÷6 to get monthly
- `yearly` - ÷12 to get monthly

**Pattern**: Income uses "upsert" pattern - add_income creates or updates based on person name.

---

### Expense Management

| Function | Line | Purpose |
|----------|------|---------|
| `get_all_expenses(user_id)` | 421 | Get all expenses for user |
| `get_expense_by_id(expense_id, user_id)` | 436 | Get single expense (with user_id check) |
| `add_expense(user_id, name, category, amount, frequency)` | 449 | Create new expense |
| `update_expense(expense_id, user_id, name, category, amount, frequency)` | 464 | Update existing expense |
| `delete_expense(expense_id, user_id)` | 478 | Delete expense |
| `get_total_monthly_expenses(user_id)` | 487 | Calculate total monthly expenses |
| `get_expenses_by_category(user_id)` | 507 | Group expenses by category |
| `get_category_totals(user_id)` | 518 | Sum expenses per category (monthly) |

**Expense Model** (dataclass, line 111):
```python
@dataclass
class Expense:
    id: int
    user_id: int
    name: str
    category: str
    amount: float
    frequency: str  # 'monthly', 'quarterly', 'semi-annual', 'yearly'

    @property
    def monthly_amount(self) -> float:
        """Convert to monthly amount based on frequency."""
        # Same calculation as Income
```

**Frequency Conversion**: Same as Income (monthly/quarterly/semi-annual/yearly)

**Security**: All operations require `user_id` to prevent cross-user access.

---

### Category Management

| Function | Line | Purpose |
|----------|------|---------|
| `get_all_categories(user_id)` | 533 | Get all categories for user |
| `get_category_by_id(category_id)` | 546 | Get single category (no user_id check - global) |
| `add_category(user_id, name, icon)` | 556 | Create new category |
| `update_category(category_id, user_id, name, icon)` | 570 | Update category |
| `delete_category(category_id, user_id)` | 604 | Delete category if unused |
| `get_category_usage_count(category_name, user_id)` | 644 | Count expenses using category |
| `ensure_default_categories(user_id)` | 662 | Add default categories for new user |

**Category Model** (dataclass, line 124):
```python
@dataclass
class Category:
    id: int
    user_id: int
    name: str
    icon: str  # Lucide icon name
```

**Default Categories** (line 51):
```python
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
```

**Icons**: Uses Lucide icon names (see https://lucide.dev/)

**Deletion Rules**: Categories can only be deleted if no expenses use them.

---

### Demo Mode Functions

| Function | Line | Purpose |
|----------|------|---------|
| `get_demo_income()` | 934 | Return hardcoded demo income data |
| `get_demo_total_income()` | 940 | Calculate demo income total |
| `get_demo_expenses()` | 945 | Return hardcoded demo expense data |
| `get_demo_expenses_by_category()` | 951 | Group demo expenses by category |
| `get_demo_category_totals()` | 962 | Sum demo expenses per category |
| `get_demo_total_expenses()` | 973 | Calculate demo expense total |

**Demo Data**:
- Income: `DEMO_INCOME` (line 64) - 3 income sources
- Expenses: `DEMO_EXPENSES` (line 72) - 24 typical Danish household expenses
- Categories: Uses `DEFAULT_CATEGORIES`

**Purpose**: Allow users to explore app without creating account.

**Implementation**: See `docs/adr/007-demo-mode-design.md`

---

### Database Utilities

| Function | Line | Purpose |
|----------|------|---------|
| `get_connection()` | 160 | Get SQLite connection with Row factory |
| `ensure_db_directory()` | 167 | Create data/ directory if missing |
| `init_db()` | 180 | Initialize database schema |

**Database Path**: `data/budget.db` (configurable via `BUDGET_DB_PATH` env var)

**Connection Pattern**:
```python
with get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    # ...
```

**Schema**: See `init_db()` at line 180 for complete table definitions.

---

## Common Tasks

### Adding a New Route

**Don't read this file. Instead:**
→ Read `docs/guides/adding-new-route.md`

That guide provides step-by-step instructions with code templates.

### Adding a Database Function

**Pattern**:
1. Define dataclass model (if needed)
2. Add function with user_id parameter
3. Use parameterized queries (never string interpolation)
4. Always commit on write operations
5. Include user_id in WHERE clause for user data

**Example**:
```python
def get_user_items(user_id: int) -> list[Item]:
    """Get all items for user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM items WHERE user_id = ?",
            (user_id,)
        )
        return [
            Item(id=row['id'], user_id=row['user_id'], name=row['name'])
            for row in cursor.fetchall()
        ]
```

**See**: `docs/guides/database-operations.md`

### Understanding Security Decisions

**Password Hashing**: Why PBKDF2 with 600k iterations?
→ Read `docs/adr/001-pbkdf2-password-hashing.md`

**Sessions**: Why session-based auth instead of JWT?
→ Read `docs/adr/002-session-based-authentication.md`

**Database**: Why SQLite?
→ Read `docs/adr/003-sqlite-database-choice.md`

---

## Database Schema

**Tables**:
1. `users` - User accounts
2. `income` - Income sources
3. `expenses` - Expenses with categories
4. `categories` - Expense categories with icons
5. `password_reset_tokens` - Password reset tokens

**Relationships**:
- All tables reference `users.id` via `user_id` foreign key
- Expenses reference categories by name (not ID)
- Categories are per-user (not shared)

**Full schema**: See `database.py:180-221` (init_db function)

---

## Security Patterns

### User Data Isolation

**CRITICAL**: Always include `user_id` in WHERE clause for user data.

```python
# ✅ CORRECT
cursor.execute(
    "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
    (expense_id, user_id)
)

# ❌ WRONG - Security vulnerability!
cursor.execute(
    "SELECT * FROM expenses WHERE id = ?",
    (expense_id,)
)
```

**Applies to**: income, expenses, categories

### SQL Injection Prevention

**Always use parameterized queries:**

```python
# ✅ CORRECT
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))

# ❌ WRONG - SQL injection vulnerability!
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

### Password Security

- Passwords: PBKDF2-HMAC-SHA256, 600k iterations
- Salts: 32 random bytes per password
- Verification: Constant-time comparison
- Never logged or exposed

**See**: `PATTERNS.md` → Security Patterns

---

## Related Documentation

- **API Routes**: `src/API-REFERENCE.md` - All routes with line numbers
- **Coding Patterns**: `PATTERNS.md` - Patterns and standards
- **Architecture Decisions**: `docs/adr/` - Why certain choices were made
- **Implementation Guides**: `docs/guides/` - How to implement common tasks

---

## Statistics

| Metric | Count |
|--------|-------|
| Total Functions | 40+ |
| User Management | 8 functions |
| Income Management | 5 functions |
| Expense Management | 8 functions |
| Category Management | 6 functions |
| Demo Mode | 6 functions |
| Security | 3 functions |
| Utilities | 3 functions |
| Database Tables | 5 tables |

---

## Navigation Tips for AI Agents

**Finding a specific function**:
1. Use the index above
2. Jump to line number
3. Read function and surrounding context

**Understanding a feature**:
1. Start with `API-REFERENCE.md` to find routes
2. Read route handler to see which DB functions are called
3. Read DB function to understand data access

**Making a change**:
1. Read relevant guide in `docs/guides/`
2. Follow the pattern in `PATTERNS.md`
3. Check ADR in `docs/adr/` if architectural question
4. Update documentation when done

**Performance tip**: Don't read entire files. Use the indexes to jump directly to relevant code.
