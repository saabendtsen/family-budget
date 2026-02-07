# Guide: Security Checklist

Security review checklist for Family Budget development.

## Pre-Commit Security Review

Run through this checklist before committing code with security implications.

## Authentication & Authorization

### ✅ Password Security

- [ ] Passwords hashed with PBKDF2 (600k iterations)
- [ ] Never store plain passwords
- [ ] Use `secrets` module for token generation (not `random`)
- [ ] Constant-time comparison for password verification
- [ ] Minimum password length enforced (8 characters)
- [ ] Password confirmation on registration
- [ ] No passwords in logs, error messages, or URLs

**Pattern**: `../../PATTERNS.md` → Password Hashing

### ✅ Session Security

- [ ] Session tokens are cryptographically random
- [ ] Session tokens hashed before storage (SHA-256)
- [ ] httponly flag set on session cookies
- [ ] secure flag set on session cookies (HTTPS only)
- [ ] samesite=lax for CSRF protection
- [ ] No session tokens in URLs or logs
- [ ] Session invalidated on logout

**Pattern**: `../../PATTERNS.md` → Session Management

### ✅ Authorization

- [ ] All protected routes check authentication
- [ ] User ID from session, never from form/URL
- [ ] Database queries include user_id in WHERE clause
- [ ] No user can access another user's data
- [ ] No mass assignment vulnerabilities

**Example**:
```python
# ✅ CORRECT
user_id = get_user_id(request)
if user_id is None:
    return RedirectResponse("/budget/login")
data = db.get_expenses(user_id)

# ❌ WRONG
user_id = request.query_params.get('user_id')  # Attacker controlled!
```

## Input Validation

### ✅ Backend Validation

- [ ] All inputs validated on backend (never trust frontend)
- [ ] Validate data types (string, int, float)
- [ ] Validate length constraints
- [ ] Validate format (email, username pattern)
- [ ] Validate business rules (amount > 0, etc.)
- [ ] Sanitize inputs before database/display

**Pattern**: `../../PATTERNS.md` → Input Validation

### ✅ SQL Injection Prevention

- [ ] All queries use parameterized queries (? placeholders)
- [ ] NEVER use f-strings or string concatenation for SQL
- [ ] No dynamic table/column names from user input
- [ ] Use ORM patterns (our dataclass pattern)

**Example**:
```python
# ✅ CORRECT
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))

# ❌ WRONG
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

### ✅ XSS Prevention

- [ ] Jinja2 auto-escapes variables ({{ var }})
- [ ] Use |safe filter only when absolutely necessary
- [ ] Validate and sanitize user content
- [ ] No user input in JavaScript contexts
- [ ] CSP headers configured

**Note**: Jinja2 escapes by default. Trust it unless using `|safe`.

## CSRF Protection

### ✅ Cookie Security

- [ ] samesite=lax on all cookies
- [ ] httponly on session cookies
- [ ] secure flag for HTTPS
- [ ] No sensitive data in cookies

**Implementation**: `src/api.py:277-284`

### ✅ Form Security

- [ ] POST for state-changing operations
- [ ] GET for read-only operations
- [ ] No state changes in GET requests
- [ ] SameSite cookie protection enabled

## Rate Limiting

### ✅ Login Protection

- [ ] Rate limiting on login endpoint (5 attempts per 5 minutes)
- [ ] IP-based rate limiting
- [ ] No user enumeration (consistent error messages)

**Implementation**: `src/api.py:39-74` (RateLimitMiddleware)

## Data Protection

### ✅ Sensitive Data

- [ ] Passwords hashed (PBKDF2)
- [ ] Emails hashed (SHA-256) for privacy
- [ ] No plain text secrets in code
- [ ] Environment variables for secrets (SMTP, GitHub tokens)
- [ ] .env file in .gitignore
- [ ] No secrets in logs

### ✅ User Data Isolation

- [ ] All user queries filter by user_id
- [ ] Foreign key constraints enforced
- [ ] Cascade deletes configured properly
- [ ] No shared data between users

**Critical Rule**: ALWAYS include user_id in WHERE clause.

## Security Headers

### ✅ HTTP Headers

Headers set in `SecurityHeadersMiddleware` (`src/api.py:77-94`):

- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY`
- [ ] `X-XSS-Protection: 1; mode=block`
- [ ] `Strict-Transport-Security: max-age=31536000`
- [ ] `Content-Security-Policy` (blocks inline scripts from untrusted sources)
- [ ] `Referrer-Policy: strict-origin-when-cross-origin`

## Common Vulnerabilities (OWASP Top 10)

### 1. Broken Access Control
- [ ] Check user_id in all data queries
- [ ] Verify ownership before delete/update
- [ ] No direct object references without auth check

### 2. Cryptographic Failures
- [ ] HTTPS enforced (secure flag on cookies)
- [ ] Strong password hashing (PBKDF2 600k)
- [ ] No hardcoded secrets

### 3. Injection
- [ ] Parameterized SQL queries
- [ ] Input validation
- [ ] No eval() or exec()

### 4. Insecure Design
- [ ] Follow security ADRs
- [ ] Use proven patterns
- [ ] Security review before deploy

### 5. Security Misconfiguration
- [ ] Security headers configured
- [ ] Debug mode off in production
- [ ] Default credentials changed
- [ ] Error messages don't leak info

### 6. Vulnerable Components
- [ ] Dependencies up to date
- [ ] No known CVEs in requirements.txt
- [ ] Minimal dependencies

### 7. Authentication Failures
- [ ] Strong password requirements
- [ ] Rate limiting on login
- [ ] Session expiration (30 days)
- [ ] Secure session management

### 8. Software and Data Integrity
- [ ] No unsigned code execution
- [ ] Validate file uploads (if any)
- [ ] CI/CD pipeline secured

### 9. Logging Failures
- [ ] Security events logged
- [ ] No sensitive data in logs
- [ ] Logs protected from tampering

### 10. SSRF
- [ ] Validate external URLs
- [ ] No user-controlled requests
- [ ] GitHub API: only configured repo

## Code Review Questions

Before approving code:

1. **Authentication**: Does this need login? Is it checked?
2. **Authorization**: Can users access other users' data?
3. **Input validation**: Is all input validated?
4. **SQL injection**: Are queries parameterized?
5. **XSS**: Is output escaped?
6. **CSRF**: Is SameSite cookie set?
7. **Secrets**: Any hardcoded passwords/tokens?
8. **Error handling**: Do errors leak information?

## Testing Security

### Unit Tests

```python
def test_user_cannot_access_other_user_data():
    """Test user isolation."""
    user1 = db.create_user("user1", "pass")
    user2 = db.create_user("user2", "pass")

    expense_id = db.add_expense(user1, "Expense", "Andet", 100, "monthly")

    # User 2 can't see user 1's expense
    expenses = db.get_all_expenses(user2)
    assert expense_id not in [e.id for e in expenses]
```

### Manual Testing

1. Try accessing `/budget/expenses` without login → Should redirect
2. Try editing another user's expense → Should fail
3. Try SQL injection in login: `admin'--` → Should fail safely
4. Try XSS in expense name: `<script>alert('xss')</script>` → Should be escaped

## Incident Response

If security issue found:

1. **Assess severity**: Critical/High/Medium/Low
2. **Fix immediately** if critical
3. **Document** in ADR if architectural
4. **Update checklist** with new item
5. **Add test** to prevent regression

## Related Documentation

- **Password Security**: `../adr/001-pbkdf2-password-hashing.md`
- **Session Security**: `../adr/002-session-based-authentication.md`
- **Security Patterns**: `../../PATTERNS.md` → Security Patterns
- **OWASP**: https://owasp.org/www-project-top-ten/
