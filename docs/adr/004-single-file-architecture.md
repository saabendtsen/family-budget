---
type: adr
number: 004
status: accepted
date: 2024-01-10
---

# ADR-004: Single-File Architecture

## Status
Accepted

## Context

FastAPI routes can be organized in multiple ways:
- Single file with all routes
- Split by feature (auth.py, expenses.py, etc.)
- Split by layer (routes/, services/, models/)

With ~30 routes and growing, need to decide on structure.

## Decision

Keep all routes in **single file** (`src/api.py`) until it becomes genuinely problematic.

## Rationale

### Benefits

1. **Easy to navigate**: Ctrl+F finds any route instantly
2. **Understand flow**: See entire request flow in one file
3. **Avoid circular imports**: No dependency management between modules
4. **Related code together**: Auth middleware + routes in same context
5. **Simple mental model**: One file per concern (api.py = routes, database.py = data)

### When Current Approach Works

- <50 routes (currently 30)
- Single-purpose application
- Small team (1-2 developers)
- No distinct feature domains

### When to Split

Consider splitting when:
- Routes exceed 100 (file becomes unwieldy)
- Distinct feature domains emerge (admin panel, API v2)
- Multiple developers work on different features
- Import complexity grows

## Implementation

**Current structure** (`src/api.py`):
```
- Imports and setup (lines 1-100)
- Middleware (lines 101-200)
- Helper functions (lines 201-250)
- Authentication routes (lines 253-530)
- Dashboard routes (lines 533-617)
- Income routes (lines 619-682)
- Expense routes (lines 685-817)
- Category routes (lines 820-930)
- Static pages (lines 933-1104)
- API endpoints (lines 1107-1168)
- Settings routes (lines 1171-1256)
```

**Navigation aids**:
- Section dividers with ASCII art
- Descriptive function names
- `src/API-REFERENCE.md` for quick lookup

## Consequences

### Positive
- Simple to understand
- Easy to search
- No import complexity
- Fast development

### Negative
- Large file (1,256 lines)
- More scrolling

**Mitigation**: Use `src/API-REFERENCE.md` to jump to line numbers.

## For AI Agents

**Finding routes**: Use `src/API-REFERENCE.md` instead of reading full file.

**Adding routes**: Place in logical section (auth with auth, expenses with expenses).

## References
- API Reference: `../../src/API-REFERENCE.md`
- Implementation: `../../src/api.py`
