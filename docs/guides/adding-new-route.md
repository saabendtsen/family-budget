# Guide: Adding a New Route

Step-by-step process for adding new routes to Family Budget.

## Prerequisites

Before adding a route, ensure you:
1. ✅ Understand the purpose of the route
2. ✅ Know if it requires authentication
3. ✅ Have read `PATTERNS.md` → FastAPI Route Pattern
4. ✅ Have read `src/API-REFERENCE.md` to see existing routes

## Step 1: Determine Route Details

Answer these questions:

| Question | Example |
|----------|---------|
| **Path** | `/budget/export` |
| **Method** | GET or POST? |
| **Auth required** | Yes / No / Optional |
| **Template** | `templates/export.html` or redirect? |
| **Purpose** | What does this route do? |

## Step 2: Choose Insertion Point

Routes are organized by feature in `src/api.py`:

| Lines | Feature | Add here if... |
|-------|---------|----------------|
| 253-530 | Authentication | Login, register, password reset |
| 533-617 | Dashboard | Main dashboard, demo mode |
| 619-682 | Income | Income management |
| 685-817 | Expenses | Expense management |
| 820-930 | Categories | Category management |
| 933-1104 | Static Pages | Help, privacy, feedback |
| 1107-1168 | API Endpoints | JSON endpoints |
| 1171-1256 | Settings | User settings |

**Add your route in the logical section** (e.g., new expense feature goes with expenses).

## Step 3: Write the Route

### GET Route (Display Page)

```python
@app.get("/budget/[route]", response_class=HTMLResponse)
async def route_name(request: Request):
    """One-line description of what this route does.

    Agent context:
    - Purpose: Why this route exists
    - Auth: Required/Optional/None
    - Template: Template file used
    - Related: Related routes/functions
    """
    # Step 1: Check authentication (if required)
    user_id = get_user_id(request)
    if user_id is None:
        return RedirectResponse("/budget/login", status_code=303)

    # Step 2: Get data from database
    data = db.get_something(user_id)

    # Step 3: Render template
    return templates.TemplateResponse("template.html", {
        "request": request,
        "data": data,
    })
```

### POST Route (Form Submission)

```python
@app.post("/budget/[route]")
async def route_action(
    request: Request,
    field1: str = Form(...),
    field2: str = Form(...),
):
    """Process form submission."""
    # Step 1: Check authentication
    user_id = get_user_id(request)
    if user_id is None:
        return RedirectResponse("/budget/login", status_code=303)

    # Step 2: Validate input
    if len(field1) < 3:
        return templates.TemplateResponse("template.html", {
            "request": request,
            "error": "Field 1 must be at least 3 characters"
        })

    # Step 3: Process data
    try:
        db.do_something(user_id, field1, field2)

        # Step 4: Redirect on success (POST-Redirect-GET pattern)
        return RedirectResponse("/budget/route", status_code=303)
    except Exception as e:
        logger.error(f"Error: {e}")
        return templates.TemplateResponse("template.html", {
            "request": request,
            "error": "En fejl opstod"
        })
```

## Step 4: Create Template (if needed)

If your route needs a template, create `templates/[name].html`:

```html
{% extends "base.html" %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Page Title
    </h1>

    <!-- Your content -->
</div>
{% endblock %}
```

See `templates/CLAUDE.md` for template patterns.

## Step 5: Update Documentation

### A. Add to `src/API-REFERENCE.md`

Add your route to the appropriate section:

```markdown
### GET /budget/your-route

**Location**: `src/api.py:XXX-YYY`

**Purpose**: Description

**Auth**: Required/Optional/None

**Template**: `templates/your-template.html`

**Returns**: Description

**Database Functions**:
- `db.function_name()` - Description (line XXX)
```

Add to summary table at bottom.

### B. Update Root `CLAUDE.md` Endpoints Table

Add your route to the endpoints table:

```markdown
| `/budget/your-route` | Description |
```

## Step 6: Add Database Functions (if needed)

If you need new database operations, see `docs/guides/database-operations.md`.

## Step 7: Write Tests

Add tests to `tests/test_api.py`:

```python
class TestYourFeature:
    """Tests for your feature routes."""

    def test_route_requires_auth(self, client):
        """Test that route requires authentication."""
        response = client.get("/budget/your-route")
        assert response.status_code == 303  # Redirect to login
        assert response.headers["location"] == "/budget/login"

    def test_route_success(self, authenticated_client):
        """Test successful route access."""
        response = authenticated_client.get("/budget/your-route")
        assert response.status_code == 200
        assert b"Expected Content" in response.content

    def test_route_post(self, authenticated_client):
        """Test form submission."""
        response = authenticated_client.post("/budget/your-route", data={
            "field1": "value1",
            "field2": "value2",
        })
        assert response.status_code == 303  # Redirect after POST
```

See `docs/guides/testing-strategy.md` for testing patterns.

## Step 8: Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::TestYourFeature::test_route_success
```

## Checklist

Before committing:

- [ ] Route follows `/budget/[name]` convention
- [ ] Docstring includes agent context (Purpose, Auth, Template, Related)
- [ ] Authentication check if required
- [ ] Input validation on backend
- [ ] POST routes use 303 redirect (POST-Redirect-GET pattern)
- [ ] Error handling with user-friendly Danish messages
- [ ] Route added to `src/API-REFERENCE.md`
- [ ] Route added to root `CLAUDE.md` endpoints table
- [ ] Template created (if needed)
- [ ] Tests written
- [ ] All tests pass

## Common Patterns

### Dynamic Form Fields (like Income)

For forms with variable number of inputs:

```python
@app.post("/budget/route")
async def route(request: Request):
    user_id = get_user_id(request)
    if user_id is None:
        return RedirectResponse("/budget/login", status_code=303)

    form = await request.form()

    i = 0
    while True:
        field = form.get(f'field_{i}')
        if not field:
            break

        # Process field
        db.do_something(user_id, field)
        i += 1

    return RedirectResponse("/budget/route", status_code=303)
```

### Danish Amount Parsing

For amount inputs:

```python
from src.api import parse_danish_amount

amount_str = form_data.get('amount')  # "25.000,50"
amount = parse_danish_amount(amount_str)  # 25000.50
```

### Optional Authentication

For routes that work with or without login:

```python
@app.get("/budget/route")
async def route(request: Request):
    user_id = get_user_id(request)  # May be None

    # Show different content based on auth
    if user_id:
        data = db.get_user_data(user_id)
    else:
        data = get_public_data()

    return templates.TemplateResponse("template.html", {
        "request": request,
        "data": data,
        "is_logged_in": user_id is not None
    })
```

## Troubleshooting

### Route not found (404)

- Check path spelling in `@app.get()`
- Ensure server restarted after code change
- Check that route is added before `app` is run

### Redirect loop

- Check authentication logic
- Ensure `/budget/login` doesn't redirect to itself
- Verify `get_user_id()` returns correct value

### Form data not received

- Check form field `name` attributes match `Form(...)` parameters
- Ensure form `method="post"`
- Check `action` attribute points to correct route

### Template not found

- Check template path in `templates.TemplateResponse()`
- Ensure template file exists in `templates/` directory
- Check file extension is `.html`

## Related Documentation

- **Patterns**: `../../PATTERNS.md` → FastAPI Route Pattern
- **API Reference**: `../../src/API-REFERENCE.md`
- **Database Guide**: `./database-operations.md`
- **Testing Guide**: `./testing-strategy.md`
- **Template Guide**: `../../templates/CLAUDE.md`
