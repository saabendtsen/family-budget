---
type: adr
number: 001
status: accepted
date: 2024-01-10
---

# ADR-001: PBKDF2 Password Hashing

## Status
Accepted

## Context

The Family Budget application requires secure password storage for user authentication. The password hashing algorithm must:

1. Be cryptographically secure against brute-force attacks
2. Require no external dependencies (minimize deployment complexity)
3. Be simple to implement correctly
4. Meet current OWASP security standards
5. Be fast enough for production use (~200ms acceptable)

### Options Considered

**1. PBKDF2-HMAC-SHA256** (Python stdlib)
- **Pros**: Built into Python hashlib, OWASP recommended, zero dependencies
- **Cons**: Slightly slower than bcrypt, less memory-hard than Argon2

**2. bcrypt** (requires `bcrypt` package)
- **Pros**: Industry standard, well-tested, good security properties
- **Cons**: Requires C extensions, more complex deployment, adds dependency

**3. Argon2** (requires `argon2-cffi` package)
- **Pros**: Winner of Password Hashing Competition, memory-hard, best security
- **Cons**: Requires C extensions, less widespread adoption, adds dependency

**4. scrypt** (Python stdlib)
- **Pros**: Built-in, memory-hard
- **Cons**: Less mature OWASP guidance than PBKDF2

## Decision

Use **PBKDF2-HMAC-SHA256** with **600,000 iterations**.

## Rationale

### OWASP Recommendation

The OWASP Password Storage Cheat Sheet (2023) explicitly recommends:
- **PBKDF2-HMAC-SHA256** with minimum 600,000 iterations

Source: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

This is the current industry standard as of 2023-2024.

### Benefits

1. **Zero Dependencies**: Part of Python standard library (`hashlib`)
   - No C compiler needed for deployment
   - No additional packages to manage
   - Reduces attack surface

2. **Simple Deployment**: Works out-of-the-box on any Python 3.x environment
   - Docker containers don't need build tools
   - Development setup is simpler
   - Fewer points of failure

3. **OWASP Compliant**: Meets current security standards
   - 600,000 iterations recommended in 2023
   - Properly salted (32 bytes random)
   - HMAC-SHA256 provides strong security

4. **Performance**: Acceptable for user authentication
   - ~200ms on modern hardware
   - Fast enough that users don't notice
   - Slow enough to resist brute force

5. **Easy to Audit**: Simple implementation
   - Fewer lines of code to review
   - Well-documented Python stdlib
   - Clear security properties

### Trade-offs Accepted

**Performance**: PBKDF2 is slightly slower than bcrypt
- PBKDF2: ~200ms for 600k iterations
- bcrypt: ~150ms
- **Decision**: 50ms difference is acceptable for login operations

**Memory hardness**: PBKDF2 is not memory-hard (unlike Argon2)
- **Decision**: For this application (small user base, not a target for sophisticated attacks), computational hardness is sufficient
- Can migrate to Argon2 in future if needed

## Implementation

### Location

- **Hash function**: `src/database.py:23-28`
- **Verify function**: `src/database.py:31-35`
- **Constant**: `src/database.py:20` (PBKDF2_ITERATIONS = 600_000)

### Code

```python
import hashlib
import secrets

# OWASP recommends 600,000 iterations for PBKDF2-HMAC-SHA256 (2023)
PBKDF2_ITERATIONS = 600_000

def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """Hash password with PBKDF2. Returns (hash, salt) as hex strings."""
    if salt is None:
        salt = secrets.token_bytes(32)  # 32 bytes = 256 bits
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, PBKDF2_ITERATIONS)
    return hashed.hex(), salt.hex()

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password against stored hash."""
    new_hash, _ = hash_password(password, bytes.fromhex(salt))
    return secrets.compare_digest(new_hash, stored_hash)  # Constant-time comparison
```

### Usage Locations

1. **User registration**: `src/database.py:724` (`create_user`)
2. **Password reset**: `src/database.py:839` (`update_user_password`)
3. **Login verification**: `src/database.py:737` (`authenticate_user`)

### Database Schema

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,  -- PBKDF2 hash as hex
    salt TEXT NOT NULL,            -- 32-byte salt as hex
    ...
)
```

## Consequences

### Positive

1. **Simple deployment**: No build dependencies required
2. **OWASP compliant**: Meets current security standards
3. **Easy to maintain**: Stdlib code is stable and well-tested
4. **Auditable**: Clear, simple implementation
5. **Secure enough**: 600k iterations provides strong protection

### Negative

1. **Performance**: Slightly slower than bcrypt (~200ms vs ~150ms)
   - **Mitigation**: Acceptable for login operations (users don't notice)

2. **Not memory-hard**: Vulnerable to GPU/ASIC attacks (theoretical)
   - **Mitigation**: Small user base, not a high-value target
   - **Future**: Can migrate to Argon2 if threat model changes

3. **Future iteration increases**: May need to increase iterations over time
   - **Mitigation**: Documented constant makes this easy to update
   - **Strategy**: Can rehash on login to migrate users gradually

## For AI Agents

When implementing authentication features:

### ✅ DO

- **ALWAYS use `hash_password()`** for new passwords (registration, reset)
- **ALWAYS use `verify_password()`** for login checks
- **NEVER store plain passwords** anywhere (logs, database, memory dumps)
- **Use `secrets` module** for salt generation (not `random`)
- **Use constant-time comparison** (`secrets.compare_digest()`)

### ❌ DON'T

- **Never hash passwords client-side** (defeats purpose of salting)
- **Never implement custom password hashing** (use stdlib)
- **Never reuse salts** (each password gets unique salt)
- **Never log passwords** (even hashed ones shouldn't be logged)
- **Never reduce iteration count** (only increase over time)

### Example: Adding Password Validation

```python
from src.database import hash_password, create_user

# When creating user
password = form_data.get('password')
if len(password) < 8:
    return error("Password must be at least 8 characters")

# Create user with hashed password
user_id = create_user(username, password, email)  # hash_password called internally
```

### Example: Password Reset

```python
from src.database import update_user_password

# When resetting password
new_password = form_data.get('password')
if len(new_password) < 8:
    return error("Password must be at least 8 characters")

update_user_password(user_id, new_password)  # Hashes internally
```

## Migration Strategy (Future)

If we need to migrate to Argon2 in the future:

1. Add `password_version` column to users table
2. Keep PBKDF2 code for backward compatibility
3. On successful login, check version:
   - If PBKDF2: verify, then rehash with Argon2, update version
   - If Argon2: verify normally
4. Gradual migration as users log in
5. After 90% migrated, force remaining users to reset

## References

- **OWASP Password Storage Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- **Python hashlib documentation**: https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac
- **NIST SP 800-132**: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-132.pdf
- **Pattern guide**: `../../PATTERNS.md` → Password Hashing Pattern
- **Implementation**: `../../src/database.py:23-35`
