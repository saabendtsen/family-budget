# Family Budget

Simpelt budget-overblik webapp bygget med FastAPI og Jinja2 templates.

## Stack
- **Backend:** FastAPI + SQLite
- **Frontend:** Jinja2 templates + TailwindCSS (CDN) + Lucide icons
- **Auth:** Session-baseret med PBKDF2 password hashing

## Endpoints

| Route | Beskrivelse |
|-------|-------------|
| `/budget/` | Dashboard med budget overblik |
| `/budget/login` | Login side |
| `/budget/register` | Brugeroprettelse |
| `/budget/demo` | Demo mode (read-only) |
| `/budget/expenses` | Administrer udgifter |
| `/budget/income` | Administrer indkomst |
| `/budget/categories` | Administrer kategorier |
| `/budget/help` | Brugervejledning |
| `/budget/logout` | Log ud |

## Kør lokalt
```bash
cd ~/projects/family-budget
source venv/bin/activate
python -m src.api
# Åbn http://localhost:8086/budget/
```

## Database
SQLite database i `data/budget.db` med tabeller:
- `users` - Brugere (username, password_hash, salt)
- `income` - Indkomst per person
- `expenses` - Udgifter med kategori og frekvens
- `categories` - Udgiftskategorier med ikoner

## Sikkerhed
- Passwords hashes med PBKDF2 (100.000 iterationer)
- Session tokens hashes med SHA-256
- Cookies: httponly, secure, samesite=lax
- Rate limiting: 5 login forsøg per 5 minutter

## Demo mode
Demo mode viser eksempeldata uden login. Tilgås via `/budget/demo`.
Data er hardcoded i `database.py` og er read-only.
