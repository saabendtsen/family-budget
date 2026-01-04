"""FastAPI application for Family Budget."""

import fcntl
import hashlib
import json
import logging
import secrets
import sqlite3
import time
from collections import defaultdict
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from . import database as db

# Initialize database at startup
db.init_db()

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Rate limiting
# =============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting for login attempts."""

    def __init__(self, app, max_attempts: int = 5, window_seconds: int = 300):
        super().__init__(app)
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Only rate limit login POST requests
        if request.url.path == "/budget/login" and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()

            # Clean old attempts for this IP
            self.attempts[client_ip] = [
                t for t in self.attempts[client_ip]
                if now - t < self.window_seconds
            ]

            # Remove IP key entirely if no recent attempts (prevents memory leak)
            if not self.attempts[client_ip]:
                del self.attempts[client_ip]
            else:
                # Check if rate limited
                if len(self.attempts[client_ip]) >= self.max_attempts:
                    return HTMLResponse(
                        content="For mange login forsøg. Prøv igen om 5 minutter.",
                        status_code=429
                    )

            # Record this attempt
            self.attempts[client_ip].append(now)

        return await call_next(request)

# Load environment
load_dotenv(Path.home() / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")


# Session management (file-based for persistence)
# Sessions map hashed tokens to user_ids
SESSIONS_FILE = Path(__file__).parent.parent / "data" / "sessions.json"


def hash_token(token: str) -> str:
    """Hash a session token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def load_sessions() -> dict:
    """Load sessions from file with file locking.

    Returns dict mapping hashed tokens to user_ids.
    Uses fcntl.LOCK_SH (shared lock) for reading.
    """
    if SESSIONS_FILE.exists():
        try:
            with open(SESSIONS_FILE) as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                    # Migrate from old format (list) to new format (dict)
                    if isinstance(data, list):
                        return {}  # Clear old sessions, users need to re-login
                    return data
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (json.JSONDecodeError, OSError) as e:
            # Log corruption/permission issues but continue with empty sessions
            logging.warning(f"Could not load sessions file: {e}")
    return {}


def save_sessions(sessions: dict):
    """Save sessions to file with file locking.

    Uses fcntl.LOCK_EX (exclusive lock) for writing to prevent
    race conditions with concurrent login/logout operations.
    """
    SESSIONS_FILE.parent.mkdir(exist_ok=True)
    with open(SESSIONS_FILE, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            json.dump(sessions, f)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


SESSIONS = load_sessions()  # Maps hashed tokens to user_ids

# Templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Create app
app = FastAPI(
    title="Family Budget",
    description="Budget overview for Søren and Anne",
    version="1.0.0"
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, max_attempts=5, window_seconds=300)


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

DEMO_SESSION_ID = "demo"  # Special marker for demo mode


def check_auth(request: Request) -> bool:
    """Check if request is authenticated (including demo mode)."""
    session_id = request.cookies.get("budget_session")
    if not session_id:
        return False
    # Demo mode
    if session_id == DEMO_SESSION_ID:
        return True
    # Compare hashed token
    return hash_token(session_id) in SESSIONS


def get_user_id(request: Request) -> int | None:
    """Get user_id from session. Returns None for demo mode or invalid sessions."""
    session_id = request.cookies.get("budget_session")
    if not session_id or session_id == DEMO_SESSION_ID:
        return None
    hashed = hash_token(session_id)
    return SESSIONS.get(hashed)


def is_demo_mode(request: Request) -> bool:
    """Check if request is in demo mode (read-only)."""
    return request.cookies.get("budget_session") == DEMO_SESSION_ID


@app.get("/budget/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page."""
    if check_auth(request):
        return RedirectResponse(url="/budget/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/budget/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Login with username and password."""
    user = db.authenticate_user(username, password)
    if user:
        session_id = secrets.token_urlsafe(32)
        # Store hashed token mapped to user_id
        SESSIONS[hash_token(session_id)] = user.id
        save_sessions(SESSIONS)

        response = RedirectResponse(url="/budget/", status_code=303)
        response.set_cookie(
            key="budget_session",
            value=session_id,
            httponly=True,
            secure=True,       # Only send over HTTPS
            samesite="lax",    # CSRF protection
            max_age=86400 * 30  # 30 days
        )
        return response
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Forkert brugernavn eller adgangskode"}
        )


@app.get("/budget/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Show registration page."""
    if check_auth(request):
        return RedirectResponse(url="/budget/", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/budget/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...)
):
    """Register a new user."""
    # Validate input
    if len(username) < 3:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Brugernavn skal være mindst 3 tegn"}
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Adgangskode skal være mindst 6 tegn"}
        )

    if password != password_confirm:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Adgangskoderne matcher ikke"}
        )

    # Create user
    new_user_id = db.create_user(username, password)
    if new_user_id is None:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Brugernavnet er allerede taget"}
        )

    # Auto-login after registration
    session_id = secrets.token_urlsafe(32)
    SESSIONS[hash_token(session_id)] = new_user_id
    save_sessions(SESSIONS)

    response = RedirectResponse(url="/budget/", status_code=303)
    response.set_cookie(
        key="budget_session",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400 * 30
    )
    return response


@app.get("/budget/demo")
async def demo_mode(request: Request):
    """Enter demo mode with pre-filled example data."""
    response = RedirectResponse(url="/budget/", status_code=303)
    response.set_cookie(
        key="budget_session",
        value=DEMO_SESSION_ID,
        httponly=True,
        secure=True,       # Only send over HTTPS
        samesite="lax",
        max_age=3600  # Demo expires after 1 hour
    )
    return response


@app.get("/budget/logout")
async def logout(request: Request):
    """Logout and clear session."""
    session_id = request.cookies.get("budget_session")
    if session_id:
        hashed = hash_token(session_id)
        if hashed in SESSIONS:
            del SESSIONS[hashed]
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

    demo = is_demo_mode(request)
    user_id = get_user_id(request)

    # Get data (demo or real)
    if demo:
        incomes = db.get_demo_income()
        total_income = db.get_demo_total_income()
        total_expenses = db.get_demo_total_expenses()
        expenses_by_category = db.get_demo_expenses_by_category()
        category_totals = db.get_demo_category_totals()
    else:
        incomes = db.get_all_income(user_id)
        total_income = db.get_total_income(user_id)
        total_expenses = db.get_total_monthly_expenses(user_id)
        expenses_by_category = db.get_expenses_by_category(user_id)
        category_totals = db.get_category_totals(user_id)

    remaining = total_income - total_expenses

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
            "demo_mode": demo,
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

    user_id = get_user_id(request)
    incomes = db.get_all_income(user_id)
    return templates.TemplateResponse(
        "income.html",
        {"request": request, "incomes": incomes, "demo_mode": is_demo_mode(request)}
    )


@app.post("/budget/income")
async def update_income(
    request: Request,
    person1_name: str = Form(...),
    person1_amount: float = Form(...),
    person2_name: str = Form(...),
    person2_amount: float = Form(...)
):
    """Update income values."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)
    if is_demo_mode(request):
        return RedirectResponse(url="/budget/", status_code=303)

    user_id = get_user_id(request)
    try:
        db.update_income(user_id, person1_name, person1_amount)
        db.update_income(user_id, person2_name, person2_amount)
    except sqlite3.Error as e:
        logger.error(f"Database error updating income: {e}")
        raise HTTPException(status_code=500, detail="Der opstod en fejl ved opdatering af indkomst")

    return RedirectResponse(url="/budget/", status_code=303)


# =============================================================================
# Expenses
# =============================================================================

@app.get("/budget/expenses", response_class=HTMLResponse)
async def expenses_page(request: Request):
    """Expenses management page."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    user_id = get_user_id(request)
    demo = is_demo_mode(request)

    if demo:
        expenses = db.get_demo_expenses()
        expenses_by_category = db.get_demo_expenses_by_category()
        category_totals = db.get_demo_category_totals()
    else:
        expenses = db.get_all_expenses(user_id)
        expenses_by_category = db.get_expenses_by_category(user_id)
        category_totals = db.get_category_totals(user_id)

    categories = db.get_all_categories()

    return templates.TemplateResponse(
        "expenses.html",
        {
            "request": request,
            "expenses": expenses,
            "expenses_by_category": expenses_by_category,
            "category_totals": category_totals,
            "categories": categories,
            "demo_mode": demo,
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
    if is_demo_mode(request):
        return RedirectResponse(url="/budget/expenses", status_code=303)

    user_id = get_user_id(request)
    try:
        db.add_expense(user_id, name, category, amount, frequency)
    except sqlite3.Error as e:
        logger.error(f"Database error adding expense: {e}")
        raise HTTPException(status_code=500, detail="Der opstod en fejl ved tilfoejelse af udgiften")
    return RedirectResponse(url="/budget/expenses", status_code=303)


@app.post("/budget/expenses/{expense_id}/delete")
async def delete_expense(request: Request, expense_id: int):
    """Delete an expense."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)
    if is_demo_mode(request):
        return RedirectResponse(url="/budget/expenses", status_code=303)

    user_id = get_user_id(request)
    try:
        db.delete_expense(expense_id, user_id)
    except sqlite3.Error as e:
        logger.error(f"Database error deleting expense: {e}")
        raise HTTPException(status_code=500, detail="Der opstod en fejl ved sletning af udgiften")
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
    if is_demo_mode(request):
        return RedirectResponse(url="/budget/expenses", status_code=303)

    user_id = get_user_id(request)
    try:
        db.update_expense(expense_id, user_id, name, category, amount, frequency)
    except sqlite3.Error as e:
        logger.error(f"Database error updating expense: {e}")
        raise HTTPException(status_code=500, detail="Der opstod en fejl ved opdatering af udgiften")
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
            "demo_mode": is_demo_mode(request),
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
    if is_demo_mode(request):
        return RedirectResponse(url="/budget/categories", status_code=303)

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
    if is_demo_mode(request):
        return RedirectResponse(url="/budget/categories", status_code=303)

    db.update_category(category_id, name, icon)
    return RedirectResponse(url="/budget/categories", status_code=303)


@app.post("/budget/categories/{category_id}/delete")
async def delete_category(request: Request, category_id: int):
    """Delete a category.

    Note: Categories are global (shared across all users). Deletion is allowed
    for any authenticated user, but only if the category is not in use.
    """
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)
    if is_demo_mode(request):
        return RedirectResponse(url="/budget/categories", status_code=303)

    try:
        success = db.delete_category(category_id)
        if not success:
            # Category is in use or doesn't exist
            raise HTTPException(
                status_code=400,
                detail="Kategorien kan ikke slettes - den er stadig i brug"
            )
    except sqlite3.Error as e:
        logger.error(f"Database error deleting category: {e}")
        raise HTTPException(status_code=500, detail="Der opstod en fejl ved sletning af kategorien")
    return RedirectResponse(url="/budget/categories", status_code=303)


# =============================================================================
# Help
# =============================================================================

@app.get("/budget/help", response_class=HTMLResponse)
async def help_page(request: Request):
    """User guide page."""
    if not check_auth(request):
        return RedirectResponse(url="/budget/login", status_code=303)

    return templates.TemplateResponse(
        "help.html",
        {"request": request, "demo_mode": is_demo_mode(request)}
    )


# =============================================================================
# Run with: python -m src.api
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)
