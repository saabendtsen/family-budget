"""FastAPI application for Family Budget."""

import json
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import database as db

# Load environment
load_dotenv(Path.home() / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

# PIN from environment
BUDGET_PIN = os.getenv("BUDGET_PIN", "1234")

# Session management (file-based for persistence)
SESSIONS_FILE = Path(__file__).parent.parent / "data" / "sessions.json"


def load_sessions() -> set:
    """Load sessions from file."""
    if SESSIONS_FILE.exists():
        try:
            with open(SESSIONS_FILE) as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_sessions(sessions: set):
    """Save sessions to file."""
    SESSIONS_FILE.parent.mkdir(exist_ok=True)
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(list(sessions), f)


SESSIONS = load_sessions()

# Templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Create app
app = FastAPI(
    title="Family Budget",
    description="Budget overview for Søren and Anne",
    version="1.0.0"
)


# =============================================================================
# Template helpers
# =============================================================================

def format_currency(amount: float) -> str:
    """Format amount as Danish currency."""
    return f"{amount:,.0f}".replace(",", ".") + " kr"


# Add to Jinja2 globals
templates.env.globals["format_currency"] = format_currency


# =============================================================================
# Authentication
# =============================================================================

def check_auth(request: Request) -> bool:
    """Check if request is authenticated."""
    session_id = request.cookies.get("budget_session")
    return session_id in SESSIONS


@app.get("/budget/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page."""
    if check_auth(request):
        return RedirectResponse(url="/budget/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/budget/login")
async def login(request: Request, pin: str = Form(...)):
    """Login with PIN."""
    if pin == BUDGET_PIN:
        session_id = secrets.token_urlsafe(32)
        SESSIONS.add(session_id)
        save_sessions(SESSIONS)

        response = RedirectResponse(url="/budget/", status_code=303)
        response.set_cookie(
            key="budget_session",
            value=session_id,
            httponly=True,
            max_age=86400 * 30  # 30 days
        )
        return response
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Forkert PIN"}
        )


@app.get("/budget/logout")
async def logout(request: Request):
    """Logout and clear session."""
    session_id = request.cookies.get("budget_session")
    if session_id in SESSIONS:
        SESSIONS.remove(session_id)
        save_sessions(SESSIONS)

    response = RedirectResponse(url="/budget/login", status_code=303)
    response.delete_cookie("budget_session")
    return response


# =============================================================================
# Dashboard
# =============================================================================

@app.get("/budget/", response_class=HTMLResponse)
@app.get("/budget", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    # Get data
    incomes = db.get_all_income()
    total_income = db.get_total_income()
    total_expenses = db.get_total_monthly_expenses()
    remaining = total_income - total_expenses

    # Get expenses grouped by category with totals
    expenses_by_category = db.get_expenses_by_category()
    category_totals = db.get_category_totals()

    # Calculate percentages for progress bars
    category_percentages = {}
    if total_expenses > 0:
        for cat, total in category_totals.items():
            category_percentages[cat] = (total / total_expenses) * 100

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "incomes": incomes,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "remaining": remaining,
            "expenses_by_category": expenses_by_category,
            "category_totals": category_totals,
            "category_percentages": category_percentages,
        }
    )


# =============================================================================
# Income
# =============================================================================

@app.get("/budget/income", response_class=HTMLResponse)
async def income_page(request: Request):
    """Income edit page."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    incomes = db.get_all_income()
    return templates.TemplateResponse(
        "income.html",
        {"request": request, "incomes": incomes}
    )


@app.post("/budget/income")
async def update_income(
    request: Request,
    soeren: float = Form(...),
    anne: float = Form(...)
):
    """Update income values."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    db.update_income("Søren", soeren)
    db.update_income("Anne", anne)

    return RedirectResponse(url="/budget/", status_code=303)


# =============================================================================
# Expenses
# =============================================================================

@app.get("/budget/expenses", response_class=HTMLResponse)
async def expenses_page(request: Request):
    """Expenses management page."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    expenses = db.get_all_expenses()
    expenses_by_category = db.get_expenses_by_category()
    category_totals = db.get_category_totals()
    categories = db.get_all_categories()

    return templates.TemplateResponse(
        "expenses.html",
        {
            "request": request,
            "expenses": expenses,
            "expenses_by_category": expenses_by_category,
            "category_totals": category_totals,
            "categories": categories,
        }
    )


@app.post("/budget/expenses/add")
async def add_expense(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    amount: float = Form(...),
    frequency: str = Form(...)
):
    """Add a new expense."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    db.add_expense(name, category, amount, frequency)
    return RedirectResponse(url="/budget/expenses", status_code=303)


@app.post("/budget/expenses/{expense_id}/delete")
async def delete_expense(request: Request, expense_id: int):
    """Delete an expense."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    db.delete_expense(expense_id)
    return RedirectResponse(url="/budget/expenses", status_code=303)


@app.post("/budget/expenses/{expense_id}/edit")
async def edit_expense(
    request: Request,
    expense_id: int,
    name: str = Form(...),
    category: str = Form(...),
    amount: float = Form(...),
    frequency: str = Form(...)
):
    """Edit an expense."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    db.update_expense(expense_id, name, category, amount, frequency)
    return RedirectResponse(url="/budget/expenses", status_code=303)


# =============================================================================
# Categories
# =============================================================================

@app.get("/budget/categories", response_class=HTMLResponse)
async def categories_page(request: Request):
    """Categories management page."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    categories = db.get_all_categories()
    # Get usage count for each category
    category_usage = {cat.name: db.get_category_usage_count(cat.name) for cat in categories}

    return templates.TemplateResponse(
        "categories.html",
        {
            "request": request,
            "categories": categories,
            "category_usage": category_usage,
        }
    )


@app.post("/budget/categories/add")
async def add_category(
    request: Request,
    name: str = Form(...),
    icon: str = Form(...)
):
    """Add a new category."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    db.add_category(name, icon)
    return RedirectResponse(url="/budget/categories", status_code=303)


@app.post("/budget/categories/{category_id}/edit")
async def edit_category(
    request: Request,
    category_id: int,
    name: str = Form(...),
    icon: str = Form(...)
):
    """Edit a category."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    db.update_category(category_id, name, icon)
    return RedirectResponse(url="/budget/categories", status_code=303)


@app.post("/budget/categories/{category_id}/delete")
async def delete_category(request: Request, category_id: int):
    """Delete a category."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    db.delete_category(category_id)
    return RedirectResponse(url="/budget/categories", status_code=303)


# =============================================================================
# Run with: python -m src.api
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)
