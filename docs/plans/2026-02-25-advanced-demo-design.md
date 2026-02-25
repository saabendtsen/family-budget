# Advanced Demo Function — Design

**Issue:** [#101](https://github.com/saabendtsen/family-budget/issues/101)
**Date:** 2026-02-25

## Problem

The demo mode shows a single view. Users should be able to switch between a simple monthly overview and an advanced view that showcases all features (accounts, diverse tags, etc.).

## Approach

Server-side toggle via cookie. Fits the existing SSR architecture — no JS complexity, easy to test. Page reloads on toggle switch.

## Toggle Mechanism

- New cookie `demo_level` with values `"simple"` (default) or `"advanced"`.
- New helper: `is_demo_advanced(request)` checks this cookie.
- New endpoint: `GET /budget/demo/toggle` flips the cookie and redirects back to the referring page.
- Toggle rendered in the amber demo banner across all pages.

## Data Model

No database changes. All demo data stays as in-memory constants in `src/database.py`.

**New constants:**
- `DEMO_ACCOUNTS` — account names: Fælles konto, Person 1 konto, Person 2 konto, Opsparingskonto.
- `DEMO_EXPENSES_ADVANCED` — same 22 expenses but with account assignments:
  - Housing, utilities, transport, food, children → Fælles konto
  - Person-specific subscriptions → Person 1/2 konto
  - Savings → Opsparingskonto
- `DEMO_INCOME_ADVANCED` — adds Børnepenge (quarterly) to existing 3 sources.

**New functions:** `get_demo_expenses_advanced()`, `get_demo_income_advanced()`, `get_demo_account_totals_advanced()`, etc.

## Feature Split

| Feature | Simple | Advanced |
|---------|--------|----------|
| Expenses | 22 items, no accounts | Same items + account assignments |
| Accounts | Hidden | 4 accounts with totals |
| Income | 3 sources | 4+ sources |
| Yearly overview | Hidden | Shown (if merged) |
| Categories | 9 with icons | Same |
| Frequencies | Mixed | Same |

## Route Changes

Every route checking `is_demo_mode()` also checks `is_demo_advanced()` to select the right data set. Affected routes: dashboard, expenses, income, chart-data API.

## Testing

- Unit tests for new demo data functions (accounts, totals).
- E2E tests: toggle switches views, advanced shows accounts, simple hides them, toggle persists across navigation.

## Maintenance Mandate

Add to `CLAUDE.md`: When adding new user-facing features, update the advanced demo data to showcase the feature. Future Claude sessions should offer this automatically.
