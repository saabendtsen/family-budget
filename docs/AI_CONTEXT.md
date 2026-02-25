# Family Budget - Project Context

This is the Single Source of Truth for the project's architecture, data model, and business logic. All AI agents should refer to this file first.

## Tech Stack
- **Backend:** FastAPI (Python 3.10+) + SQLite
- **Frontend:** Jinja2 templates + TailwindCSS (via CDN) + Lucide icons
- **Auth:** Session-based with PBKDF2 password hashing (server-side sessions)
- **Database:** SQLite in `data/budget.db`

## Core Data Model (SQLite)
- `users`: `id`, `username`, `password_hash`, `salt`, `email`, `last_login`
- `income`: `id`, `user_id`, `person`, `amount`, `frequency` (monthly, quarterly, semi-annual, yearly)
- `expenses`: `id`, `user_id`, `category_id`, `name`, `amount`, `frequency`
- `categories`: `id`, `user_id`, `name`, `icon` (Lucide icon names)
- `password_reset_tokens`: `user_id`, `token_hash`, `expires_at`

## Endpoints

| Route | Description |
|-------|-------------|
| `/budget/` | Dashboard (Overview) |
| `/budget/login` | Login page |
| `/budget/register` | User registration |
| `/budget/demo` | Demo mode (Read-only constants in `src/database.py`) |
| `/budget/expenses` | Expense management |
| `/budget/income` | Income management (Dynamic sources) |
| `/budget/categories` | Category management |
| `/budget/settings` | Account settings |
| `/budget/om` | User guide & info |

## Architecture Decisions (ADRs)

- **Password Hashing:** PBKDF2-HMAC-SHA256 with 600k iterations (OWASP 2023). Uses stdlib `hashlib` to avoid C-extensions.
- **Sessions:** Server-side sessions in `data/sessions.json`. Tokens are SHA-256 hashed. Cookies: `httponly`, `secure`, `samesite=lax`.
- **Database Access:** Direct SQLite with `sqlite3.Row` factory for dict-like access. No ORM.
- **User Isolation:** EVERY query must include `user_id` in the `WHERE` clause.
- **Frontend:** Server-Side Rendering (SSR). No JavaScript build step. Minimal JS for modals.
- **Formatting:** Amounts use Danish formatting (`25.000,50 kr.`). All UI text is in Danish.

## Key Logic Patterns
- **Frequencies:** All amounts (monthly, quarterly, etc.) are normalized to monthly via the `monthly_amount` property/calculation.
- **Post-Redirect-Get:** All POST handlers must redirect with status `303`.
- **Amount Parsing:** Use `parse_danish_amount` for all numeric inputs.
