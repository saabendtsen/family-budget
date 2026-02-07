---
type: adr
number: 007
status: accepted
date: 2024-01-15
---

# ADR-007: Demo Mode Design

## Status
Accepted

## Context

Want to let users explore the application without creating an account. Need demo mode with:
- Realistic sample data (Danish household budget)
- Read-only (no data modification)
- No database writes
- Easy to access

### Options Considered

1. **Hardcoded demo data** (no database)
2. **Shared demo account** (test@example.com)
3. **Temporary accounts** (auto-created, auto-deleted)

## Decision

Use **hardcoded demo data** with special demo session cookie.

## Rationale

### Why Hardcoded Data

1. **No database pollution**: Demo data never touches database
2. **Consistent experience**: Same data for all users
3. **Fast**: No database queries
4. **Simple**: Just return constants
5. **Safe**: Impossible to modify

### Design

**Demo data location**: `src/database.py:64-95`
- `DEMO_INCOME`: 3 income sources (~50k kr/month)
- `DEMO_EXPENSES`: 24 typical expenses (~42k kr/month)

**Demo session**: Special cookie value
```python
DEMO_SESSION_ID = "demo_mode_session"
```

**Demo functions**: `src/database.py:934-978`
- `get_demo_income()`
- `get_demo_expenses()`
- `get_demo_category_totals()`
- etc.

**Entry point**: `/budget/demo` route

## Implementation

**Location**: `src/api.py:533-546`

```python
@app.get("/budget/demo")
async def demo_mode(request: Request):
    """Demo mode with hardcoded data."""
    # Set demo session cookie
    response = templates.TemplateResponse("dashboard.html", {
        "request": request,
        "income_list": db.get_demo_income(),
        "expenses": db.get_demo_expenses(),
        "categories": db.get_demo_category_totals(),
        "total_income": db.get_demo_total_income(),
        "total_expenses": db.get_demo_total_expenses(),
        "leftover": db.get_demo_total_income() - db.get_demo_total_expenses(),
        "chart_data": db.get_demo_category_totals()
    })
    response.set_cookie("budget_session", DEMO_SESSION_ID)
    return response
```

**Demo check**:
```python
def is_demo_mode(request: Request) -> bool:
    return request.cookies.get("budget_session") == DEMO_SESSION_ID
```

## Consequences

### Positive
- No database writes
- Consistent experience
- Fast (no queries)
- Safe (read-only)
- Realistic Danish budget data

### Negative
- Can't customize demo data per user
- Need separate demo functions

**Acceptable**: Demo is meant to be consistent preview.

## Demo Data

Represents typical Danish family (2 adults, 2 kids):

**Income** (~50,000 kr/month):
- Person 1: 28,000 kr/month
- Person 2: 22,000 kr/month
- Bonus: 30,000 kr semi-annually

**Expenses** (~42,000 kr/month):
- Housing: 12,000 kr/month
- Transport: ~4,500 kr/month (car loan, gas, insurance)
- Kids: 3,600 kr/month (daycare, activities)
- Food: 6,000 kr/month
- Utilities: 2,000 kr/month
- Insurance: ~500 kr/month
- Subscriptions: 527 kr/month
- Savings: 3,000 kr/month
- Other: ~10,000 kr/month

**Leftover**: ~8,000 kr/month

## For AI Agents

**Check if demo mode**:
```python
if is_demo_mode(request):
    # Return demo data
    return db.get_demo_expenses()
else:
    # Return user data
    user_id = get_user_id(request)
    return db.get_all_expenses(user_id)
```

**Adding demo data**: Update constants in `src/database.py:64-95`

## References
- Demo route: `../../src/api.py:533-546`
- Demo data: `../../src/database.py:64-95`
- Demo functions: `../../src/database.py:934-978`
