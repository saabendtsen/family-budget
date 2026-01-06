# Family Budget 💰

En moderne, brugervenlig webapplikation til styring af familiens budget, bygget med FastAPI og SQLite. Applikationen giver et klart overblik over indtægter og udgifter, og hjælper med at planlægge økonomien på månedsbasis.

## ✨ Funktioner

*   **📊 Dashboard**: Centralt overblik over samlet indkomst, faste udgifter og rådighedsbeløb.
*   **💸 Udgiftshåndtering**: Nem registrering af både månedlige og årlige udgifter. Årlige udgifter omregnes automatisk til månedsbeløb.
*   **🏢 Kategorisering**: Organiser udgifter i tilpassede kategorier med ikoner (f.eks. Bolig, Mad, Transport, Opsparing).
*   **👤 Brugerstyring**: Sikker login og registrering med hashing af adgangskoder (PBKDF2).
*   **🛡️ Sikkerhed**: Rate limiting på login-forsøg og sessionsstyring via cookies.
*   **🎮 Demo-tilstand**: Mulighed for at afprøve applikationen med testdata uden at oprette en konto.
*   **📱 Responsivt Design**: Udviklet med Tailwind CSS for en optimal oplevelse på både mobil og desktop.
*   **🌙 Dark Mode**: Indbygget understøttelse af mørkt tema.

## 🛠️ Teknisk Stack

*   **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
*   **Frontend**: [Jinja2 Templates](https://jinja.palletsprojects.com/), [Tailwind CSS](https://tailwindcss.com/), [Lucide Icons](https://lucide.dev/)
*   **Database**: [SQLite](https://sqlite.org/) (Fil-baseret for nem portabilitet)
*   **Test**: [Pytest](https://docs.pytest.org/), [Playwright](https://playwright.dev/) (E2E testing)

## 🚀 Kom i gang

### Forudsætninger
*   Python 3.10+
*   pip

### Installation

1.  **Klon repoet**:
    ```bash
    git clone https://github.com/saabendtsen/family-budget.git
    cd family-budget
    ```

2.  **Installer afhængigheder**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Kør applikationen**:
    ```bash
    python -m src.api
    ```
    Applikationen vil være tilgængelig på `http://localhost:8086/budget/`

## �️ Deployment

### Docker (Anbefalet)
Den nemmeste måde at deploye applikationen på er via Docker:

1.  **Byg og start med Docker Compose**:
    ```bash
    docker-compose up -d --build
    ```
    Applikationen vil nu køre i baggrunden, og databasen gemmes i `./data` mappen for at sikre persistens.

### Manuel VPS Setup
Hvis du foretrækker en manuel installation på en Linux server (f.eks. Ubuntu):

1.  **Installer system-afhængigheder**:
    ```bash
    sudo apt update
    sudo apt install python3-pip python3-venv nginx
    ```

2.  **Opsæt virtuelt miljø og installer pakker**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Brug Gunicorn/Uvicorn**:
    Det anbefales at bruge en proces-manager som `systemd` til at køre applikationen.

## �📂 Projektstruktur

*   `src/`: Backend logik og database-operationer.
    *   `api.py`: FastAPI routes og middleware.
    *   `database.py`: Database-skema og SQL operationer.
*   `templates/`: Jinja2 HTML skabeloner.
*   `tests/`: Unit og integration tests.
*   `e2e/`: End-to-end tests med Playwright.
*   `data/`: (Oprettes automatisk) Indeholder SQLite databasen og session-filer.

## 🧪 Test

For at køre test-suiten:

```bash
# Kør alle tests
pytest

# Kør E2E tests (kræver Playwright installation)
playwright install
pytest e2e/
```

## 📝 Licens

Dette projekt er udviklet til privat brug, men koden er frit tilgængelig til inspiration.
