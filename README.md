# Family Budget

A web application for household budget management, built with FastAPI and SQLite. The application provides a clear overview of income and expenses, facilitating monthly financial planning.

## Features

- **Dashboard**: Central overview of total income, fixed expenses, and disposable income.
- **Expense Management**: Register both monthly and annual expenses. Annual expenses are automatically converted to monthly amounts.
- **Categorization**: Organize expenses into customizable categories with icons (e.g., Housing, Food, Transport, Savings).
- **User Management**: Secure login and registration with password hashing (PBKDF2).
- **Security**: Rate limiting on login attempts and session management via cookies.
- **Demo Mode**: Try the application with sample data without creating an account.

## Technical Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Frontend**: [Jinja2 Templates](https://jinja.palletsprojects.com/), [Tailwind CSS](https://tailwindcss.com/), [Lucide Icons](https://lucide.dev/)
- **Database**: [SQLite](https://sqlite.org/) (file-based for portability)
- **Testing**: [Pytest](https://docs.pytest.org/), [Playwright](https://playwright.dev/) (E2E)

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/saabendtsen/family-budget.git
    cd family-budget
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the application**:
    ```bash
    python -m src.api
    ```
    The application will be available at `http://localhost:8086/budget/`

## Deployment

### Docker (Recommended)

1. **Build and start with Docker Compose**:
    ```bash
    docker-compose up -d --build
    ```
    The application will run in the background, with the database stored in `./data` for persistence.

### Manual VPS Setup

For manual installation on a Linux server (e.g., Ubuntu):

1. **Install system dependencies**:
    ```bash
    sudo apt update
    sudo apt install python3-pip python3-venv nginx
    ```

2. **Set up virtual environment and install packages**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. **Run with Gunicorn/Uvicorn**:
    It is recommended to use a process manager such as `systemd` for production deployments.

## Project Structure

- `src/`: Backend logic and database operations.
    - `api.py`: FastAPI routes and middleware.
    - `database.py`: Database schema and SQL operations.
- `templates/`: Jinja2 HTML templates.
- `tests/`: Unit and integration tests.
- `e2e/`: End-to-end tests with Playwright.
- `data/`: (Auto-generated) Contains the SQLite database and session files.

## Testing

To run the test suite:

```bash
# Run all tests
pytest

# Run E2E tests (requires Playwright installation)
playwright install
pytest e2e/
```

## License

This project is developed for private use, but the code is freely available for reference.
