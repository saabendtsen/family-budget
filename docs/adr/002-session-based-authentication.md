---
type: adr
number: 002
status: accepted
date: 2024-01-10
---

# ADR-002: Session-Based Authentication

## Status
Accepted

## Context

The Family Budget application needs user authentication to protect budget data. The authentication system must:

1. Securely identify users across requests
2. Protect against XSS and CSRF attacks
3. Work with server-side rendered templates (Jinja2)
4. Be simple to implement and maintain
5. Support 30-day "remember me" functionality
6. Allow logout from all devices

### Options Considered

**1. Session-based authentication** (cookies + server-side storage)
- **Pros**: Simple, secure, works great with SSR, easy to invalidate
- **Cons**: Requires server-side storage, doesn't scale horizontally easily

**2. JWT tokens** (stateless)
- **Pros**: Stateless, scales horizontally, works with SPAs
- **Cons**: Hard to invalidate, larger payload, overkill for SSR app

**3. OAuth 2.0** (third-party)
- **Pros**: Offload auth to provider, social login
- **Cons**: Complex, requires internet, privacy concerns, dependency

## Decision

Use **session-based authentication** with:
- **Session storage**: File-based (`data/sessions.json`)
- **Session tokens**: 32-byte random tokens (SHA-256 hashed before storage)
- **Cookie attributes**: httponly, secure, samesite=lax
- **Session lifetime**: 30 days

## Rationale

### Why Sessions Over JWT

1. **Server-side rendering**: Application uses Jinja2 templates, not a SPA
   - Sessions are natural fit for SSR
   - No need for client-side token management
   - Simpler mental model

2. **Easy invalidation**: Can logout users immediately
   - Delete session from storage
   - User is logged out on next request
   - JWTs can't be invalidated without complex blacklisting

3. **Smaller cookies**: Session ID is small (32 bytes vs ~200+ bytes for JWT)
   - Faster request/response
   - Lower bandwidth

4. **Simpler implementation**: No need for JWT libraries or key management
   - Fewer dependencies
   - Less code to audit
   - Easier to understand

5. **Security**: httponly cookies prevent XSS token theft
   - JWTs often stored in localStorage (vulnerable to XSS)
   - Sessions in httponly cookies are XSS-safe

### File-Based vs Database vs Redis

**Chose file-based** (`data/sessions.json`) because:
- **Simple**: Single JSON file, easy to backup
- **Low user count**: <100 users expected, no scale issues
- **No additional services**: No Redis/Memcached to manage
- **Fast enough**: File read/write is fast for small data

**Trade-off**: Doesn't support horizontal scaling
- **Acceptable because**: Single-server deployment
- **Future migration**: Can switch to Redis if needed

### Security Properties

1. **Token generation**: `secrets.token_urlsafe(32)` - cryptographically secure
2. **Token storage**: SHA-256 hashed before storing in file
3. **Cookie security**:
   - `httponly=True` - Prevents JavaScript access (XSS protection)
   - `secure=True` - HTTPS-only transmission (MITM protection)
   - `samesite="lax"` - CSRF protection (blocks cross-site requests)
4. **Rate limiting**: 5 failed login attempts per 5 minutes (IP-based)

## Implementation

### Session Management Code

**Location**: `src/api.py:134-161`

```python
import hashlib
import json
import secrets
from pathlib import Path

SESSIONS_FILE = Path(__file__).parent.parent / "data" / "sessions.json"

def hash_token(token: str) -> str:
    """Hash session token with SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()

def load_sessions() -> dict[str, int]:
    """Load sessions from file. Returns {hashed_token: user_id}."""
    if not SESSIONS_FILE.exists():
        return {}
    with open(SESSIONS_FILE, 'r') as f:
        return json.load(f)

def save_sessions(sessions: dict[str, int]):
    """Save sessions to file."""
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f, indent=2)

# In-memory session store (loaded at startup)
SESSIONS = load_sessions()
```

### Login Flow

**Location**: `src/api.py:261-290`

```python
@app.post("/budget/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Login with username and password."""
    user = db.authenticate_user(username, password)
    if user:
        # Generate session token
        session_id = secrets.token_urlsafe(32)

        # Store hashed token mapped to user_id
        SESSIONS[hash_token(session_id)] = user.id
        save_sessions(SESSIONS)

        # Set secure cookie
        response = RedirectResponse(url="/budget/", status_code=303)
        response.set_cookie(
            key="budget_session",
            value=session_id,              # Plain token in cookie
            httponly=True,                  # No JavaScript access
            secure=True,                    # HTTPS only
            samesite="lax",                 # CSRF protection
            max_age=86400 * 30              # 30 days
        )
        return response
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Forkert brugernavn eller adgangskode"
        })
```

### Authentication Check

**Location**: `src/api.py:237-242`

```python
def get_user_id(request: Request) -> Optional[int]:
    """Get user ID from session cookie. Returns None if not logged in."""
    session_id = request.cookies.get("budget_session")
    if not session_id:
        return None
    return SESSIONS.get(hash_token(session_id))
```

### Logout Flow

**Location**: `src/api.py:548-565`

```python
@app.get("/budget/logout")
async def logout(request: Request):
    """Clear session and logout."""
    session_id = request.cookies.get("budget_session")
    if session_id:
        hashed = hash_token(session_id)
        if hashed in SESSIONS:
            del SESSIONS[hashed]
            save_sessions(SESSIONS)

    response = RedirectResponse("/budget/login", status_code=303)
    response.delete_cookie("budget_session")
    return response
```

## Consequences

### Positive

1. **Simple and secure**: Easy to understand, hard to misuse
2. **XSS protection**: httponly cookies can't be accessed by JavaScript
3. **CSRF protection**: samesite=lax prevents cross-site attacks
4. **Easy logout**: Delete session immediately, user logged out
5. **Works with SSR**: Natural fit for Jinja2 templates
6. **No external dependencies**: No JWT libraries needed

### Negative

1. **Not horizontally scalable**: File-based sessions tied to single server
   - **Mitigation**: Can migrate to Redis if needed
   - **Acceptable**: Single-server deployment planned

2. **File I/O overhead**: Every session change writes to disk
   - **Mitigation**: Infrequent writes (login/logout only)
   - **Performance**: Fast enough for <100 users

3. **No automatic session cleanup**: Old sessions stay in file
   - **Mitigation**: Could add cleanup on startup (check max_age)
   - **Impact**: Minimal (sessions.json stays small)

## For AI Agents

### ✅ DO - Authentication Pattern

**Check if user is logged in:**
```python
user_id = get_user_id(request)
if user_id is None:
    return RedirectResponse("/budget/login", status_code=303)
```

**Create session on login:**
```python
session_id = secrets.token_urlsafe(32)
SESSIONS[hash_token(session_id)] = user.id
save_sessions(SESSIONS)

response.set_cookie(
    key="budget_session",
    value=session_id,
    httponly=True,
    secure=True,
    samesite="lax",
    max_age=86400 * 30
)
```

**Destroy session on logout:**
```python
session_id = request.cookies.get("budget_session")
if session_id:
    hashed = hash_token(session_id)
    if hashed in SESSIONS:
        del SESSIONS[hashed]
        save_sessions(SESSIONS)

response.delete_cookie("budget_session")
```

### ❌ DON'T

- **Never store plain tokens** in sessions.json (always hash first)
- **Never use `random`** for token generation (use `secrets`)
- **Never omit cookie security flags** (httponly, secure, samesite)
- **Never expose sessions to client** (no API endpoint returning sessions)
- **Never forget to save_sessions()** after modifying SESSIONS dict

### Example: Protected Route

```python
@app.get("/budget/expenses")
async def expenses(request: Request):
    """Protected route - requires login."""
    # Check authentication
    user_id = get_user_id(request)
    if user_id is None:
        return RedirectResponse("/budget/login", status_code=303)

    # Get user data
    expenses = db.get_all_expenses(user_id)

    return templates.TemplateResponse("expenses.html", {
        "request": request,
        "expenses": expenses
    })
```

## Migration Path (If Needed)

If we need to scale horizontally in the future:

### Option 1: Redis Sessions
```python
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

def save_session(token_hash: str, user_id: int):
    r.setex(token_hash, 86400 * 30, user_id)  # 30 day expiry

def get_session(token_hash: str) -> Optional[int]:
    user_id = r.get(token_hash)
    return int(user_id) if user_id else None
```

### Option 2: Database Sessions
```sql
CREATE TABLE sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL
);
```

Both migrations are straightforward - just replace file operations with Redis/DB operations.

## References

- **OWASP Session Management Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- **Cookie security**: https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies
- **CSRF protection**: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- **Pattern guide**: `../../PATTERNS.md` → Session Management Pattern
- **Implementation**: `../../src/api.py:134-290`
