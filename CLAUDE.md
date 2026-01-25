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
- Passwords hashes med PBKDF2 (100.000 iterationer)
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

## Næste Steps
- [ ] Merge feature branches når brugere er færdige med at teste
- [ ] Opsæt SMTP credentials for password reset
- [ ] Overvej: eksport af budget data (CSV/PDF)
- [ ] Overvej: budget mål/targets
- [ ] Overvej: historik/grafer over tid
