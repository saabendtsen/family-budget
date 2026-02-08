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
| `/budget/register` | Brugeroprettelse (med valgfrit email) |
| `/budget/demo` | Demo mode (read-only) |
| `/budget/expenses` | Administrer udgifter |
| `/budget/income` | Administrer indkomst (dynamiske kilder) |
| `/budget/categories` | Administrer kategorier |
| `/budget/settings` | Kontoindstillinger |
| `/budget/help` | Brugervejledning |
| `/budget/forgot-password` | Glemt password |
| `/budget/reset-password/<token>` | Nulstil password |
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
- `users` - Brugere (username, password_hash, salt, email, last_login)
- `income` - Indkomst per kilde (dynamisk antal)
- `expenses` - Udgifter med kategori og frekvens
- `categories` - Udgiftskategorier med ikoner
- `password_reset_tokens` - Tokens til password reset

## Sikkerhed
- Passwords hashes med PBKDF2 (600.000 iterationer - OWASP 2023 standard)
- Session tokens hashes med SHA-256
- Cookies: httponly, secure, samesite=lax
- Rate limiting: 5 login forsøg per 5 minutter
- Password reset tokens: SHA-256 hashed, 1 times udløb, single-use

## Demo mode
Demo mode viser eksempeldata uden login. Tilgås via `/budget/demo`.
Data er hardcoded i `database.py` og er read-only.

## CI/CD Pipeline

### Automatisk Release (GitHub Actions)
- **CI:** Tests kører på alle PRs og pushes til master
- **Release-please:** Opretter automatisk release PRs baseret på conventional commits
- **Auto-merge:** Release PRs merges automatisk når CI er grøn

### Auto-Deploy (MIDLERTIDIGT DEAKTIVERET)

⚠️ **Auto-deploy er deaktiveret** fordi der ofte arbejdes på feature branches direkte på serveren.
Timeren overskrev lokale ændringer ved at pulle fra master.

**Manuel deploy fra serveren:**
```bash
# Rebuild og genstart
cd ~/projects/family-budget
docker compose up -d --build

# Eller brug deploy scriptet (puller IKKE fra git)
# ~/projects/family-budget/scripts/deploy.sh
```

**Genaktiver auto-deploy når feature branches er merget:**
```bash
systemctl --user enable --now family-budget-deploy.timer
```

### Filer
- `.github/workflows/ci.yml` - Test workflow
- `.github/workflows/release-please.yml` - Automatic releases
- `.github/workflows/automerge-release.yml` - Auto-merge release PRs
- `scripts/deploy.sh` - Deploy script
- `VERSION` - Versions-fil (opdateres af release-please)

## Feature Branches (ikke merget endnu)

### `feature/last-login`
Tracker hvornår brugere sidst loggede ind.
- Tilføjer `last_login` kolonne til users
- Opdaterer timestamp ved login

### `feature/email-password-reset`
Email-baseret password reset.
- Email felt ved registrering (valgfrit)
- Konto-side til email administration
- Glemt password flow med email link
- Kræver SMTP konfiguration (se nedenfor)

**Merge begge:**
```bash
git checkout master
git merge feature/last-login
git merge feature/email-password-reset
systemctl --user restart family-budget
```

## SMTP Konfiguration (til password reset)
Tilføj til `~/.env`:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=din@email.dk
SMTP_PASS=app-password
SMTP_FROM=Budget <din@email.dk>
```

## Architecture Decisions

Key technical decisions and their rationale. Update the relevant entry here when changing a fundamental decision.

**Password Hashing**: PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP 2023). Chose over bcrypt/Argon2 to avoid C extension dependencies — stdlib `hashlib` works everywhere. ~200ms per hash is acceptable for login. See `def hash_password` in `src/database.py`.

**Authentication**: Server-side sessions (file-based `data/sessions.json`), not JWT. SSR app doesn't need stateless tokens. Sessions allow instant revocation on logout. SHA-256 hashed tokens, httponly/secure/samesite cookies. See `def hash_token`, `def load_sessions` in `src/api.py`.

**Database**: SQLite embedded database (`data/budget.db`). No separate server needed. Sufficient for <100 concurrent users. Easy backup (copy single file). Consider PostgreSQL migration only if horizontal scaling needed. See `def get_connection` in `src/database.py`.

**Architecture**: Single-file routes (`src/api.py`, ~1,250 lines) + single-file database (`src/database.py`, ~1,000 lines). Avoids circular imports and keeps related code together. Consider splitting when routes exceed ~100 or distinct feature domains emerge.

**Frontend**: Jinja2 SSR templates + TailwindCSS CDN. No JS build step needed. Template inheritance via `base.html`. Minimal JavaScript for modals and form interactions. CDN adds ~100KB but eliminates Node.js dependency entirely.

**Tailwind CDN**: Uses CDN instead of build process. Trades ~90KB extra CSS for zero build configuration. Custom primary color (`#10b981` green) configured inline in `base.html`. Always include `dark:` variants.

**Demo Mode**: Hardcoded data constants in `src/database.py` (search for `DEMO_INCOME` and `DEMO_EXPENSES`). No database writes. Special cookie value `"demo_mode_session"`. Consistent experience for all visitors. See `def get_demo_income`, `def get_demo_expenses` in `src/database.py`.

## Agent Navigation Hints

Use these search patterns instead of reading entire files:

```bash
# Find all routes
grep -n "@app\." src/api.py

# Find all database functions
grep -n "def " src/database.py

# Find all templates
ls templates/

# Find all test classes
grep -n "class Test" tests/*.py e2e/*.py

# Find a specific route handler
grep -n "async def expenses" src/api.py
```

**Key conventions**:
- All UI text is in Danish
- Amounts use Danish formatting: `25.000,50 kr.` — see `def parse_danish_amount` and `def format_currency` in `src/api.py`
- All user data queries include `user_id` in WHERE clause
- POST handlers redirect with 303 (POST-redirect-GET pattern)
- Frequency system: `monthly`, `quarterly`, `semi-annual`, `yearly` — all converted to monthly via `monthly_amount` property

**Documentation**:
- `PATTERNS.md` — coding patterns and conventions (frontend, backend, security, database, testing)
- `docs/guides/adding-new-route.md` — step-by-step guide for new routes

## Deployment Gotchas
- **Deploy script:** `scripts/deploy.sh` kører `git reset --hard origin/master` — commit ALDRIG direkte til master. Brug altid branch → PR → merge workflow.
- **Migrationer:** Kør altid migrations efter merge af PRs med database-ændringer. Migrationer kører IKKE automatisk.
- **Dockerfile-referencer:** Før rebuild, verificér at alle filer refereret i Dockerfile (fx `VERSION`) stadig eksisterer i current branch.
- **Volume mounts:** Verificér at data directory mount points matcher produktions-konfiguration før genstart af containers.

## Næste Steps
- [ ] Merge feature branches når brugere er færdige med at teste
- [ ] Opsæt SMTP credentials for password reset
- [ ] Overvej: eksport af budget data (CSV/PDF)
- [ ] Overvej: budget mål/targets
- [ ] Overvej: historik/grafer over tid
