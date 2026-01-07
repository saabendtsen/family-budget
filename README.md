# Family Budget

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simple, self-hosted family budget webapp built with FastAPI and Jinja2 templates.

## Features

- **Multi-user support** - Each family member has their own account
- **Income tracking** - Track multiple income sources
- **Expense management** - Categorize expenses with custom categories and icons
- **Demo mode** - Try the app without creating an account
- **Responsive design** - Works on desktop and mobile

## Tech Stack

- **Backend:** FastAPI + SQLite
- **Frontend:** Jinja2 templates + TailwindCSS (CDN) + Lucide icons
- **Auth:** Session-based with PBKDF2 password hashing (100,000 iterations)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/saabendtsen/family-budget.git
cd family-budget

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python -m src.api

# Open http://localhost:8086/budget/
```

## Routes

| Route | Description |
|-------|-------------|
| `/budget/` | Dashboard with budget overview |
| `/budget/login` | Login page |
| `/budget/register` | User registration |
| `/budget/demo` | Demo mode (read-only) |
| `/budget/expenses` | Manage expenses |
| `/budget/income` | Manage income sources |
| `/budget/categories` | Manage expense categories |
| `/budget/settings` | Account settings |
| `/budget/help` | User guide |

## Database

SQLite database stored in `data/budget.db` with tables:
- `users` - User accounts with hashed passwords
- `income` - Income per source
- `expenses` - Expenses with category and frequency
- `categories` - Expense categories with icons

## Security

- Passwords hashed with PBKDF2 (100,000 iterations)
- Session tokens hashed with SHA-256
- Cookies: httponly, secure, samesite=lax
- Rate limiting: 5 login attempts per 5 minutes

## Testing

```bash
pytest
```

## Contributing

See [CLAUDE.md](CLAUDE.md) for development guidelines and project context.

## License

MIT License - see [LICENSE](LICENSE) for details.
