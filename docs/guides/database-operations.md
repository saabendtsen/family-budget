# Guide: Database Operations

How to add new database functions and modify the schema.

## Prerequisites

- Read `src/CLAUDE.md` → Database Functions Index
- Read `PATTERNS.md` → Database Patterns
- Read `docs/adr/003-sqlite-database-choice.md`

## Adding a New Database Function

### Step 1: Determine Operation Type

| Type | Example | Returns |
|------|---------|---------|
| **Read (SELECT)** | Get user expenses | `list[Expense]` or `Optional[Item]` |
| **Create (INSERT)** | Add expense | `int` (new ID) |
| **Update** | Edit expense | `None` or `int` (rows affected) |
| **Delete** | Remove expense | `None` or `bool` (success) |
| **Aggregate** | Calculate totals | `float` or `dict` |

### Step 2: Write Function

**Location**: `src/database.py` (add in logical section)

**Read Operation**:
```python
def get_items(user_id: int) -> list[Item]:
    """Get all items for user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM items WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return [
            Item(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                amount=row['amount']
            )
            for row in cursor.fetchall()
        ]
```

**Create Operation**:
```python
def add_item(user_id: int, name: str, amount: float) -> int:
    """Add item. Returns new item ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO items (user_id, name, amount) VALUES (?, ?, ?)",
            (user_id, name, amount)
        )
        conn.commit()
        return cursor.lastrowid
```

**Update Operation**:
```python
def update_item(item_id: int, user_id: int, name: str, amount: float):
    """Update item."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE items SET name = ?, amount = ? WHERE id = ? AND user_id = ?",
            (name, amount, item_id, user_id)
        )
        conn.commit()
```

**Delete Operation**:
```python
def delete_item(item_id: int, user_id: int):
    """Delete item."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM items WHERE id = ? AND user_id = ?",
            (item_id, user_id)
        )
        conn.commit()
```

### Step 3: Add to Index

Update `src/CLAUDE.md` → Database Functions Index with new function.

### Step 4: Write Tests

Add tests to `tests/test_database.py`:

```python
def test_add_item():
    """Test adding item."""
    user_id = db.create_user("testuser", "password123")
    item_id = db.add_item(user_id, "Test Item", 100.50)

    assert item_id > 0

    items = db.get_items(user_id)
    assert len(items) == 1
    assert items[0].name == "Test Item"
    assert items[0].amount == 100.50
```

## Critical Rules

### ✅ Always Include user_id in WHERE

```python
# ✅ CORRECT
WHERE id = ? AND user_id = ?

# ❌ WRONG - Security vulnerability!
WHERE id = ?
```

### ✅ Always Use Parameterized Queries

```python
# ✅ CORRECT
cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))

# ❌ WRONG - SQL injection!
cursor.execute(f"SELECT * FROM items WHERE id = {item_id}")
```

### ✅ Always Commit Writes

```python
cursor.execute("INSERT ...")
conn.commit()  # Required!
```

### ✅ Always Use Context Manager

```python
with get_connection() as conn:
    # Operations
    conn.commit()
# Connection auto-closed
```

## Adding a Table

### Step 1: Add to Schema

Edit `src/database.py` → `init_db()` function:

```python
def init_db():
    """Initialize database schema."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # ... existing tables ...

        # Add new table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS new_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
```

### Step 2: Create Dataclass Model

```python
@dataclass
class NewItem:
    id: int
    user_id: int
    name: str
    created_at: str
```

### Step 3: Write Migration (if production data exists)

Create `scripts/migrate_add_new_table.py`:

```python
import sqlite3
from pathlib import Path

DB_PATH = Path("data/budget.db")

def migrate():
    """Add new_table to existing database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS new_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
```

Run: `python scripts/migrate_add_new_table.py`

## Best Practices

### Use Meaningful Function Names

```python
# ✅ Good
get_expenses_by_category(user_id)
get_total_monthly_income(user_id)

# ❌ Bad
get_stuff(user_id)
calc(user_id)
```

### Return Typed Dataclasses

```python
# ✅ Good
def get_expense(expense_id: int) -> Optional[Expense]:
    ...

# ❌ Bad
def get_expense(expense_id: int) -> dict:
    ...
```

### Use Descriptive SQL

```python
# ✅ Good - clear what we're selecting
cursor.execute('''
    SELECT id, name, amount, category
    FROM expenses
    WHERE user_id = ?
    ORDER BY created_at DESC
''', (user_id,))

# ❌ Bad - unclear
cursor.execute("SELECT * FROM expenses WHERE user_id = ?", (user_id,))
```

## Troubleshooting

**Error: "no such table"**
- Run `init_db()` (happens automatically on startup)
- Check table name spelling

**Error: "no such column"**
- Column doesn't exist in table
- Check schema in `init_db()`
- May need migration if production

**Data not appearing**
- Check `user_id` filter
- Verify `conn.commit()` called
- Check `ORDER BY` clause

**Foreign key violation**
- Check that referenced user/category exists
- Ensure foreign keys are enabled (default in SQLite 3.6.19+)

## Related Documentation

- **Pattern Guide**: `../../PATTERNS.md` → Database Patterns
- **Module Guide**: `../../src/CLAUDE.md` → Database Functions Index
- **ADR**: `../adr/003-sqlite-database-choice.md`
