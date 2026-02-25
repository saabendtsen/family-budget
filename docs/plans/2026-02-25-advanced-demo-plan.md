# Advanced Demo Function — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a simple/advanced toggle to demo mode so users can switch between a basic monthly overview and a full-featured view with accounts, extra income sources, and all UI features visible.

**Architecture:** Server-side cookie (`demo_level`) controls which demo data set is returned. A toggle endpoint flips the cookie and redirects back. The demo banner in `base.html` renders the toggle on all pages. Advanced demo data adds account assignments to expenses and an extra income source.

**Tech Stack:** FastAPI, Jinja2, SQLite (no DB changes), TailwindCSS

---

### Task 1: Add advanced demo data constants

**Files:**
- Modify: `src/database.py:63-95` (after existing demo constants)

**Step 1: Write the failing test**

Add to `tests/test_api.py`:

```python
class TestAdvancedDemoData:
    """Tests for advanced demo data functions."""

    def test_advanced_expenses_have_accounts(self, db_module):
        """Advanced demo expenses should all have account assignments."""
        expenses = db_module.get_demo_expenses(advanced=True)
        for exp in expenses:
            assert exp.account is not None, f"Expense '{exp.name}' missing account"

    def test_advanced_income_has_extra_source(self, db_module):
        """Advanced demo income should have more sources than simple."""
        simple = db_module.get_demo_income(advanced=False)
        advanced = db_module.get_demo_income(advanced=True)
        assert len(advanced) > len(simple)

    def test_simple_expenses_have_no_accounts(self, db_module):
        """Simple demo expenses should have no account assignments."""
        expenses = db_module.get_demo_expenses(advanced=False)
        for exp in expenses:
            assert exp.account is None

    def test_advanced_account_totals_not_empty(self, db_module):
        """Advanced demo should return account totals."""
        totals = db_module.get_demo_account_totals(advanced=True)
        assert len(totals) > 0

    def test_simple_account_totals_empty(self, db_module):
        """Simple demo should return empty account totals."""
        totals = db_module.get_demo_account_totals(advanced=False)
        assert len(totals) == 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py::TestAdvancedDemoData -v`
Expected: FAIL — `get_demo_expenses` doesn't accept `advanced` parameter yet.

**Step 3: Add advanced demo constants and update functions**

In `src/database.py`, after the existing `DEMO_EXPENSES` list (line 95), add:

```python
# Advanced demo data - adds account assignments and extra income
DEMO_INCOME_ADVANCED = [
    # (person, amount, frequency)
    ("Person 1", 28000, "monthly"),
    ("Person 2", 22000, "monthly"),
    ("Bonus", 30000, "semi-annual"),
    ("Børnepenge", 6264, "quarterly"),
]

DEMO_EXPENSES_ADVANCED = [
    # (name, category, amount, frequency, account)
    ("Husleje/boliglån", "Bolig", 12000, "monthly", "Fælles konto"),
    ("Ejendomsskat", "Bolig", 18000, "yearly", "Fælles konto"),
    ("Varme", "Forbrug", 800, "monthly", "Fælles konto"),
    ("El", "Forbrug", 600, "monthly", "Fælles konto"),
    ("Vand", "Forbrug", 2400, "quarterly", "Fælles konto"),
    ("Internet", "Forbrug", 299, "monthly", "Fælles konto"),
    ("Bil - lån", "Transport", 2500, "monthly", "Fælles konto"),
    ("Benzin", "Transport", 1500, "monthly", "Fælles konto"),
    ("Vægtafgift", "Transport", 3600, "yearly", "Fælles konto"),
    ("Bilforsikring", "Transport", 6000, "yearly", "Fælles konto"),
    ("Bilservice", "Transport", 4500, "semi-annual", "Fælles konto"),
    ("Institution", "Børn", 3200, "monthly", "Fælles konto"),
    ("Fritidsaktiviteter", "Børn", 400, "monthly", "Fælles konto"),
    ("Dagligvarer", "Mad", 6000, "monthly", "Fælles konto"),
    ("Indboforsikring", "Forsikring", 1800, "yearly", "Fælles konto"),
    ("Ulykkesforsikring", "Forsikring", 1200, "yearly", "Fælles konto"),
    ("Tandlægeforsikring", "Forsikring", 600, "quarterly", "Fælles konto"),
    ("Netflix", "Abonnementer", 129, "monthly", "Person 1 konto"),
    ("Spotify", "Abonnementer", 99, "monthly", "Person 2 konto"),
    ("Fitness", "Abonnementer", 299, "monthly", "Person 1 konto"),
    ("Opsparing", "Opsparing", 3000, "monthly", "Opsparingskonto"),
    ("Telefon", "Andet", 199, "monthly", "Person 2 konto"),
]
```

Then update the existing demo functions to accept an `advanced` parameter. Modify each function in the demo data section (lines 1091-1133):

```python
def get_demo_income(advanced: bool = False) -> list[Income]:
    """Get demo income data."""
    source = DEMO_INCOME_ADVANCED if advanced else DEMO_INCOME
    return [Income(id=i+1, user_id=0, person=person, amount=amount, frequency=freq)
            for i, (person, amount, freq) in enumerate(source)]


def get_demo_total_income(advanced: bool = False) -> float:
    """Get total demo income (converted to monthly equivalent)."""
    return sum(inc.monthly_amount for inc in get_demo_income(advanced))


def get_demo_expenses(advanced: bool = False) -> list[Expense]:
    """Get demo expense data."""
    if advanced:
        return [Expense(id=i+1, user_id=0, name=name, category=cat, amount=amount, frequency=freq, account=acct)
                for i, (name, cat, amount, freq, acct) in enumerate(DEMO_EXPENSES_ADVANCED)]
    return [Expense(id=i+1, user_id=0, name=name, category=cat, amount=amount, frequency=freq, account=None)
            for i, (name, cat, amount, freq) in enumerate(DEMO_EXPENSES)]


def get_demo_expenses_by_category(advanced: bool = False) -> dict[str, list[Expense]]:
    """Get demo expenses grouped by category."""
    expenses = get_demo_expenses(advanced)
    grouped = {}
    for exp in expenses:
        if exp.category not in grouped:
            grouped[exp.category] = []
        grouped[exp.category].append(exp)
    return grouped


def get_demo_category_totals(advanced: bool = False) -> dict[str, float]:
    """Get demo total monthly amount per category."""
    expenses = get_demo_expenses(advanced)
    totals = {}
    for exp in expenses:
        if exp.category not in totals:
            totals[exp.category] = 0
        totals[exp.category] += exp.monthly_amount
    return totals


def get_demo_total_expenses(advanced: bool = False) -> float:
    """Get demo total monthly expenses."""
    return sum(exp.monthly_amount for exp in get_demo_expenses(advanced))


def get_demo_account_totals(advanced: bool = False) -> dict[str, float]:
    """Get demo account totals (monthly equivalent)."""
    if not advanced:
        return {}
    expenses = get_demo_expenses(advanced=True)
    totals = {}
    for exp in expenses:
        if exp.account:
            if exp.account not in totals:
                totals[exp.account] = 0
            totals[exp.account] += exp.monthly_amount
    return totals
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_api.py::TestAdvancedDemoData -v`
Expected: PASS — all 5 tests green.

**Step 5: Commit**

```bash
git add src/database.py tests/test_api.py
git commit -m "feat: add advanced demo data with account assignments (#101)"
```

---

### Task 2: Add toggle endpoint and helper

**Files:**
- Modify: `src/api.py:255-258` (add helper after `is_demo_mode`)
- Modify: `src/api.py:540-552` (add toggle route after demo route)

**Step 1: Write the failing test**

Add to `tests/test_api.py`:

```python
class TestDemoToggle:
    """Tests for demo simple/advanced toggle."""

    def test_is_demo_advanced_defaults_to_false(self, client):
        """Demo mode should default to simple (not advanced)."""
        client.cookies.set("budget_session", "demo")
        response = client.get("/budget/")
        # Should not have account totals in simple mode
        assert "Fælles konto" not in response.text

    def test_toggle_sets_advanced_cookie(self, client):
        """Toggle endpoint should set demo_level=advanced cookie."""
        client.cookies.set("budget_session", "demo")
        response = client.get("/budget/demo/toggle", follow_redirects=False)
        assert response.status_code == 303
        assert response.cookies.get("demo_level") == "advanced"

    def test_toggle_flips_back_to_simple(self, client):
        """Toggle should flip advanced back to simple."""
        client.cookies.set("budget_session", "demo")
        client.cookies.set("demo_level", "advanced")
        response = client.get("/budget/demo/toggle", follow_redirects=False)
        assert response.status_code == 303
        assert response.cookies.get("demo_level") == "simple"

    def test_toggle_requires_demo_mode(self, client):
        """Toggle should redirect to login if not in demo mode."""
        response = client.get("/budget/demo/toggle", follow_redirects=False)
        assert response.status_code == 303
        assert "/budget/login" in response.headers["location"]
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py::TestDemoToggle -v`
Expected: FAIL — no `/budget/demo/toggle` endpoint exists.

**Step 3: Add helper and toggle endpoint**

In `src/api.py`, after `is_demo_mode` (line 257), add:

```python
def is_demo_advanced(request: Request) -> bool:
    """Check if demo mode is set to advanced view."""
    return is_demo_mode(request) and request.cookies.get("demo_level") == "advanced"
```

After the demo route (line 552), add:

```python
@app.get("/budget/demo/toggle")
async def demo_toggle(request: Request):
    """Toggle between simple and advanced demo mode."""
    if not is_demo_mode(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    current = request.cookies.get("demo_level", "simple")
    new_level = "simple" if current == "advanced" else "advanced"

    # Redirect back to referring page, or dashboard
    referer = request.headers.get("referer", "/budget/")
    response = RedirectResponse(url=referer, status_code=303)
    response.set_cookie(
        key="demo_level",
        value=new_level,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600,
    )
    return response
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_api.py::TestDemoToggle -v`
Expected: PASS — all 4 tests green.

**Step 5: Commit**

```bash
git add src/api.py tests/test_api.py
git commit -m "feat: add demo toggle endpoint and is_demo_advanced helper (#101)"
```

---

### Task 3: Wire advanced flag into all demo routes

**Files:**
- Modify: `src/api.py:574-622` (dashboard route)
- Modify: `src/api.py:629-646` (income route)
- Modify: `src/api.py:695-732` (expenses route)
- Modify: `src/api.py:1272-1322` (chart-data API)

**Step 1: Write the failing test**

Add to `tests/test_api.py`:

```python
class TestAdvancedDemoRoutes:
    """Tests that advanced mode shows richer data on all routes."""

    def test_dashboard_advanced_shows_accounts(self, client):
        """Dashboard in advanced mode should show account totals."""
        client.cookies.set("budget_session", "demo")
        client.cookies.set("demo_level", "advanced")
        response = client.get("/budget/")
        assert "Fælles konto" in response.text

    def test_dashboard_simple_hides_accounts(self, client):
        """Dashboard in simple mode should not show accounts."""
        client.cookies.set("budget_session", "demo")
        response = client.get("/budget/")
        assert "Fælles konto" not in response.text

    def test_expenses_advanced_shows_accounts(self, client):
        """Expenses page in advanced mode should show account list."""
        client.cookies.set("budget_session", "demo")
        client.cookies.set("demo_level", "advanced")
        response = client.get("/budget/expenses")
        assert "Fælles konto" in response.text

    def test_income_advanced_shows_extra_source(self, client):
        """Income page in advanced mode should show Børnepenge."""
        client.cookies.set("budget_session", "demo")
        client.cookies.set("demo_level", "advanced")
        response = client.get("/budget/income")
        assert "Børnepenge" in response.text

    def test_income_simple_no_extra_source(self, client):
        """Income page in simple mode should not show Børnepenge."""
        client.cookies.set("budget_session", "demo")
        response = client.get("/budget/income")
        assert "Børnepenge" not in response.text

    def test_chart_data_advanced(self, client):
        """Chart API in advanced mode should return data."""
        client.cookies.set("budget_session", "demo")
        client.cookies.set("demo_level", "advanced")
        response = client.get("/budget/api/chart-data")
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] > 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py::TestAdvancedDemoRoutes -v`
Expected: FAIL — routes don't pass `advanced` flag yet.

**Step 3: Update all routes**

In each route, replace the demo data calls with the `advanced` parameter. The pattern is the same everywhere — get the advanced flag, pass it through:

**Dashboard (`src/api.py:581-591`):**
```python
    demo = is_demo_mode(request)
    advanced = is_demo_advanced(request)
    user_id = get_user_id(request)

    # Get data (demo or real)
    if demo:
        incomes = db.get_demo_income(advanced)
        total_income = db.get_demo_total_income(advanced)
        total_expenses = db.get_demo_total_expenses(advanced)
        expenses_by_category = db.get_demo_expenses_by_category(advanced)
        category_totals = db.get_demo_category_totals(advanced)
        account_totals = db.get_demo_account_totals(advanced)
```

Also pass `demo_advanced` to the template context:
```python
        "demo_mode": demo,
        "demo_advanced": advanced,
```

**Income (`src/api.py:635-641`):**
```python
    demo = is_demo_mode(request)
    advanced = is_demo_advanced(request)
    user_id = get_user_id(request)

    if demo:
        incomes = db.get_demo_income(advanced)
```

Also pass `demo_advanced`:
```python
    {"request": request, "incomes": incomes, "demo_mode": demo, "demo_advanced": advanced}
```

**Expenses (`src/api.py:701-711`):**
```python
    demo = is_demo_mode(request)
    advanced = is_demo_advanced(request)

    if demo:
        expenses = db.get_demo_expenses(advanced)
        expenses_by_category = db.get_demo_expenses_by_category(advanced)
        category_totals = db.get_demo_category_totals(advanced)
        categories = db.get_all_categories(0)
        category_usage = {cat.name: 0 for cat in categories}
        accounts = db.get_demo_accounts(advanced)
```

Add a helper in `src/database.py` for demo accounts:
```python
def get_demo_accounts(advanced: bool = False) -> list[Account]:
    """Get demo accounts for the accounts dropdown."""
    if not advanced:
        return []
    names = ["Fælles konto", "Person 1 konto", "Person 2 konto", "Opsparingskonto"]
    return [Account(id=i+1, name=name) for i, name in enumerate(names)]
```

Also pass `demo_advanced`:
```python
        "demo_mode": demo,
        "demo_advanced": advanced,
```

**Chart data API (`src/api.py:1282-1290`):**
```python
    demo = is_demo_mode(request)
    advanced = is_demo_advanced(request)
    user_id = get_user_id(request)

    if demo:
        category_totals = db.get_demo_category_totals(advanced)
        total_income = db.get_demo_total_income(advanced)
        total_expenses = db.get_demo_total_expenses(advanced)
        expenses = db.get_demo_expenses(advanced)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_api.py::TestAdvancedDemoRoutes -v`
Expected: PASS — all 6 tests green.

**Step 5: Run full test suite for regressions**

Run: `python -m pytest tests/test_api.py -x -q`
Expected: All tests pass (existing tests should not break since `advanced` defaults to `False`).

**Step 6: Commit**

```bash
git add src/api.py src/database.py tests/test_api.py
git commit -m "feat: wire advanced flag into all demo routes (#101)"
```

---

### Task 4: Add toggle UI to demo banner

**Files:**
- Modify: `templates/base.html:33-40` (demo banner)

**Step 1: Write the failing E2E test**

Add to `e2e/test_demo.py`:

```python
class TestDemoToggle:
    """Tests for simple/advanced demo toggle."""

    def test_toggle_visible_in_demo_banner(self, page: Page, base_url: str):
        """Toggle should be visible in demo banner."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        expect(page.get_by_text("Avanceret")).to_be_visible()

    def test_toggle_switches_to_advanced(self, page: Page, base_url: str):
        """Clicking toggle should switch to advanced mode."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        page.get_by_role("link", name="Avanceret").click()
        page.wait_for_load_state("networkidle")
        # In advanced mode, accounts should appear
        expect(page.get_by_text("Fælles konto")).to_be_visible()

    def test_toggle_switches_back_to_simple(self, page: Page, base_url: str):
        """Clicking toggle again should switch back to simple."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        # Switch to advanced
        page.get_by_role("link", name="Avanceret").click()
        page.wait_for_load_state("networkidle")
        # Switch back to simple
        page.get_by_role("link", name="Simpel").click()
        page.wait_for_load_state("networkidle")
        # Accounts should be gone
        expect(page.get_by_text("Fælles konto")).not_to_be_visible()

    def test_advanced_persists_across_pages(self, page: Page, base_url: str):
        """Advanced mode should persist when navigating to other pages."""
        page.goto(f"{base_url}/budget/demo")
        page.wait_for_url(f"{base_url}/budget/")
        page.get_by_role("link", name="Avanceret").click()
        page.wait_for_load_state("networkidle")
        # Navigate to income page
        page.goto(f"{base_url}/budget/income")
        # Should still be in advanced mode — extra income visible
        expect(page.get_by_text("Børnepenge")).to_be_visible()
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/test_demo.py::TestDemoToggle -v`
Expected: FAIL — no toggle link in banner yet.

**Step 3: Update demo banner in base.html**

Replace the demo banner (lines 33-40) with:

```html
{% if demo_mode %}
<!-- Demo mode banner -->
<div class="bg-amber-500 text-amber-900 px-4 py-2 text-center text-sm font-medium flex items-center justify-center gap-3 flex-wrap">
    <span class="flex items-center gap-1">
        <i data-lucide="info" class="w-4 h-4 inline"></i>
        Demo-tilstand (kun visning)
    </span>
    <span class="inline-flex rounded-lg overflow-hidden border border-amber-600">
        <a href="/budget/demo/toggle"
           class="px-3 py-0.5 text-xs font-semibold transition-colors
                  {% if not demo_advanced %}bg-amber-900 text-amber-100{% else %}hover:bg-amber-400{% endif %}">
            Simpel
        </a>
        <a href="/budget/demo/toggle"
           class="px-3 py-0.5 text-xs font-semibold transition-colors
                  {% if demo_advanced %}bg-amber-900 text-amber-100{% else %}hover:bg-amber-400{% endif %}">
            Avanceret
        </a>
    </span>
    <a href="/budget/register" class="underline hover:text-amber-800">Opret konto</a>
</div>
{% endif %}
```

**Step 4: Ensure `demo_advanced` is passed in all template contexts**

Verify that every route passing `demo_mode` also passes `demo_advanced`. Check that the following routes include `"demo_advanced": advanced` (or `"demo_advanced": False` for non-demo): dashboard, income, expenses, settings, about page, categories, accounts.

For non-demo routes and routes that don't branch on demo, add `"demo_advanced": False` to the template context (or `"demo_advanced": is_demo_advanced(request)` if the route has auth).

**Step 5: Run E2E test to verify it passes**

Run: `python -m pytest e2e/test_demo.py::TestDemoToggle -v`
Expected: PASS — all 4 tests green.

**Step 6: Run full E2E test suite**

Run: `python -m pytest e2e/ -v`
Expected: All existing demo tests still pass.

**Step 7: Commit**

```bash
git add templates/base.html src/api.py
git commit -m "feat: add simple/advanced toggle to demo banner (#101)"
```

---

### Task 5: Update CLAUDE.md with maintenance mandate

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add the mandate**

Add a new section to `CLAUDE.md` after section 5:

```markdown
## 6. Demo Data Maintenance
- **Advanced Demo:** When adding new user-facing features, update the advanced demo data in `src/database.py` to showcase the feature.
- Always offer to update the advanced demo when implementing features that add new UI elements or data types.
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add demo data maintenance mandate to CLAUDE.md (#101)"
```

---

### Task 6: Final verification

**Step 1: Run full test suite**

```bash
python -m pytest tests/test_api.py -x -q
python -m pytest e2e/ -v
```

Expected: All tests pass.

**Step 2: Manual smoke test**

Start the server (`python -m src.api`), navigate to `/budget/demo`, verify:
1. Demo banner shows "Simpel / Avanceret" toggle
2. Default is simple (no accounts visible)
3. Clicking "Avanceret" reloads with accounts visible
4. Clicking "Simpel" switches back
5. Navigate to expenses, income — toggle persists
6. Income page shows "Børnepenge" in advanced mode
