# Templates Module - AI Agent Guide

Guide to Jinja2 templates in Family Budget.

## Template Overview

All templates use **Jinja2** with **TailwindCSS** (CDN) and **Lucide** icons.

| Template | Purpose | Route | Lines |
|----------|---------|-------|-------|
| `base.html` | Master layout | All pages | 289 |
| `dashboard.html` | Budget overview | `/budget/` | 409 |
| `expenses.html` | Expense management | `/budget/expenses` | 358 |
| `categories.html` | Category management | `/budget/categories` | 348 |
| `income.html` | Income management | `/budget/income` | 244 |
| `help.html` | User guide | `/budget/help` | 193 |
| `settings.html` | User settings | `/budget/settings` | 115 |
| `login.html` | Login page | `/budget/login` | 101 |
| `register.html` | Registration | `/budget/register` | 77 |
| `forgot-password.html` | Password reset request | `/budget/forgot-password` | 67 |
| `reset-password.html` | Password reset form | `/budget/reset-password/{token}` | 80 |
| `privacy.html` | Privacy policy | `/budget/privacy` | 143 |
| `feedback.html` | Feedback form | `/budget/feedback` | 116 |

**Total**: 13 templates, 2,540 lines

## Base Template (`base.html`)

Master template with:
- Navigation header
- Dark mode toggle
- Footer
- TailwindCSS CDN
- Lucide icons CDN
- Mobile responsive layout

**Structure**:
```jinja2
<!DOCTYPE html>
<html lang="da">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Family Budget{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 dark:bg-gray-900">
    <nav><!-- Navigation --></nav>

    <main>
        {% block content %}{% endblock %}
    </main>

    <footer><!-- Footer --></footer>

    <script src="https://unpkg.com/lucide@latest"></script>
    <script>lucide.createIcons();</script>
</body>
</html>
```

## Template Inheritance Pattern

All pages extend base:

```jinja2
{% extends "base.html" %}

{% block title %}Page Title - Family Budget{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Page Title
    </h1>

    <!-- Page content -->
</div>
{% endblock %}
```

## Common Patterns

### Modal Pattern

See `PATTERNS.md` → Modal Pattern for full details.

**Quick reference** (`expenses.html:151-222`):

```jinja2
<div id="modal" class="fixed inset-0 bg-black/50 flex items-end justify-center z-50 hidden">
    <div class="bg-white dark:bg-gray-800 w-full max-w-md rounded-t-2xl p-6 animate-slide-up">
        <div class="flex justify-between items-center mb-4">
            <h2 id="modal-title" class="text-xl font-bold text-gray-900 dark:text-white">
                Modal Title
            </h2>
            <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <i data-lucide="x" class="w-6 h-6"></i>
            </button>
        </div>
        <form method="post" action="/budget/endpoint" class="space-y-4">
            <!-- Form fields -->
        </form>
    </div>
</div>
```

### Form Input Pattern

```jinja2
<div>
    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        Label
    </label>
    <input
        type="text"
        name="field"
        placeholder="Hint text"
        class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        required
    >
</div>
```

### Jinja2 Control Flow

**Conditional rendering**:
```jinja2
{% if user_id %}
    <p>Logged in</p>
{% else %}
    <p>Not logged in</p>
{% endif %}
```

**Loops**:
```jinja2
{% for expense in expenses %}
    <div>{{ expense.name }}: {{ expense.amount }} kr.</div>
{% endfor %}
```

**Empty state**:
```jinja2
{% if expenses %}
    <!-- Show expenses -->
{% else %}
    <p>Ingen udgifter endnu</p>
{% endif %}
```

## Tailwind Class Conventions

### Color Palette

- **Primary**: Green (`#10b981`)
  - Buttons: `bg-primary hover:bg-primary/90`
- **Gray scale**: gray-50 to gray-900
  - Light mode: gray-50 backgrounds, gray-900 text
  - Dark mode: gray-900 backgrounds, white text

### Standard Classes

**Container**:
```html
<div class="container mx-auto px-4 py-6">
```

**Card**:
```html
<div class="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
```

**Button (primary)**:
```html
<button class="w-full bg-primary hover:bg-primary/90 text-white font-medium py-3 px-4 rounded-xl transition-colors">
    Text
</button>
```

**Button (secondary)**:
```html
<button class="w-full bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-medium py-3 px-4 rounded-xl transition-colors">
    Text
</button>
```

### Dark Mode

**Always include dark mode variants**:

```html
<div class="bg-white dark:bg-gray-800">
    <p class="text-gray-900 dark:text-white">Text</p>
    <input class="bg-white dark:bg-gray-700 text-gray-900 dark:text-white border-gray-300 dark:border-gray-600">
</div>
```

**Dark mode toggle** (in `base.html`):
```javascript
function toggleDarkMode() {
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('darkMode', document.documentElement.classList.contains('dark'));
}
```

## Lucide Icons

**Icon usage**:
```html
<i data-lucide="icon-name" class="w-5 h-5"></i>
```

**Common icons**:
- `home` - Home/dashboard
- `wallet` - Income
- `receipt` - Expenses
- `tag` - Categories
- `settings` - Settings
- `help-circle` - Help
- `log-in`, `log-out` - Authentication
- `plus` - Add
- `pencil` - Edit
- `trash-2` - Delete
- `x` - Close

**Icon browser**: https://lucide.dev/icons/

## Template Variables

Variables passed from routes are available in templates:

**Dashboard** (`dashboard.html`):
```python
# In route
return templates.TemplateResponse("dashboard.html", {
    "request": request,
    "income_list": income_list,
    "expenses": expenses,
    "total_income": total_income,
    "total_expenses": total_expenses,
    "leftover": leftover
})
```

```jinja2
<!-- In template -->
<p>Total: {{ total_income }} kr.</p>

{% for expense in expenses %}
    <p>{{ expense.name }}: {{ expense.amount }} kr.</p>
{% endfor %}
```

## Template Filters

**Currency formatting**:
```jinja2
{{ amount|format_currency }}
<!-- or use helper function -->
{{ format_currency(amount) }}
```

**JSON encoding** (for JavaScript):
```jinja2
<script>
const data = {{ data|tojson }};
</script>
```

**Escaping** (auto by default):
```jinja2
{{ user_input }}  <!-- Auto-escaped, safe from XSS -->
{{ html_content|safe }}  <!-- Disable escaping (use carefully!) -->
```

## JavaScript in Templates

**Inline scripts** at bottom of template:

```jinja2
{% block content %}
<!-- Template content -->
{% endblock %}

<script>
function openModal() {
    document.getElementById('modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('modal').classList.add('hidden');
}

// Initialize icons
lucide.createIcons();
</script>
```

**Best practices**:
- Keep JavaScript minimal
- Place at bottom of template
- Use vanilla JavaScript (no jQuery)
- Initialize Lucide icons after DOM ready

## Adding a New Template

### Step 1: Create Template File

`templates/new-page.html`:

```jinja2
{% extends "base.html" %}

{% block title %}New Page - Family Budget{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        New Page
    </h1>

    <!-- Content -->
</div>
{% endblock %}
```

### Step 2: Create Route

In `src/api.py`:

```python
@app.get("/budget/new-page", response_class=HTMLResponse)
async def new_page(request: Request):
    """New page description."""
    return templates.TemplateResponse("new-page.html", {
        "request": request
    })
```

### Step 3: Add Navigation Link

In `templates/base.html` (if needed):

```html
<a href="/budget/new-page" class="...">New Page</a>
```

## Troubleshooting

**Template not found**:
- Check filename matches route
- Ensure file is in `templates/` directory
- Restart server after creating new template

**Variables undefined**:
- Check variable passed in context dict
- Verify spelling in template matches context

**Icons not showing**:
- Ensure `lucide.createIcons()` called
- Check icon name at https://lucide.dev/
- Verify `data-lucide` attribute set

**Dark mode not working**:
- Check `dark:` variants on classes
- Verify dark mode script in base.html
- Check localStorage for dark mode preference

## Related Documentation

- **Patterns**: `../PATTERNS.md` → Frontend Patterns
- **ADR**: `../docs/adr/005-jinja2-templating.md`
- **Tailwind Docs**: https://tailwindcss.com/
- **Lucide Icons**: https://lucide.dev/
- **Jinja2 Docs**: https://jinja.palletsprojects.com/
