# AGENTS.md

## Project Summary
`czech_out_auto_bot` is a Telegram-integrated car-search assistant for the Czech market that scrapes Bazos.cz, processes ads using an LLM (LangChain with local Ollama or remote Gemini), and notifies users of relevant matches.

## Tech Stack
- **Language**: Python >= 3.11, Node.js 20 (for E2E tests)
- **Web Framework**: FastAPI (with Uvicorn and Starlette)
- **Database**: PostgreSQL (Production), SQLite (Local/Test)
- **ORM & Migrations**: SQLAlchemy 2.0, Alembic
- **Scraping & Parsing**: BeautifulSoup4, undetected-chromedriver
- **LLM Integration**: LangChain (Google GenAI, Ollama)
- **Bot Integration**: pytelegrambotapi (Telebot)
- **Dependency Management**: `uv` for Python (`pyproject.toml` / `uv.lock`), `npm` for Playwright tests
- **Testing**: `pytest` (Unit/Integration), `Playwright` (E2E Smoke Tests)
- **Infrastructure**: Docker & Docker Compose

## Context & Architecture
The project is a multi-service application orchestrated via Docker Compose:
- **web_app**: A FastAPI application rendering a Jinja2/Bootstrap web UI for users to create and manage car searches.
- **telegram_bot**: The Telegram bot service that interacts with users and sends notifications. **Note:** This container is also responsible for running database migrations and seed data scripts (`init_db.py`) on startup.
- **postgres_db**: The PostgreSQL database storing user info, search configurations, and parsed ads.
- **ollama**: A local LLM container (running `gemma4:12b` by default) used for extracting structured car data from ads.
- **queue**: A background worker that runs periodically (every 2 hours). It executes a `parser` (scrapes bazos.cz) followed by a `worker` (processes scraped ads through the LLM, matches them against DB user searches, and queues Telegram notifications).

### Key Directory Structure
- `alembic/` - Database migration scripts.
- `queue_svc/` - Contains the `parser` and `worker` modules for background tasks.
- `src/` - Shared business logic.
  - `src/database_utils/` - Database connection handlers and migration utilities.
  - `src/models/` - SQLAlchemy DB models and Pydantic schemas.
- `telegram_bot/` - Telegram bot integration code.
- `tests/` - Contains `unit_tests`, `integration_tests`, and Node.js `e2e_smoke_tests`.
- `web_app/` - FastAPI endpoints, static assets, and HTML templates.

## Operational Commands
*Run these commands from the project root.*

- **Install Dependencies:**
  - Python: `uv pip install -e .`
  - Node.js (E2E): `cd tests/e2e_smoke_tests && npm ci && npx playwright install --with-deps`
- **Dev (Docker):** 
  `docker compose up --build`
- **Dev (Local Python):**
  1. Initialize Test DB: `export ENV=test && uv run python -m src.database_utils.init_test_db`
  2. Start Web App: `export ENV=test && uv run python -m web_app.main`
  3. Start Bot: `export ENV=test && uv run python -m telegram_bot.run_bot`
- **Test:**
  - Unit Tests: `export ENV=test && uv run pytest tests/unit_tests -v`
  - Integration Tests: `export ENV=test && uv run pytest tests/integration_tests -v`
  - E2E Tests: `cd tests/e2e_smoke_tests && npm run test:playwright` (Requires the web app to be running on port 8000).
- **Lint/Format:** 
  The project does not have a strict CI linting gate, but standard PEP8 should be followed. *[INFERRED]* You may use `ruff check .` or `black .` if available in your global environment.
- **Build:** 
  `docker compose build`

## Coding Standards
- **Formatting**: Use 4 spaces for indentation.
- **Naming Conventions**: 
  - `snake_case` for variables, functions, and module names.
  - `PascalCase` for classes and SQLAlchemy models.
  - `UPPER_CASE` for global constants.
- **Preferred Patterns**:
  - Use FastAPI's Dependency Injection (e.g., `Depends(get_db_session)`) for passing database sessions to endpoints.
  - Centralize database models in `src/models/models.py`.
- **Forbidden Patterns**:
  - Do NOT hardcode database connection strings; always use `src.database_utils.db_handler`.
  - Avoid executing heavy database queries directly inside Jinja templates.
  - Do NOT commit `.env` files or sensitive API keys.

## Workflow Rules
- **Jira Management [INFERRED]**: 
  - Default project: **TCP**
  - Assign tickets before beginning work.
  - Transition tickets to "In Progress" and "In Review" as appropriate.
- **Version Control & CI/CD**:
  - Branch naming convention: `<ProjectKey>-<TicketNumber>-<short-description>` (e.g., `TCP-1234-fix-parser`).
  - Commit message format: `[TCP-1234] Description of changes`.
  - The CI/CD pipeline (GitHub Actions) runs Unit, Integration, and E2E tests automatically on PRs to `main`.
- **Database Changes**:
  - NEVER manually edit existing migration files in `alembic/versions/`.
  - Always generate a new migration after modifying SQLAlchemy models: `uv run alembic revision --autogenerate -m "description of change"`.
- **Development Process**:
  - Test locally against the SQLite test DB (`ENV=test`) before opening a PR.
  - Include unit tests for new parser or worker logic.

## Environment Setup
The project requires a `.env` file in the root directory. Missing values will cause container failures.
```env
POSTGRES_USER=app_user
POSTGRES_PASSWORD=secret
POSTGRES_DB=czech_out_db
CIPHER_KEY=your_fernet_key_here
RENDER_EXTERNAL_URL=http://localhost:8000
BOT_TOKEN=your_telegram_bot_token
# Optional overrides:
LLM=local # or 'api-key' for Gemini
OLLAMA_MODEL=gemma4:12b
OLLAMA_BASE_URL=http://ollama:11434
# GEMINI_API_KEY=...
# GEMINI_MODEL=gemini-2.5-flash
```

## Dependency Management
- **Python**: Dependencies are locked and managed using `uv`. Use `uv add <package>` to add new dependencies and update `pyproject.toml`.
- **Node.js**: E2E test dependencies are managed via `npm` inside `tests/e2e_smoke_tests/`. Use standard `npm install <package>` there.

## External Integrations
- **Bazos.cz**: The scraping target. Aggressive concurrent scraping must be avoided to prevent rate-limiting or IP bans.
- **Telegram API**: Used for dispatching user notifications.
- **LangChain / LLMs**: The system dynamically relies on a local Ollama container or Google's Gemini API depending on the `LLM` environment variable.

## Documentation Standards
- Update `readme.md` for any user-facing changes (setup, environment, UI).
- Update `boring_readme_for_devs.md` for architecture, testing, or Docker-related adjustments.
- Include Python docstrings for complex logic, especially within the `queue_svc` parsing algorithms.

## Known Gotchas
- **Database Initialization**: The Telegram bot container is unusually tasked with running DB migrations on startup. If the bot container crashes, the DB schema might not be updated.
- **Test Database Targeting**: The system switches between PostgreSQL and SQLite based on the `ENV` variable. Ensure `export ENV=test` is present when testing or developing locally outside of Docker to target the SQLite DB instead of crashing while looking for PostgreSQL.
- **Queue Cycle Timer**: The `queue` service's parser/worker cycle runs every 2 hours. If a cycle takes less than 2 hours, the container naturally sleeps for the remainder of the time.
