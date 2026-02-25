# Gemini CLI Project Mandates

This file defines the operational rules for Gemini CLI within the Family Budget project.

## 1. Research & Discovery
- ALWAYS read `docs/AI_CONTEXT.md` first to understand the project's state.
- ALWAYS refer to `PATTERNS.md` for coding standards (modals, forms, DB queries).
- ALWAYS refer to `docs/DESIGN_GUIDE.md` for UI patterns and TailwindCSS colors.

## 2. Technical Standards
- **UI Text:** All UI text must be in Danish.
- **Safety:** Never log or commit secrets. Use environment variables (via `~/.env`) for SMTP.
- **SQLite:** When modifying schema, always check for existing data and migrations.
- **Testing:** 
  - For bug fixes: Create a reproduction test first.
  - For new features: Add unit tests in `tests/` and E2E tests in `e2e/`.
  - Commands: `pytest tests/` (Unit) and `pytest e2e/` (E2E).

## 3. Tool Usage
- Use `grep_search` to find route handlers in `src/api.py`.
- Use `grep_search` to find database functions in `src/database.py`.
- Use `run_shell_command` for:
  - Running tests (`pytest`)
  - Running migrations (`python -m scripts.[migration_script]`)
  - Starting the app (`python -m src.api`)

## 4. Design Philosophy
- Follow the "Simple Web App" design: Mobile-first, card-based, clean UI.
- Use `primary` (#3b82f6), `success` (#10b981), and `danger` (#ef4444) colors strictly.
- Ensure dark mode is supported (`dark:` variants) for every UI change.
