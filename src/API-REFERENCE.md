# API Reference - FastAPI Routes

Quick reference for all routes in `src/api.py`. Jump directly to line numbers to see implementation.

## Quick Navigation

- [Authentication](#authentication) - Login, register, password reset (8 routes)
- [Dashboard](#dashboard) - Main budget overview (3 routes)
- [Income Management](#income-management) - Income sources (2 routes)
- [Expense Management](#expense-management) - Expense tracking (4 routes)
- [Category Management](#category-management) - Category CRUD (4 routes)
- [Static Pages](#static-pages) - Help, privacy, feedback (4 routes)
- [API Endpoints](#api-endpoints) - JSON data endpoints (2 routes)
- [Settings](#settings) - User settings (2 routes)

---

## Authentication

### GET /budget/login

**Location**: `src/api.py:253-258`

**Purpose**: Display login page

**Auth**: None (public)

**Template**: `templates/login.html`

**Returns**: HTML login page

**Related**:
- POST /budget/login (form submission)
- Pattern: `PATTERNS.md` → Form Input Pattern

**Notes**: Redirects to dashboard if already authenticated

---

### POST /budget/login

**Location**: `src/api.py:261-290`

**Purpose**: Process login form submission

**Form Data**:
- `username` (str, required)
- `password` (str, required)

**Returns**:
- Success: Redirect to `/budget/` with session cookie
- Failure: Login page with error message "Forkert brugernavn eller adgangskode"

**Security**:
- Rate limited: 5 attempts per 5 minutes (see `RateLimitMiddleware` at line 39)
- Password verified with `database.authenticate_user()` (calls `verify_password()`)
- Session token hashed with SHA-256
- Cookie: httponly, secure, samesite=lax, 30-day expiry

**Database Functions**:
- `db.authenticate_user()` - Verify credentials
- `db.update_last_login()` - Update timestamp (line 859)

**Testing**: `tests/test_api.py::TestAuthentication::test_login_success`

---

### GET /budget/register

**Location**: `src/api.py:293-298`

**Purpose**: Display registration page

**Auth**: None (public)

**Template**: `templates/register.html`

**Returns**: HTML registration page

**Notes**: Redirects to dashboard if already authenticated

---

### POST /budget/register

**Location**: `src/api.py:301-427`

**Purpose**: Create new user account

**Form Data**:
- `username` (str, required) - 3-50 chars, alphanumeric + underscore
- `password` (str, required) - Min 8 chars
- `confirm_password` (str, required) - Must match password
- `email` (str, optional) - Valid email format

**Validation**:
- Username: 3-50 characters, alphanumeric + underscore
- Password: Minimum 8 characters
- Passwords must match
- Email: Valid format (if provided)
- Username must be unique

**Returns**:
- Success: Redirect to `/budget/` with auto-login
- Failure: Registration page with error message

**Database Functions**:
- `db.create_user()` - Create user with PBKDF2 hashed password (line 724)
- `db.ensure_default_categories()` - Add default categories for new user (line 662)

**Security**:
- Password hashed with PBKDF2-HMAC-SHA256 (600k iterations)
- Email hashed with SHA-256 for privacy
- See: `docs/adr/001-pbkdf2-password-hashing.md`

---

### GET /budget/forgot-password

**Location**: `src/api.py:430-436`

**Purpose**: Display forgot password page

**Auth**: None (public)

**Template**: `templates/forgot-password.html`

**Returns**: HTML password reset request page

---

### POST /budget/forgot-password

**Location**: `src/api.py:438-468`

**Purpose**: Send password reset email

**Form Data**:
- `email` (str, required)

**Returns**:
- Always: Success message (to prevent email enumeration)
- If email exists: Sends reset email with token link

**Email**:
- Subject: "Nulstil din adgangskode - Family Budget"
- Contains: Reset link with token (1 hour expiry)
- SMTP config required (see `CLAUDE.md` → SMTP Configuration)

**Database Functions**:
- `db.get_user_by_email()` - Look up user by email hash (line 783)
- `db.create_password_reset_token()` - Generate single-use token (line 884)

**Security**:
- Token: SHA-256 hashed, 1 hour expiry, single-use
- No email enumeration (always shows success)

---

### GET /budget/reset-password/{token}

**Location**: `src/api.py:471-488`

**Purpose**: Display password reset form

**Auth**: None (public, but requires valid token)

**URL Parameters**:
- `token` (str) - Password reset token from email

**Template**: `templates/reset-password.html`

**Returns**:
- Valid token: Password reset form
- Invalid/expired token: Error page

**Database Functions**:
- `db.get_valid_reset_token()` - Validate token (line 902)

---

### POST /budget/reset-password/{token}

**Location**: `src/api.py:490-530`

**Purpose**: Update password with reset token

**URL Parameters**:
- `token` (str) - Password reset token

**Form Data**:
- `password` (str, required) - Min 8 chars
- `confirm_password` (str, required) - Must match

**Returns**:
- Success: Redirect to login with success message
- Failure: Reset form with error message

**Database Functions**:
- `db.get_valid_reset_token()` - Validate token (line 902)
- `db.update_user_password()` - Hash and update password (line 839)
- Token marked as used after successful reset

---

## Dashboard

### GET /budget/demo

**Location**: `src/api.py:533-546`

**Purpose**: Demo mode with sample data (read-only)

**Auth**: None (public)

**Template**: `templates/dashboard.html`

**Returns**: Dashboard with hardcoded demo data

**Data**:
- Demo income: `database.DEMO_INCOME` (line 64)
- Demo expenses: `database.DEMO_EXPENSES` (line 72)
- See: `docs/adr/007-demo-mode-design.md`

**Notes**: Sets special demo session cookie (`DEMO_SESSION_ID`)

---

### GET /budget/logout

**Location**: `src/api.py:548-565`

**Purpose**: Clear session and logout

**Auth**: None (but only useful if logged in)

**Returns**: Redirect to login page with cleared session cookie

**Actions**:
- Removes session from `SESSIONS` dict
- Deletes session cookie
- Persists session changes to file

---

### GET /budget/ and GET /budget

**Location**: `src/api.py:567-617`

**Purpose**: Main dashboard - budget overview

**Auth**: Required (redirects to `/budget/login` if not authenticated)

**Template**: `templates/dashboard.html`

**Returns**: Dashboard with income, expenses, categories, and calculations

**Context Data**:
- `income_list` - All income sources with monthly amounts
- `expenses` - All expenses
- `categories` - Category totals
- `total_income` - Monthly income total
- `total_expenses` - Monthly expense total
- `leftover` - Income minus expenses
- `chart_data` - Category breakdown for chart

**Database Functions**:
- `db.get_all_income()` - Get income sources (line 344)
- `db.get_total_income()` - Calculate monthly total (line 389)
- `db.get_all_expenses()` - Get expenses (line 421)
- `db.get_category_totals()` - Sum by category (line 518)
- `db.get_total_monthly_expenses()` - Calculate total (line 487)

**Calculations**:
- All frequencies converted to monthly amounts
- Leftover = total_income - total_expenses

---

## Income Management

### GET /budget/income

**Location**: `src/api.py:619-637`

**Purpose**: Income management page

**Auth**: Required

**Template**: `templates/income.html`

**Returns**: Income page with all income sources and form

**Context Data**:
- `income_list` - All income sources for user
- `total_income` - Monthly total

**Database Functions**:
- `db.get_all_income()` - Get all income (line 344)
- `db.get_total_income()` - Calculate total (line 389)

---

### POST /budget/income

**Location**: `src/api.py:639-682`

**Purpose**: Add or update income sources (handles multiple)

**Auth**: Required

**Form Data** (dynamic keys):
- `person_{i}` (str) - Person name
- `amount_{i}` (str) - Amount in Danish format (e.g., "25.000,50")
- `frequency_{i}` (str) - monthly/quarterly/semi-annual/yearly

**Returns**: Redirect to `/budget/income`

**Process**:
1. Delete all existing income for user
2. Parse form data (grouped by index `{i}`)
3. Add each non-empty income source
4. Danish amount parsing: `parse_danish_amount()` (line 104)

**Database Functions**:
- `db.delete_all_income()` - Clear existing (line 409)
- `db.add_income()` - Add new source (line 357)

**Helper Functions**:
- `parse_danish_amount()` - Converts "25.000,50" → 25000.50 (line 104)

**Pattern**: See `PATTERNS.md` → Danish Amount Parsing

---

## Expense Management

### GET /budget/expenses

**Location**: `src/api.py:685-720`

**Purpose**: Expense management page

**Auth**: Required

**Template**: `templates/expenses.html`

**Returns**: Expense list with add/edit modals

**Context Data**:
- `expenses` - All expenses for user
- `categories` - Available categories
- `total_monthly` - Total monthly expenses

**Database Functions**:
- `db.get_all_expenses()` - Get all expenses (line 421)
- `db.get_all_categories()` - Get categories (line 533)
- `db.get_total_monthly_expenses()` - Calculate total (line 487)

---

### POST /budget/expenses/add

**Location**: `src/api.py:722-758`

**Purpose**: Create new expense

**Auth**: Required

**Form Data**:
- `name` (str, required) - Expense name
- `category` (str, required) - Category name
- `amount` (str, required) - Amount in Danish format
- `frequency` (str, required) - monthly/quarterly/semi-annual/yearly

**Returns**: Redirect to `/budget/expenses`

**Database Functions**:
- `db.add_expense()` - Create expense (line 449)

**Validation**:
- Amount parsed with `parse_danish_amount()`
- All fields required

---

### POST /budget/expenses/{expense_id}/delete

**Location**: `src/api.py:760-775`

**Purpose**: Delete expense

**Auth**: Required

**URL Parameters**:
- `expense_id` (int) - Expense to delete

**Returns**: Redirect to `/budget/expenses`

**Database Functions**:
- `db.delete_expense()` - Delete by ID and user_id (line 478)

**Security**: User ID check prevents deleting other users' expenses

---

### POST /budget/expenses/{expense_id}/edit

**Location**: `src/api.py:777-817`

**Purpose**: Update existing expense

**Auth**: Required

**URL Parameters**:
- `expense_id` (int) - Expense to update

**Form Data**:
- `name` (str, required)
- `category` (str, required)
- `amount` (str, required)
- `frequency` (str, required)

**Returns**: Redirect to `/budget/expenses`

**Database Functions**:
- `db.update_expense()` - Update expense (line 464)

**Security**: User ID check prevents editing other users' expenses

---

## Category Management

### GET /budget/categories

**Location**: `src/api.py:820-848`

**Purpose**: Category management page

**Auth**: Required

**Template**: `templates/categories.html`

**Returns**: Category list with add/edit modals

**Context Data**:
- `categories` - All categories for user

**Database Functions**:
- `db.get_all_categories()` - Get categories (line 533)

---

### POST /budget/categories/add

**Location**: `src/api.py:850-872`

**Purpose**: Create new category

**Auth**: Required

**Form Data**:
- `name` (str, required) - Category name
- `icon` (str, required) - Lucide icon name

**Returns**: Redirect to `/budget/categories`

**Database Functions**:
- `db.add_category()` - Create category (line 556)

**Icons**: Uses Lucide icons (see `templates/base.html` for available icons)

---

### POST /budget/categories/{category_id}/edit

**Location**: `src/api.py:874-900`

**Purpose**: Update existing category

**Auth**: Required

**URL Parameters**:
- `category_id` (int) - Category to update

**Form Data**:
- `name` (str, required)
- `icon` (str, required)

**Returns**: Redirect to `/budget/categories`

**Database Functions**:
- `db.update_category()` - Update category (line 570)

**Security**: User ID check prevents editing other users' categories

---

### POST /budget/categories/{category_id}/delete

**Location**: `src/api.py:902-930`

**Purpose**: Delete category

**Auth**: Required

**URL Parameters**:
- `category_id` (int) - Category to delete

**Returns**:
- Success: Redirect to `/budget/categories`
- Failure: Redirect with error if category in use

**Validation**:
- Checks if any expenses use this category
- Prevents deletion if in use

**Database Functions**:
- `db.get_category_usage_count()` - Count expenses (line 644)
- `db.delete_category()` - Delete if unused (line 604)

---

## Static Pages

### GET /budget/help

**Location**: `src/api.py:933-947`

**Purpose**: User guide and help documentation

**Auth**: Optional (shows different content if logged in)

**Template**: `templates/help.html`

**Returns**: Help page with usage instructions

---

### GET /budget/privacy

**Location**: `src/api.py:949-986`

**Purpose**: Privacy policy page

**Auth**: None (public)

**Template**: `templates/privacy.html`

**Returns**: Privacy policy

**Content**: Explains data collection, storage, and usage

---

### GET /budget/feedback

**Location**: `src/api.py:988-998`

**Purpose**: Display feedback form

**Auth**: Required

**Template**: `templates/feedback.html`

**Returns**: Feedback form page

---

### POST /budget/feedback

**Location**: `src/api.py:1000-1104`

**Purpose**: Submit feedback as GitHub issue

**Auth**: Required

**Form Data**:
- `feedback_type` (str, required) - bug/request/general
- `message` (str, required) - Feedback message

**Returns**:
- Success: Feedback page with success message
- Failure: Feedback page with error message

**GitHub Integration**:
- Creates issue via GitHub API
- Requires env vars: `GITHUB_TOKEN`, `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`
- Title prefix: [Bug], [Feature Request], or [Feedback]
- Labels: bug, enhancement, or question

**Issue Type Mapping**:
| Form Value | GitHub Label | Title Prefix |
|------------|--------------|--------------|
| bug | bug | [Bug] |
| request | enhancement | [Feature Request] |
| general | question | [Feedback] |

**External API**: Uses `httpx.AsyncClient` to call GitHub API

---

## API Endpoints

### GET /budget/api/stats

**Location**: `src/api.py:1107-1112`

**Purpose**: Get budget statistics as JSON

**Auth**: Required

**Returns**: JSON with user count

```json
{
  "user_count": 42
}
```

**Database Functions**:
- `db.get_user_count()` - Count total users (line 870)

---

### GET /budget/api/chart-data

**Location**: `src/api.py:1114-1168`

**Purpose**: Get category breakdown data for charts

**Auth**: Required

**Returns**: JSON with category totals

```json
{
  "Bolig": 12000.00,
  "Transport": 5500.00,
  ...
}
```

**Database Functions**:
- `db.get_category_totals()` - Calculate totals by category (line 518)

**Usage**: Used by dashboard charts

---

## Settings

### GET /budget/settings

**Location**: `src/api.py:1171-1190`

**Purpose**: User settings page

**Auth**: Required

**Template**: `templates/settings.html`

**Returns**: Settings page with account management

**Context Data**:
- `user` - Current user object (username, email if set)

**Database Functions**:
- `db.get_user_by_id()` - Get user details (line 802)

---

### POST /budget/settings/email

**Location**: `src/api.py:1192-1256`

**Purpose**: Update user email address

**Auth**: Required

**Form Data**:
- `email` (str, required) - New email address
- Empty string to remove email

**Validation**:
- Email format validation (if provided)
- Checks if email already in use by another user

**Returns**:
- Success: Settings page with success message
- Failure: Settings page with error message

**Database Functions**:
- `db.get_user_by_email()` - Check if email exists (line 783)
- `db.update_user_email()` - Update email hash (line 816)

**Security**: Email stored as SHA-256 hash for privacy

---

## Route Summary Table

| Method | Path | Line | Auth | Template | Purpose |
|--------|------|------|------|----------|---------|
| GET | `/budget/login` | 253 | No | login.html | Login page |
| POST | `/budget/login` | 261 | No | - | Process login |
| GET | `/budget/register` | 293 | No | register.html | Registration page |
| POST | `/budget/register` | 301 | No | - | Create account |
| GET | `/budget/forgot-password` | 430 | No | forgot-password.html | Password reset request |
| POST | `/budget/forgot-password` | 438 | No | - | Send reset email |
| GET | `/budget/reset-password/{token}` | 471 | Token | reset-password.html | Reset form |
| POST | `/budget/reset-password/{token}` | 490 | Token | - | Update password |
| GET | `/budget/demo` | 533 | No | dashboard.html | Demo mode |
| GET | `/budget/logout` | 548 | No | - | Clear session |
| GET | `/budget/` | 567 | Yes | dashboard.html | Dashboard |
| GET | `/budget` | 568 | Yes | dashboard.html | Dashboard (alias) |
| GET | `/budget/income` | 619 | Yes | income.html | Income management |
| POST | `/budget/income` | 639 | Yes | - | Update income |
| GET | `/budget/expenses` | 685 | Yes | expenses.html | Expense management |
| POST | `/budget/expenses/add` | 722 | Yes | - | Add expense |
| POST | `/budget/expenses/{id}/delete` | 760 | Yes | - | Delete expense |
| POST | `/budget/expenses/{id}/edit` | 777 | Yes | - | Edit expense |
| GET | `/budget/categories` | 820 | Yes | categories.html | Category management |
| POST | `/budget/categories/add` | 850 | Yes | - | Add category |
| POST | `/budget/categories/{id}/edit` | 874 | Yes | - | Edit category |
| POST | `/budget/categories/{id}/delete` | 902 | Yes | - | Delete category |
| GET | `/budget/help` | 933 | Optional | help.html | User guide |
| GET | `/budget/privacy` | 949 | No | privacy.html | Privacy policy |
| GET | `/budget/feedback` | 988 | Yes | feedback.html | Feedback form |
| POST | `/budget/feedback` | 1000 | Yes | - | Submit feedback |
| GET | `/budget/api/stats` | 1107 | Yes | JSON | User count |
| GET | `/budget/api/chart-data` | 1114 | Yes | JSON | Category data |
| GET | `/budget/settings` | 1171 | Yes | settings.html | Settings page |
| POST | `/budget/settings/email` | 1192 | Yes | - | Update email |

**Total**: 30 routes (17 GET, 13 POST)

---

## Common Patterns

### Authentication Check

All routes requiring auth use this pattern:

```python
user_id = get_user_id(request)
if user_id is None:
    return RedirectResponse("/budget/login", status_code=303)
```

Helper function at line 237-242.

### Danish Amount Parsing

All amount inputs use:

```python
amount = parse_danish_amount(form_amount)
```

Converts "25.000,50" → 25000.50 (line 104-131)

### Session Management

- Sessions stored in `data/sessions.json`
- Tokens hashed with SHA-256 before storage
- Helper functions: `load_sessions()` (line 147), `save_sessions()` (line 156)

---

## Related Documentation

- **Patterns**: `PATTERNS.md` - Coding patterns and standards
- **Database**: `src/CLAUDE.md` - Database function index
- **Architecture**: `docs/adr/` - Architecture decisions
- **Guides**: `docs/guides/adding-new-route.md` - How to add new routes
