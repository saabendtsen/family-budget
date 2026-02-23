# Yearly Overview Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add monthly expense allocation and a yearly overview page for liquidity planning.

**Architecture:** New `months` JSON column on expenses table stores which months an expense falls in. New `/budget/yearly` route renders a 12-column table showing expenses by category per month, income, and balance. Month picker added to the "Avanceret" section of the expense modal.

**Tech Stack:** FastAPI, SQLite (JSON1 extension), Jinja2 templates, TailwindCSS CDN, Playwright E2E tests.

**Design doc:** `docs/plans/2026-02-23-yearly-overview-design.md`

---

## Task 1: Add `months` field to Expense dataclass + migration

**Files:**
- Modify: `src/database.py:114-129` (Expense dataclass)
- Modify: `src/database.py:252+` (migration section in `init_db()`)
- Test: `tests/test_database.py`

**Step 1: Write failing tests for `months` field and `get_monthly_amounts()`**

Add to `tests/test_database.py` in the `TestExpenseOperations` class:

```python
class TestExpenseMonthlyAmounts:
    """Tests for Expense.get_monthly_amounts() method."""

    def test_monthly_expense_no_months(self, db_module):
        """Monthly expense without months set: equal amount every month."""
        exp = db_module.Expense(id=1, user_id=1, name="Husleje", category="Bolig",
                                amount=6000, frequency="monthly", months=None)
        result = exp.get_monthly_amounts()
        assert len(result) == 12
        assert all(v == 6000 for v in result.values())

    def test_yearly_expense_no_months(self, db_module):
        """Yearly expense without months: spread equally across 12 months."""
        exp = db_module.Expense(id=1, user_id=1, name="Forsikring", category="Forsikring",
                                amount=12000, frequency="yearly", months=None)
        result = exp.get_monthly_amounts()
        assert len(result) == 12
        assert all(v == 1000 for v in result.values())

    def test_semi_annual_expense_no_months(self, db_module):
        """Semi-annual without months: spread equally across 12 months."""
        exp = db_module.Expense(id=1, user_id=1, name="Service", category="Transport",
                                amount=6000, frequency="semi-annual", months=None)
        result = exp.get_monthly_amounts()
        assert len(result) == 12
        assert all(v == 1000 for v in result.values())

    def test_quarterly_expense_no_months(self, db_module):
        """Quarterly without months: spread equally across 12 months."""
        exp = db_module.Expense(id=1, user_id=1, name="Vand", category="Forbrug",
                                amount=2400, frequency="quarterly", months=None)
        result = exp.get_monthly_amounts()
        assert len(result) == 12
        assert all(v == 800 for v in result.values())

    def test_yearly_expense_with_months(self, db_module):
        """Yearly expense assigned to January: full amount in Jan only."""
        exp = db_module.Expense(id=1, user_id=1, name="Skat", category="Bolig",
                                amount=18000, frequency="yearly", months=[1])
        result = exp.get_monthly_amounts()
        assert result[1] == 18000
        assert all(result[m] == 0 for m in range(2, 13))

    def test_semi_annual_with_months(self, db_module):
        """Semi-annual in Mar+Sep: half amount in each."""
        exp = db_module.Expense(id=1, user_id=1, name="Forsikring", category="Forsikring",
                                amount=6000, frequency="semi-annual", months=[3, 9])
        result = exp.get_monthly_amounts()
        assert result[3] == 3000
        assert result[9] == 3000
        assert all(result[m] == 0 for m in range(1, 13) if m not in [3, 9])

    def test_quarterly_with_months(self, db_module):
        """Quarterly in Jan/Apr/Jul/Oct: quarter amount in each."""
        exp = db_module.Expense(id=1, user_id=1, name="Vand", category="Forbrug",
                                amount=2400, frequency="quarterly", months=[1, 4, 7, 10])
        result = exp.get_monthly_amounts()
        assert result[1] == 600
        assert result[4] == 600
        assert result[7] == 600
        assert result[10] == 600
        assert all(result[m] == 0 for m in [2, 3, 5, 6, 8, 9, 11, 12])
```

**Step 2: Run tests to verify they fail**

Run: `cd ~/projects/family-budget && python -m pytest tests/test_database.py::TestExpenseMonthlyAmounts -v`
Expected: FAIL — `Expense.__init__() got an unexpected keyword argument 'months'`

**Step 3: Implement `months` field and `get_monthly_amounts()`**

In `src/database.py`, update the `Expense` dataclass (line ~114):

```python
@dataclass
class Expense:
    id: int
    user_id: int
    name: str
    category: str
    amount: float
    frequency: str  # 'monthly', 'quarterly', 'semi-annual', or 'yearly'
    account: Optional[str] = None  # Optional bank account assignment
    months: Optional[list[int]] = None  # JSON array of month numbers (1-12), None = spread equally

    @property
    def monthly_amount(self) -> float:
        """Return the monthly equivalent amount with 2 decimal precision."""
        divisors = {'monthly': 1, 'quarterly': 3, 'semi-annual': 6, 'yearly': 12}
        result = self.amount / divisors.get(self.frequency, 1)
        return round(result, 2)

    def get_monthly_amounts(self) -> dict[int, float]:
        """Return amount per month (1-12) based on frequency and months assignment.

        If months is None, amount is spread equally across all 12 months
        (yearly amount / 12 per month).
        If months is set, the full frequency amount is split across those months.
        """
        result = {m: 0.0 for m in range(1, 13)}

        if self.frequency == 'monthly':
            # Monthly expenses: same amount every month regardless of months field
            for m in range(1, 13):
                result[m] = self.amount
            return result

        # Yearly total for this expense
        multipliers = {'quarterly': 4, 'semi-annual': 2, 'yearly': 1}
        yearly_total = self.amount * multipliers.get(self.frequency, 1)

        if self.months:
            # Split across specified months
            per_month = round(yearly_total / len(self.months), 2)
            for m in self.months:
                result[m] = per_month
        else:
            # Spread equally across 12 months
            per_month = round(yearly_total / 12, 2)
            for m in range(1, 13):
                result[m] = per_month

        return result
```

**Step 4: Run tests to verify they pass**

Run: `cd ~/projects/family-budget && python -m pytest tests/test_database.py::TestExpenseMonthlyAmounts -v`
Expected: ALL PASS

**Step 5: Add database migration for `months` column**

In `src/database.py` `init_db()`, add after the existing migrations (after the account migration section):

```python
# Migration: Add months column to expenses table
cur.execute("PRAGMA table_info(expenses)")
expense_columns = [col[1] for col in cur.fetchall()]
if "months" not in expense_columns:
    cur.execute("ALTER TABLE expenses ADD COLUMN months TEXT")
```

**Step 6: Write test for migration**

Add to `tests/test_database.py`:

```python
class TestMonthsMigration:
    """Tests for months column migration."""

    def test_months_column_exists_after_init(self, db_module):
        """init_db should create months column on expenses table."""
        conn = db_module.get_connection()
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(expenses)")
        columns = [col[1] for col in cur.fetchall()]
        conn.close()
        assert "months" in columns

    def test_existing_expenses_have_null_months(self, db_module):
        """Existing expenses should have months=None after migration."""
        user_id = db_module.create_user("migrationtest", "testpass")
        expense_id = db_module.add_expense(user_id, "Test", "Bolig", 1000, "monthly")
        expense = db_module.get_expense_by_id(expense_id, user_id)
        assert expense.months is None
```

**Step 7: Run all tests to verify nothing broke**

Run: `cd ~/projects/family-budget && python -m pytest tests/test_database.py -v`
Expected: ALL PASS (including existing tests)

**Step 8: Commit**

```bash
cd ~/projects/family-budget
git add src/database.py tests/test_database.py
git commit -m "feat: add months field to Expense dataclass with get_monthly_amounts()

Add months JSON column to expenses table for specifying which months
a non-monthly expense falls in. Includes migration and unit tests."
```

---

## Task 2: Update Expense CRUD to handle `months` field

**Files:**
- Modify: `src/database.py` — `get_all_expenses()`, `get_expense_by_id()`, `add_expense()`, `update_expense()`
- Modify: `src/database.py` — `get_demo_expenses()`
- Test: `tests/test_database.py`

**Step 1: Write failing tests for CRUD with months**

Add to `tests/test_database.py`:

```python
class TestExpenseCRUDWithMonths:
    """Tests for expense CRUD operations with months field."""

    def test_add_expense_with_months(self, db_module):
        """add_expense should store months as JSON."""
        user_id = db_module.create_user("monthstest1", "testpass")
        expense_id = db_module.add_expense(user_id, "Forsikring", "Forsikring", 6000, "semi-annual", months=[3, 9])
        expense = db_module.get_expense_by_id(expense_id, user_id)
        assert expense.months == [3, 9]

    def test_add_expense_without_months(self, db_module):
        """add_expense without months should store None."""
        user_id = db_module.create_user("monthstest2", "testpass")
        expense_id = db_module.add_expense(user_id, "Husleje", "Bolig", 10000, "monthly")
        expense = db_module.get_expense_by_id(expense_id, user_id)
        assert expense.months is None

    def test_update_expense_with_months(self, db_module):
        """update_expense should update months field."""
        user_id = db_module.create_user("monthstest3", "testpass")
        expense_id = db_module.add_expense(user_id, "Skat", "Bolig", 18000, "yearly")
        db_module.update_expense(expense_id, user_id, "Skat", "Bolig", 18000, "yearly", months=[7])
        expense = db_module.get_expense_by_id(expense_id, user_id)
        assert expense.months == [7]

    def test_update_expense_clear_months(self, db_module):
        """update_expense with months=None should clear months."""
        user_id = db_module.create_user("monthstest4", "testpass")
        expense_id = db_module.add_expense(user_id, "Skat", "Bolig", 18000, "yearly", months=[1])
        db_module.update_expense(expense_id, user_id, "Skat", "Bolig", 18000, "yearly", months=None)
        expense = db_module.get_expense_by_id(expense_id, user_id)
        assert expense.months is None

    def test_get_all_expenses_includes_months(self, db_module):
        """get_all_expenses should include months field."""
        user_id = db_module.create_user("monthstest5", "testpass")
        db_module.add_expense(user_id, "Forsikring", "Forsikring", 6000, "semi-annual", months=[3, 9])
        db_module.add_expense(user_id, "Husleje", "Bolig", 10000, "monthly")
        expenses = db_module.get_all_expenses(user_id)
        months_map = {e.name: e.months for e in expenses}
        assert months_map["Forsikring"] == [3, 9]
        assert months_map["Husleje"] is None
```

**Step 2: Run tests to verify they fail**

Run: `cd ~/projects/family-budget && python -m pytest tests/test_database.py::TestExpenseCRUDWithMonths -v`
Expected: FAIL — `add_expense() got an unexpected keyword argument 'months'`

**Step 3: Update CRUD functions**

In `src/database.py`, update these functions:

**`get_all_expenses()`** — add `months` to SELECT and parse JSON:

```python
def get_all_expenses(user_id: int) -> list[Expense]:
    """Get all expenses for a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, user_id, name, category, amount, frequency, account, months
        FROM expenses
        WHERE user_id = ?
        ORDER BY category, name
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    expenses = []
    for row in rows:
        d = dict(row)
        d['months'] = json.loads(d['months']) if d['months'] else None
        expenses.append(Expense(**d))
    return expenses
```

**`get_expense_by_id()`** — same pattern:

```python
def get_expense_by_id(expense_id: int, user_id: int) -> Optional[Expense]:
    """Get a specific expense for a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, name, category, amount, frequency, account, months FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id)
    )
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    d = dict(row)
    d['months'] = json.loads(d['months']) if d['months'] else None
    return Expense(**d)
```

**`add_expense()`** — add `months` parameter:

```python
def add_expense(user_id: int, name: str, category: str, amount: float, frequency: str, account: str = None, months: list[int] = None) -> int:
    """Add a new expense for a user. Returns the new expense ID."""
    conn = get_connection()
    cur = conn.cursor()
    months_json = json.dumps(months) if months else None
    cur.execute(
        """INSERT INTO expenses (user_id, name, category, amount, frequency, account, months)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name, category, amount, frequency, account, months_json)
    )
    expense_id = cur.lastrowid
    conn.commit()
    conn.close()
    return expense_id
```

**`update_expense()`** — add `months` parameter:

```python
def update_expense(expense_id: int, user_id: int, name: str, category: str, amount: float, frequency: str, account: str = None, months: list[int] = None):
    """Update an existing expense for a user."""
    conn = get_connection()
    cur = conn.cursor()
    months_json = json.dumps(months) if months else None
    cur.execute(
        """UPDATE expenses
           SET name = ?, category = ?, amount = ?, frequency = ?, account = ?, months = ?
           WHERE id = ? AND user_id = ?""",
        (name, category, amount, frequency, account, months_json, expense_id, user_id)
    )
    conn.commit()
    conn.close()
```

Also add `import json` at the top of `database.py` if not already present.

**Step 4: Update demo expenses to include months**

In `get_demo_expenses()`:

```python
def get_demo_expenses() -> list[Expense]:
    """Get demo expense data."""
    return [Expense(id=i+1, user_id=0, name=name, category=cat, amount=amount, frequency=freq, account=None, months=None)
            for i, (name, cat, amount, freq) in enumerate(DEMO_EXPENSES)]
```

No change needed since `months` already defaults to `None`, but verify the constructor call works after adding the field.

**Step 5: Run tests to verify they pass**

Run: `cd ~/projects/family-budget && python -m pytest tests/test_database.py -v`
Expected: ALL PASS

**Step 6: Run existing route tests to verify nothing broke**

Run: `cd ~/projects/family-budget && python -m pytest tests/ -v`
Expected: ALL PASS

**Step 7: Commit**

```bash
cd ~/projects/family-budget
git add src/database.py tests/test_database.py
git commit -m "feat: update expense CRUD to handle months field

Add months parameter to add_expense() and update_expense().
Parse JSON months from database in get_all_expenses() and get_expense_by_id()."
```

---

## Task 3: Update expense routes to accept `months` form field

**Files:**
- Modify: `src/api.py:738-833` — add/edit expense route handlers
- Test: `tests/test_api.py` (or `tests/test_routes.py` — check which exists)

**Step 1: Write failing tests for routes with months**

Check which test file has route tests first. Add tests for the expense add/edit routes:

```python
class TestExpenseRoutesWithMonths:
    """Tests for expense routes with months field."""

    def test_add_expense_with_months(self, authenticated_client):
        """POST /budget/expenses/add with months should store them."""
        response = authenticated_client.post("/budget/expenses/add", data={
            "name": "Bilforsikring",
            "category": "Forsikring",
            "amount": "6000",
            "frequency": "semi-annual",
            "account": "",
            "months": "3,9",
        }, follow_redirects=False)
        assert response.status_code == 303

        from src import database as db
        expenses = db.get_all_expenses(authenticated_client.user_id)
        insurance = [e for e in expenses if e.name == "Bilforsikring"][0]
        assert insurance.months == [3, 9]

    def test_add_expense_without_months(self, authenticated_client):
        """POST /budget/expenses/add without months should store None."""
        response = authenticated_client.post("/budget/expenses/add", data={
            "name": "Husleje",
            "category": "Bolig",
            "amount": "10000",
            "frequency": "monthly",
            "account": "",
        }, follow_redirects=False)
        assert response.status_code == 303

        from src import database as db
        expenses = db.get_all_expenses(authenticated_client.user_id)
        rent = [e for e in expenses if e.name == "Husleje"][0]
        assert rent.months is None

    def test_add_expense_months_validation_wrong_count(self, authenticated_client):
        """POST with wrong number of months for frequency should return 400."""
        response = authenticated_client.post("/budget/expenses/add", data={
            "name": "Bad",
            "category": "Bolig",
            "amount": "6000",
            "frequency": "semi-annual",
            "account": "",
            "months": "3",  # semi-annual needs exactly 2
        }, follow_redirects=False)
        assert response.status_code == 400

    def test_add_expense_months_validation_invalid_month(self, authenticated_client):
        """POST with invalid month number should return 400."""
        response = authenticated_client.post("/budget/expenses/add", data={
            "name": "Bad",
            "category": "Bolig",
            "amount": "6000",
            "frequency": "yearly",
            "account": "",
            "months": "13",
        }, follow_redirects=False)
        assert response.status_code == 400

    def test_edit_expense_with_months(self, authenticated_client):
        """POST /budget/expenses/{id}/edit with months should update them."""
        from src import database as db
        expense_id = db.add_expense(authenticated_client.user_id, "Skat", "Bolig", 18000, "yearly")

        response = authenticated_client.post(f"/budget/expenses/{expense_id}/edit", data={
            "name": "Skat",
            "category": "Bolig",
            "amount": "18000",
            "frequency": "yearly",
            "account": "",
            "months": "7",
        }, follow_redirects=False)
        assert response.status_code == 303

        expense = db.get_expense_by_id(expense_id, authenticated_client.user_id)
        assert expense.months == [7]

    def test_edit_expense_clear_months_on_frequency_change(self, authenticated_client):
        """Changing frequency to monthly should clear months."""
        from src import database as db
        expense_id = db.add_expense(authenticated_client.user_id, "Test", "Bolig", 6000, "semi-annual", months=[3, 9])

        response = authenticated_client.post(f"/budget/expenses/{expense_id}/edit", data={
            "name": "Test",
            "category": "Bolig",
            "amount": "6000",
            "frequency": "monthly",
            "account": "",
        }, follow_redirects=False)
        assert response.status_code == 303

        expense = db.get_expense_by_id(expense_id, authenticated_client.user_id)
        assert expense.months is None
```

**Step 2: Run tests to verify they fail**

Run: `cd ~/projects/family-budget && python -m pytest tests/ -k "TestExpenseRoutesWithMonths" -v`
Expected: FAIL

**Step 3: Update route handlers**

In `src/api.py`, update both `add_expense` and `edit_expense` routes:

**Validation helper** (add near `VALID_FREQUENCIES`):

```python
MONTHS_REQUIRED = {
    'quarterly': 4,
    'semi-annual': 2,
    'yearly': 1,
}

def parse_months(months_str: str | None, frequency: str) -> list[int] | None:
    """Parse and validate months form field.

    Args:
        months_str: Comma-separated month numbers (e.g. "3,9") or None/empty
        frequency: The expense frequency

    Returns:
        List of month ints, or None if no months specified

    Raises:
        HTTPException(400) if validation fails
    """
    if frequency == 'monthly':
        return None  # Monthly expenses don't use months

    if not months_str or not months_str.strip():
        return None  # No months specified = spread equally

    try:
        months = [int(m.strip()) for m in months_str.split(',')]
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldige måneder")

    # Validate month values are 1-12
    if any(m < 1 or m > 12 for m in months):
        raise HTTPException(status_code=400, detail="Måneder skal være mellem 1 og 12")

    # Validate count matches frequency
    expected = MONTHS_REQUIRED.get(frequency)
    if expected and len(months) != expected:
        raise HTTPException(status_code=400, detail=f"Vælg præcis {expected} måneder for denne frekvens")

    return sorted(months)
```

**Update `add_expense` route** — add `months` form field:

```python
@app.post("/budget/expenses/add")
async def add_expense(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    amount: str = Form(...),
    frequency: str = Form(...),
    account: str = Form(""),
    months: str = Form(""),
):
    # ... existing auth/demo checks ...

    if frequency not in VALID_FREQUENCIES:
        raise HTTPException(status_code=400, detail="Ugyldig frekvens")

    # ... existing amount parsing ...

    months_list = parse_months(months if months else None, frequency)

    user_id = get_user_id(request)
    account_value = account if account else None
    try:
        db.add_expense(user_id, name, category, amount_float, frequency, account_value, months=months_list)
    except sqlite3.Error as e:
        logger.error(f"Database error adding expense: {e}")
        raise HTTPException(status_code=500, detail="Der opstod en fejl ved tilfoejelse af udgiften")
    return RedirectResponse(url="/budget/expenses", status_code=303)
```

**Update `edit_expense` route** — same pattern, add `months: str = Form("")`.

**Step 4: Run tests to verify they pass**

Run: `cd ~/projects/family-budget && python -m pytest tests/ -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
cd ~/projects/family-budget
git add src/api.py tests/
git commit -m "feat: add months form field to expense add/edit routes

Parse comma-separated months from form, validate count matches frequency.
Monthly expenses always clear months. Invalid months return 400."
```

---

## Task 4: Add month picker UI to expense modal

**Files:**
- Modify: `templates/expenses.html` — add month picker in advanced section + JavaScript logic

**Step 1: Add month picker HTML**

In `templates/expenses.html`, inside `#advanced-section` (line ~266), add the month picker **before** the account field:

```html
<div id="months-picker-section" class="hidden mb-3">
    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        Falder i <span class="text-gray-400 font-normal">(valgfri)</span>
    </label>
    <p id="months-hint" class="text-xs text-gray-400 dark:text-gray-500 mb-2">Ikke valgt = fordeles ligeligt</p>
    <input type="hidden" name="months" id="expense-months" value="">
    <div class="grid grid-cols-6 gap-1.5" id="months-grid">
        <button type="button" data-month="1" onclick="toggleMonth(1)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Jan</button>
        <button type="button" data-month="2" onclick="toggleMonth(2)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Feb</button>
        <button type="button" data-month="3" onclick="toggleMonth(3)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Mar</button>
        <button type="button" data-month="4" onclick="toggleMonth(4)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Apr</button>
        <button type="button" data-month="5" onclick="toggleMonth(5)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Maj</button>
        <button type="button" data-month="6" onclick="toggleMonth(6)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Jun</button>
        <button type="button" data-month="7" onclick="toggleMonth(7)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Jul</button>
        <button type="button" data-month="8" onclick="toggleMonth(8)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Aug</button>
        <button type="button" data-month="9" onclick="toggleMonth(9)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Sep</button>
        <button type="button" data-month="10" onclick="toggleMonth(10)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Okt</button>
        <button type="button" data-month="11" onclick="toggleMonth(11)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Nov</button>
        <button type="button" data-month="12" onclick="toggleMonth(12)" class="month-btn py-2 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary transition-colors">Dec</button>
    </div>
</div>
```

**Step 2: Add JavaScript for month picker**

Add in the `<script>` section:

```javascript
// Month picker logic
const selectedMonths = new Set();
const monthsRequired = { 'quarterly': 4, 'semi-annual': 2, 'yearly': 1 };

function getRequiredMonths() {
    const freq = document.querySelector('input[name="frequency"]:checked')?.value;
    return monthsRequired[freq] || 0;
}

function toggleMonth(month) {
    const btn = document.querySelector(`[data-month="${month}"]`);
    if (selectedMonths.has(month)) {
        selectedMonths.delete(month);
        btn.classList.remove('bg-primary', 'text-white', 'border-primary');
        btn.classList.add('border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
    } else {
        const required = getRequiredMonths();
        if (required > 0 && selectedMonths.size >= required) return; // Max reached
        selectedMonths.add(month);
        btn.classList.add('bg-primary', 'text-white', 'border-primary');
        btn.classList.remove('border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
    }
    updateMonthsHidden();
    updateMonthButtons();
}

function updateMonthsHidden() {
    const sorted = [...selectedMonths].sort((a, b) => a - b);
    document.getElementById('expense-months').value = sorted.join(',');
}

function updateMonthButtons() {
    const required = getRequiredMonths();
    const atMax = required > 0 && selectedMonths.size >= required;
    document.querySelectorAll('.month-btn').forEach(btn => {
        const month = parseInt(btn.dataset.month);
        if (atMax && !selectedMonths.has(month)) {
            btn.classList.add('opacity-40');
            btn.disabled = true;
        } else {
            btn.classList.remove('opacity-40');
            btn.disabled = false;
        }
    });
    // Update hint text
    const hint = document.getElementById('months-hint');
    if (required > 0) {
        const remaining = required - selectedMonths.size;
        if (remaining > 0) {
            hint.textContent = `Vælg ${remaining} måned${remaining !== 1 ? 'er' : ''} mere`;
        } else {
            hint.textContent = 'Ikke valgt = fordeles ligeligt';
        }
    }
}

function clearMonths() {
    selectedMonths.clear();
    document.querySelectorAll('.month-btn').forEach(btn => {
        btn.classList.remove('bg-primary', 'text-white', 'border-primary', 'opacity-40');
        btn.classList.add('border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
        btn.disabled = false;
    });
    document.getElementById('expense-months').value = '';
}

function setMonths(monthsArray) {
    clearMonths();
    if (monthsArray) {
        monthsArray.forEach(m => {
            selectedMonths.add(m);
            const btn = document.querySelector(`[data-month="${m}"]`);
            if (btn) {
                btn.classList.add('bg-primary', 'text-white', 'border-primary');
                btn.classList.remove('border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
            }
        });
        updateMonthsHidden();
        updateMonthButtons();
    }
}

function updateMonthsPickerVisibility() {
    const freq = document.querySelector('input[name="frequency"]:checked')?.value;
    const section = document.getElementById('months-picker-section');
    if (freq && freq !== 'monthly') {
        section.classList.remove('hidden');
    } else {
        section.classList.add('hidden');
        clearMonths();
    }
}
```

**Step 3: Hook frequency radio buttons to show/hide month picker**

Add event listeners to frequency radios (in the script section, after DOM elements are assigned):

```javascript
// Listen for frequency changes
document.querySelectorAll('input[name="frequency"]').forEach(radio => {
    radio.addEventListener('change', () => {
        clearMonths();
        updateMonthsPickerVisibility();
    });
});
```

**Step 4: Update `openAddModal()` and `openEditModal()` to handle months**

Update `openAddModal()` — add at end before `modal.classList.remove('hidden')`:

```javascript
clearMonths();
updateMonthsPickerVisibility();
```

Update `openEditModal()` signature to accept `months` parameter:

```javascript
function openEditModal(id, name, category, amount, frequency, account, months) {
    // ... existing code ...
    // After setting frequency radio:
    document.querySelector('input[name="frequency"][value="' + frequency + '"]').checked = true;
    updateMonthsPickerVisibility();
    if (months) {
        setMonths(months);
        setAdvancedOpen(true);
    } else {
        clearMonths();
    }
    // ... rest of function ...
}
```

**Step 5: Update expense list items to pass months to openEditModal**

Where expenses are rendered with edit buttons, update the `onclick` call to include the months data. The expense list items need to pass `{{ expense.months | tojson }}` as the last argument.

Find the edit button onclick and update to:
```html
onclick="openEditModal({{ exp.id }}, '{{ exp.name | e }}', '{{ exp.category | e }}', '{{ exp.amount }}', '{{ exp.frequency }}', '{{ exp.account or "" }}', {{ exp.months | tojson }})"
```

**Step 6: Test manually**

Run: `cd ~/projects/family-budget && source venv/bin/activate && python -m src.api`
- Open http://localhost:8086/budget/expenses
- Add expense → select "Halvårlig" → verify month picker appears in Avanceret
- Select 2 months → verify 3rd month is disabled
- Save → edit → verify months are pre-selected

**Step 7: Commit**

```bash
cd ~/projects/family-budget
git add templates/expenses.html
git commit -m "feat: add month picker UI to expense modal

12-button grid in advanced section, visible for non-monthly frequencies.
Enforces correct month count per frequency. Persists on edit."
```

---

## Task 5: Add yearly overview backend + route

**Files:**
- Modify: `src/database.py` — add `get_yearly_overview()` function
- Modify: `src/api.py` — add `GET /budget/yearly` route
- Test: `tests/test_database.py`, `tests/test_api.py`

**Step 1: Write failing test for `get_yearly_overview()`**

```python
class TestYearlyOverview:
    """Tests for yearly overview data calculation."""

    def test_yearly_overview_empty(self, db_module):
        """Empty budget should return zeros."""
        user_id = db_module.create_user("yearlytest1", "testpass")
        result = db_module.get_yearly_overview(user_id)
        assert result['categories'] == {}
        assert all(result['totals'][m] == 0 for m in range(1, 13))

    def test_yearly_overview_monthly_expense(self, db_module):
        """Monthly expense shows same amount every month."""
        user_id = db_module.create_user("yearlytest2", "testpass")
        db_module.add_expense(user_id, "Husleje", "Bolig", 10000, "monthly")
        result = db_module.get_yearly_overview(user_id)
        assert all(result['categories']['Bolig'][m] == 10000 for m in range(1, 13))
        assert result['year_total'] == 120000

    def test_yearly_overview_with_months(self, db_module):
        """Expense with months assigned shows in correct months."""
        user_id = db_module.create_user("yearlytest3", "testpass")
        db_module.add_expense(user_id, "Forsikring", "Forsikring", 6000, "semi-annual", months=[3, 9])
        result = db_module.get_yearly_overview(user_id)
        assert result['categories']['Forsikring'][3] == 3000
        assert result['categories']['Forsikring'][9] == 3000
        assert result['categories']['Forsikring'][1] == 0
        assert result['year_total'] == 6000

    def test_yearly_overview_mixed_expenses(self, db_module):
        """Multiple expenses combine correctly per category."""
        user_id = db_module.create_user("yearlytest4", "testpass")
        db_module.add_expense(user_id, "Husleje", "Bolig", 10000, "monthly")
        db_module.add_expense(user_id, "Ejendomsskat", "Bolig", 18000, "yearly", months=[1])
        result = db_module.get_yearly_overview(user_id)
        assert result['categories']['Bolig'][1] == 28000  # 10000 + 18000
        assert result['categories']['Bolig'][2] == 10000   # Only husleje

    def test_yearly_overview_totals(self, db_module):
        """Totals row sums all categories per month."""
        user_id = db_module.create_user("yearlytest5", "testpass")
        db_module.add_expense(user_id, "Husleje", "Bolig", 5000, "monthly")
        db_module.add_expense(user_id, "Mad", "Mad", 3000, "monthly")
        result = db_module.get_yearly_overview(user_id)
        assert all(result['totals'][m] == 8000 for m in range(1, 13))

    def test_yearly_overview_income(self, db_module):
        """Income is spread equally (no months support)."""
        user_id = db_module.create_user("yearlytest6", "testpass")
        db_module.add_income(user_id, "Løn", 30000, "monthly")
        result = db_module.get_yearly_overview(user_id)
        assert all(result['income'][m] == 30000 for m in range(1, 13))

    def test_yearly_overview_balance(self, db_module):
        """Balance = income - expenses per month."""
        user_id = db_module.create_user("yearlytest7", "testpass")
        db_module.add_income(user_id, "Løn", 30000, "monthly")
        db_module.add_expense(user_id, "Husleje", "Bolig", 10000, "monthly")
        db_module.add_expense(user_id, "Skat", "Bolig", 18000, "yearly", months=[1])
        result = db_module.get_yearly_overview(user_id)
        assert result['balance'][1] == 2000   # 30000 - 10000 - 18000
        assert result['balance'][2] == 20000  # 30000 - 10000
```

**Step 2: Run tests to verify they fail**

Run: `cd ~/projects/family-budget && python -m pytest tests/test_database.py::TestYearlyOverview -v`
Expected: FAIL — `get_yearly_overview` not found

**Step 3: Implement `get_yearly_overview()`**

In `src/database.py`:

```python
def get_yearly_overview(user_id: int) -> dict:
    """Calculate yearly overview with monthly breakdown.

    Returns dict with:
        categories: {category_name: {1: amount, 2: amount, ..., 12: amount}}
        totals: {1: total, ..., 12: total}
        income: {1: amount, ..., 12: amount}
        balance: {1: amount, ..., 12: amount}
        year_total: float (total expenses for the year)
    """
    expenses = get_all_expenses(user_id)
    income_entries = get_all_income(user_id)

    # Build category breakdown
    categories: dict[str, dict[int, float]] = {}
    for exp in expenses:
        if exp.category not in categories:
            categories[exp.category] = {m: 0.0 for m in range(1, 13)}
        monthly = exp.get_monthly_amounts()
        for m in range(1, 13):
            categories[exp.category][m] += monthly[m]

    # Round all values
    for cat in categories:
        for m in range(1, 13):
            categories[cat][m] = round(categories[cat][m], 2)

    # Totals per month
    totals = {m: 0.0 for m in range(1, 13)}
    for cat_amounts in categories.values():
        for m in range(1, 13):
            totals[m] += cat_amounts[m]
    for m in range(1, 13):
        totals[m] = round(totals[m], 2)

    # Income per month (spread equally, no months support)
    income = {m: 0.0 for m in range(1, 13)}
    for inc in income_entries:
        monthly_amt = inc.monthly_amount
        for m in range(1, 13):
            income[m] += monthly_amt
    for m in range(1, 13):
        income[m] = round(income[m], 2)

    # Balance
    balance = {m: round(income[m] - totals[m], 2) for m in range(1, 13)}

    # Year total
    year_total = round(sum(totals.values()), 2)

    return {
        'categories': categories,
        'totals': totals,
        'income': income,
        'balance': balance,
        'year_total': year_total,
    }
```

**Step 4: Run tests to verify they pass**

Run: `cd ~/projects/family-budget && python -m pytest tests/test_database.py::TestYearlyOverview -v`
Expected: ALL PASS

**Step 5: Write failing route test**

```python
class TestYearlyOverviewRoute:
    """Tests for GET /budget/yearly route."""

    def test_yearly_requires_auth(self, client):
        """GET /budget/yearly should redirect to login if not authenticated."""
        response = client.get("/budget/yearly", follow_redirects=False)
        assert response.status_code == 303
        assert "/budget/login" in response.headers["location"]

    def test_yearly_page_loads(self, authenticated_client):
        """GET /budget/yearly should return 200."""
        response = authenticated_client.get("/budget/yearly")
        assert response.status_code == 200
        assert "Årsoverblik" in response.text
```

**Step 6: Add route handler**

In `src/api.py`:

```python
@app.get("/budget/yearly", response_class=HTMLResponse)
async def yearly_overview_page(request: Request):
    """Yearly overview page with monthly expense breakdown."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    user_id = get_user_id(request)
    demo = is_demo_mode(request)

    if demo:
        # For demo, use demo data through yearly overview
        overview = db.get_yearly_overview_demo()
    else:
        overview = db.get_yearly_overview(user_id)

    return templates.TemplateResponse("yearly.html", {
        "request": request,
        "overview": overview,
        "demo_mode": demo,
    })
```

Also add a `get_yearly_overview_demo()` function in `database.py` that creates demo expenses/income and calculates their yearly overview:

```python
def get_yearly_overview_demo() -> dict:
    """Get yearly overview for demo mode."""
    demo_expenses = get_demo_expenses()
    demo_income = get_demo_income()

    categories: dict[str, dict[int, float]] = {}
    for exp in demo_expenses:
        if exp.category not in categories:
            categories[exp.category] = {m: 0.0 for m in range(1, 13)}
        monthly = exp.get_monthly_amounts()
        for m in range(1, 13):
            categories[exp.category][m] += monthly[m]

    for cat in categories:
        for m in range(1, 13):
            categories[cat][m] = round(categories[cat][m], 2)

    totals = {m: round(sum(cat[m] for cat in categories.values()), 2) for m in range(1, 13)}

    income = {m: 0.0 for m in range(1, 13)}
    for inc in demo_income:
        for m in range(1, 13):
            income[m] += inc.monthly_amount
    for m in range(1, 13):
        income[m] = round(income[m], 2)

    balance = {m: round(income[m] - totals[m], 2) for m in range(1, 13)}
    year_total = round(sum(totals.values()), 2)

    return {'categories': categories, 'totals': totals, 'income': income, 'balance': balance, 'year_total': year_total}
```

**Step 7: Run tests**

Run: `cd ~/projects/family-budget && python -m pytest tests/ -v`
Expected: ALL PASS

**Step 8: Commit**

```bash
cd ~/projects/family-budget
git add src/database.py src/api.py tests/
git commit -m "feat: add yearly overview backend and route

get_yearly_overview() calculates 12-month expense breakdown by category.
GET /budget/yearly route serves the data to yearly.html template."
```

---

## Task 6: Create yearly overview template + navigation

**Files:**
- Create: `templates/yearly.html`
- Modify: `templates/base.html` — add nav item

**Step 1: Create `templates/yearly.html`**

```html
{% extends "base.html" %}
{% set active_page = "yearly" %}

{% block title %}Årsoverblik - Budget{% endblock %}

{% block content %}
<div class="max-w-6xl mx-auto px-4 py-6 pb-24">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Årsoverblik</h1>

    {% if not overview.categories %}
    <div class="bg-white dark:bg-gray-800 rounded-2xl p-8 text-center">
        <i data-lucide="calendar-range" class="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3"></i>
        <p class="text-gray-500 dark:text-gray-400">Ingen udgifter endnu.</p>
        <a href="/budget/expenses" class="text-primary hover:underline text-sm mt-2 inline-block">Tilføj udgifter</a>
    </div>
    {% else %}
    <div class="bg-white dark:bg-gray-800 rounded-2xl overflow-hidden shadow-sm">
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
                <thead>
                    <tr class="border-b border-gray-200 dark:border-gray-700">
                        <th class="sticky left-0 bg-white dark:bg-gray-800 text-left px-4 py-3 font-semibold text-gray-900 dark:text-white z-10">Kategori</th>
                        {% set month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec'] %}
                        {% for name in month_names %}
                        <th class="text-right px-3 py-3 font-semibold text-gray-900 dark:text-white whitespace-nowrap">{{ name }}</th>
                        {% endfor %}
                        <th class="text-right px-4 py-3 font-semibold text-gray-900 dark:text-white whitespace-nowrap">År total</th>
                    </tr>
                </thead>
                <tbody>
                    {% for cat_name, months in overview.categories.items() %}
                    <tr class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                        <td class="sticky left-0 bg-white dark:bg-gray-800 px-4 py-2.5 font-medium text-gray-900 dark:text-white z-10">{{ cat_name }}</td>
                        {% for m in range(1, 13) %}
                        <td class="text-right px-3 py-2.5 tabular-nums {% if months[m] == 0 %}text-gray-300 dark:text-gray-600{% else %}text-gray-700 dark:text-gray-300{% endif %}">
                            {{ format_currency_short(months[m]) }}
                        </td>
                        {% endfor %}
                        <td class="text-right px-4 py-2.5 font-medium tabular-nums text-gray-900 dark:text-white">
                            {{ format_currency_short(months.values() | sum) }}
                        </td>
                    </tr>
                    {% endfor %}

                    <!-- Expenses total row -->
                    <tr class="border-t-2 border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50">
                        <td class="sticky left-0 bg-gray-50 dark:bg-gray-700/50 px-4 py-2.5 font-semibold text-gray-900 dark:text-white z-10">Udgifter i alt</td>
                        {% for m in range(1, 13) %}
                        <td class="text-right px-3 py-2.5 font-semibold tabular-nums text-gray-900 dark:text-white">
                            {{ format_currency_short(overview.totals[m]) }}
                        </td>
                        {% endfor %}
                        <td class="text-right px-4 py-2.5 font-bold tabular-nums text-gray-900 dark:text-white">
                            {{ format_currency_short(overview.year_total) }}
                        </td>
                    </tr>

                    <!-- Income row -->
                    <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                        <td class="sticky left-0 bg-white dark:bg-gray-800 px-4 py-2.5 font-medium text-green-600 dark:text-green-400 z-10">Indkomst</td>
                        {% for m in range(1, 13) %}
                        <td class="text-right px-3 py-2.5 tabular-nums text-green-600 dark:text-green-400">
                            {{ format_currency_short(overview.income[m]) }}
                        </td>
                        {% endfor %}
                        <td class="text-right px-4 py-2.5 font-medium tabular-nums text-green-600 dark:text-green-400">
                            {{ format_currency_short(overview.income.values() | sum) }}
                        </td>
                    </tr>

                    <!-- Balance row -->
                    <tr class="border-t-2 border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50">
                        <td class="sticky left-0 bg-gray-50 dark:bg-gray-700/50 px-4 py-2.5 font-bold text-gray-900 dark:text-white z-10">Balance</td>
                        {% for m in range(1, 13) %}
                        <td class="text-right px-3 py-2.5 font-bold tabular-nums {% if overview.balance[m] >= 0 %}text-green-600 dark:text-green-400{% else %}text-red-600 dark:text-red-400{% endif %}">
                            {{ format_currency_short(overview.balance[m]) }}
                        </td>
                        {% endfor %}
                        {% set year_balance = overview.balance.values() | sum %}
                        <td class="text-right px-4 py-2.5 font-bold tabular-nums {% if year_balance >= 0 %}text-green-600 dark:text-green-400{% else %}text-red-600 dark:text-red-400{% endif %}">
                            {{ format_currency_short(year_balance) }}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
```

**Step 2: Add `format_currency_short` Jinja2 helper**

In `src/api.py`, near `format_currency`:

```python
def format_currency_short(amount: float) -> str:
    """Format amount as short Danish currency (no 'kr' suffix, no decimals for whole numbers)."""
    if amount == 0:
        return "0"
    if amount == int(amount):
        formatted = f"{int(amount):,}".replace(",", ".")
    else:
        formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted

templates.env.globals["format_currency_short"] = format_currency_short
```

**Step 3: Add navigation item to `base.html`**

In `templates/base.html`, in the bottom nav `<div class="flex justify-around items-center">`, add before the "Om" link:

```html
<a href="/budget/yearly" class="nav-item flex flex-col items-center py-2 px-4 rounded-lg {% if active_page == 'yearly' %}text-primary bg-blue-50 dark:bg-blue-900/30{% else %}text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200{% endif %}">
    <i data-lucide="calendar-range" class="w-6 h-6"></i>
    <span class="text-xs mt-1">Årsoverblik</span>
</a>
```

**Step 4: Test manually**

Run: `cd ~/projects/family-budget && source venv/bin/activate && python -m src.api`
- Verify nav item appears
- Click "Årsoverblik" → verify table renders
- Check demo mode works
- Check mobile scroll works

**Step 5: Commit**

```bash
cd ~/projects/family-budget
git add templates/yearly.html templates/base.html src/api.py
git commit -m "feat: add yearly overview page with 12-month table

New /budget/yearly route with category-by-month table, income row,
and color-coded balance. Sticky category column for mobile scroll.
Nav item added to bottom navigation."
```

---

## Task 7: E2E tests

**Files:**
- Modify: `e2e/test_budget.py` — add E2E tests for month picker and yearly overview

**Step 1: Write E2E tests**

```python
class TestYearlyOverview:
    """E2E tests for yearly overview feature."""

    def test_yearly_page_loads(self, authenticated_page: Page, base_url: str):
        """Yearly overview page should load."""
        authenticated_page.goto(f"{base_url}/budget/yearly")
        expect(authenticated_page.get_by_text("Årsoverblik")).to_be_visible()

    def test_yearly_shows_expense_data(self, authenticated_page: Page, base_url: str):
        """Yearly overview should show added expenses."""
        import uuid
        # Add an expense first
        authenticated_page.goto(f"{base_url}/budget/expenses")
        authenticated_page.click('[data-lucide="plus"]')
        expense_name = f"E2E Year {uuid.uuid4().hex[:6]}"
        authenticated_page.fill('#expense-name', expense_name)
        authenticated_page.fill('#expense-amount', '12000')
        # Monthly is default
        authenticated_page.click('button:has-text("Tilføj")')
        authenticated_page.wait_for_url(f"{base_url}/budget/expenses")

        # Navigate to yearly overview
        authenticated_page.goto(f"{base_url}/budget/yearly")
        # Should show the expense category
        expect(authenticated_page.get_by_text("Bolig")).to_be_visible()

    def test_month_picker_visible_for_yearly(self, authenticated_page: Page, base_url: str):
        """Month picker should appear for yearly frequency in advanced section."""
        authenticated_page.goto(f"{base_url}/budget/expenses")
        authenticated_page.click('[data-lucide="plus"]')

        # Select yearly frequency
        authenticated_page.click('text=Årlig')

        # Open advanced section
        authenticated_page.click('#advanced-toggle')

        # Month picker should be visible
        expect(authenticated_page.locator('#months-picker-section')).to_be_visible()

    def test_month_picker_hidden_for_monthly(self, authenticated_page: Page, base_url: str):
        """Month picker should be hidden for monthly frequency."""
        authenticated_page.goto(f"{base_url}/budget/expenses")
        authenticated_page.click('[data-lucide="plus"]')

        # Monthly is default
        authenticated_page.click('#advanced-toggle')
        expect(authenticated_page.locator('#months-picker-section')).to_be_hidden()

    def test_add_expense_with_months(self, authenticated_page: Page, base_url: str):
        """Should save expense with specific months."""
        import uuid
        authenticated_page.goto(f"{base_url}/budget/expenses")
        authenticated_page.click('[data-lucide="plus"]')

        expense_name = f"E2E Months {uuid.uuid4().hex[:6]}"
        authenticated_page.fill('#expense-name', expense_name)
        authenticated_page.fill('#expense-amount', '6000')
        authenticated_page.click('text=Halvårlig')

        # Open advanced and select months
        authenticated_page.click('#advanced-toggle')
        authenticated_page.click('[data-month="3"]')  # March
        authenticated_page.click('[data-month="9"]')  # September

        authenticated_page.click('button:has-text("Tilføj")')
        authenticated_page.wait_for_url(f"{base_url}/budget/expenses")
        expect(authenticated_page.get_by_text(expense_name)).to_be_visible()
```

**Step 2: Run E2E tests**

Run: `cd ~/projects/family-budget && python -m pytest e2e/test_budget.py::TestYearlyOverview -v --headed`
Expected: ALL PASS

**Step 3: Run full test suite**

Run: `cd ~/projects/family-budget && python -m pytest tests/ e2e/ -v`
Expected: ALL PASS (including all existing tests)

**Step 4: Commit**

```bash
cd ~/projects/family-budget
git add e2e/test_budget.py
git commit -m "test: add E2E tests for yearly overview and month picker

Tests cover page load, expense data display, month picker visibility
per frequency, and saving expense with specific months."
```

---

## Task 8: Final verification and cleanup

**Files:**
- Verify: all tests pass
- Verify: demo mode works
- Verify: existing functionality unchanged

**Step 1: Run full test suite**

Run: `cd ~/projects/family-budget && python -m pytest tests/ e2e/ -v`
Expected: ALL PASS

**Step 2: Verify demo mode**

- Open http://localhost:8086/budget/demo
- Navigate to Årsoverblik → should show demo data with all expenses spread equally (no months assigned to demo data)

**Step 3: Verify existing pages unchanged**

- Dashboard should look identical
- Expenses page should work as before
- Editing existing expenses (without months) should work unchanged

**Step 4: Create PR**

```bash
cd ~/projects/family-budget
gh pr create --title "feat: yearly overview with monthly expense allocation" --body "$(cat <<'EOF'
## Summary
- Adds month picker to expense modal (in Advanced section) for non-monthly expenses
- New `/budget/yearly` page with 12-column table showing expenses by category per month
- Balance row color-coded green/red for liquidity planning

Closes #24

## Test plan
- [ ] Unit tests for `get_monthly_amounts()` method
- [ ] Unit tests for CRUD with months field
- [ ] Unit tests for `get_yearly_overview()` calculation
- [ ] Route tests for `/budget/yearly`
- [ ] E2E tests for month picker and yearly page
- [ ] Manual: verify demo mode
- [ ] Manual: verify existing pages unchanged
EOF
)"
```
