---
type: adr
number: 003
status: accepted
date: 2024-01-10
---

# ADR-003: SQLite Database Choice

## Status
Accepted

## Context

Family Budget needs a database for storing users, income, expenses, and categories. Requirements:
- Support for relational data with foreign keys
- Simple deployment (no separate database server)
- Sufficient performance for <100 concurrent users
- ACID transactions for data integrity
- Easy backup and migration

### Options Considered

1. **SQLite** (embedded)
2. **PostgreSQL** (server)
3. **MySQL/MariaDB** (server)
4. **MongoDB** (NoSQL)

## Decision

Use **SQLite** with database file at `data/budget.db`.

## Rationale

### Why SQLite

1. **Zero configuration**: No database server to install/manage
2. **Simple deployment**: Single file database
3. **Sufficient for use case**: <100 users, low write concurrency
4. **Built into Python**: No additional dependencies
5. **Easy backup**: Copy single .db file
6. **ACID compliant**: Full transaction support
7. **Good enough performance**: Handles thousands of reads/sec

### Trade-offs Accepted

**Concurrency**: Limited write concurrency
- **Impact**: Only matters with >100 concurrent writes
- **Our use case**: <10 concurrent users expected

**Features**: Missing advanced PostgreSQL features
- **Impact**: No JSON operators, full-text search, etc.
- **Our use case**: Don't need these features

## Implementation

**Location**: `src/database.py`

**Connection pattern**:
```python
DB_PATH = Path("data/budget.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
```

**Schema initialization**: `src/database.py:180-221`

## Consequences

### Positive
- Simple deployment (no DB server)
- Easy backup (single file)
- Fast for read-heavy workload
- No dependencies

### Negative
- Limited horizontal scaling
- No built-in replication

## For AI Agents

Always use `get_connection()` with context manager:

```python
with get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    conn.commit()  # For writes
```

## References
- SQLite docs: https://www.sqlite.org/
- Implementation: `../../src/database.py`
