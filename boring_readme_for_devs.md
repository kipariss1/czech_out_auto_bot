# Czech Out Auto Bot

`czech_out_auto_bot` is a car-search assistant for the Czech market.

It combines:
- a FastAPI web app for creating searches
- a Telegram bot for notifications
- a PostgreSQL database for persistent search data
- a parser/worker pipeline for scraping Bazos and filtering ads with an LLM
- automated test coverage for unit, integration, and smoke e2e flows

## What It Does

The app lets a user define a car search with filters such as:
- manufacturer and model
- production year range
- mileage range
- price range
- PSC / search radius

The backend then:
1. collects matching ads from Bazos
2. pushes new ads into a processing queue
3. sends each ad to the configured LangChain LLM for structured extraction and validation
4. checks whether the ad fits an existing user search
5. sends a Telegram notification when a match is found

## Architecture

Relevant code areas:
- [web_app](./web_app) - FastAPI web UI for creating and viewing car searches.
- [telegram_bot](./telegram_bot) - Telegram bot integration used for sending matched-ad notifications. Its Docker service also initializes the database on startup via [src/database_utils/init_db.py](./src/database_utils/init_db.py), applying Alembic migrations when migration files are present or creating initial tables and loading seed car model data otherwise.
- [queue_svc/parser](./queue_svc/parser) - parser logic that scans Bazos and pushes new ads into the processing queue.
- [queue_svc/worker](./queue_svc/worker) - worker pipeline that validates queued ads and matches them against user searches.
- [src/models](./src/models) - shared database and domain models used across services.
- [src/database_utils](./src/database_utils) - database access and helper utilities for persistence-related operations.

The Docker `queue` service runs one parser/worker/cache-cleanup cycle every 2 hours after `docker compose up`: first parser, then worker, then cache cleanup. The next cycle is scheduled from the cycle start timestamp. If the cycle finishes in less than 2 hours, `queue` waits the remaining time; if it takes 2 hours or more, the next cycle starts immediately.

## Parsed Advertisement Cache

Before asking the LLM to parse an advertisement, `BazosWorker` checks
`Parsed_Advertisements_Cache` for a non-expired result keyed by the advertisement's Bazos id and
the car model (`CarModel.id`) it's being evaluated against. On a hit, the stored result is reused
and the LLM is not called; on a miss, the LLM result is written back to the cache (updating the
existing row if one already expired and got reprocessed, never duplicating it).

Cache rows older than `PARSED_AD_CACHE_RETENTION_DAYS` (default `30`) are deleted automatically as
the third step of each `queue` cycle, after the parser and worker steps. A cache read/write failure
is logged and falls back to a direct LLM call — it never blocks advertisement processing.

## Worker LLM Configuration

The worker selects its LLM provider from `LLM`:

- `LLM=local` uses the Ollama service. This is the default.
- `LLM=api-key` uses Gemini through `GEMINI_API_KEY`.

Optional model overrides:

- `OLLAMA_MODEL`, default `gemma4:12b`
- `OLLAMA_BASE_URL`, default `http://ollama:11434` in `production` and `http://localhost:11434` in `local`/`test`
- `GEMINI_MODEL`, default `gemini-3-flash`

## Local Run

### Requirements

- Docker and Docker Compose
- Python 3.11 if you want to run tests locally outside containers
- Node.js 20 if you want to run Playwright smoke tests locally

### Local Development Startup With The Postgres Test Container

`ENV=test` targets a dedicated, disposable PostgreSQL container (`postgres_test_db`, published on
`localhost:5433`) instead of a local file — it's the same database engine as `local`/`production`,
just empty and separate. Three `uv run` commands cover the local test workflow:

- **Start just the empty test database** (for manual debugging, without running either test suite):
  ```bash
  uv run start-test-db
  ```
  Reuses an already-healthy `postgres_test_db` container if one exists, or starts and initializes a
  fresh one otherwise.

- **Run the component tests** (unit + integration; starts/recreates the test database, never touches
  the web app):
  ```bash
  uv run run-local-component-tests
  ```

- **Run the e2e tests** (starts/recreates the test database, starts the web app against it, runs the
  Playwright smoke suite):
  ```bash
  uv run run-local-e2e-tests
  ```

Both `run-local-component-tests` and `run-local-e2e-tests` always start from an empty database and
tear down the test container when they finish (including on Ctrl+C).

Once a test database is up (e.g. via `uv run start-test-db`), you can also start the individual
services for local development against it:

- **Web App**:
  ```bash
  export ENV=test && uv run python -m web_app.main
  ```

- **Telegram Bot**:
  ```bash
  export ENV=test && uv run python -m telegram_bot.run_bot
  ```

### Local PostgreSQL Container

`ENV=local` is for commands run from the host machine against the Docker PostgreSQL container. It connects to PostgreSQL through `localhost:5432`, so the `postgres_db` service publishes port `5432`.

To start only the local PostgreSQL container:

```bash
docker compose up -d postgres_db
```

Initialize it from the host:

```bash
ENV=local uv run python -m src.database_utils.init_db
```

Create or apply Alembic migrations from the host with the same environment:

```bash
ENV=local uv run alembic revision --autogenerate -m "describe schema change"
ENV=local uv run alembic upgrade head
```

Docker Compose services run with `ENV=production` and connect to PostgreSQL through the Compose DNS name `postgres_db`.

To update the server after merging an MR, run `uv run deploy` (`git pull` + `docker compose build --no-cache` + `docker compose up -d`).

## Database Migrations

Alembic is configured in [alembic.ini](./alembic.ini), with migration scripts in [alembic/versions](./alembic/versions). The runtime database URL is resolved through [src/database_utils/migrations.py](./src/database_utils/migrations.py): `ENV=production`, `ENV=local`, and `ENV=test` all resolve to PostgreSQL — `ENV=test` targets the dedicated `postgres_test_db` container on `localhost:5433`.

Apply migrations in the configured production environment:

```bash
uv run alembic upgrade head
```

Apply migrations against the Postgres test container (start it first with `uv run start-test-db`):

```bash
ENV=test uv run alembic upgrade head
```

To test migrations against a throwaway database, pass an Alembic override with any reachable
Postgres URL:

```bash
ENV=test uv run alembic -x database_url=postgresql://app_user:secret@localhost:5433/czech_out_db_migration_test upgrade head
```

Create a new autogenerated revision after changing SQLAlchemy models:

```bash
uv run alembic revision --autogenerate -m "describe schema change"
```

The Telegram bot container also runs [src/database_utils/init_db.py](./src/database_utils/init_db.py) on startup, so migrations are applied before seed car model data is loaded.

For local PostgreSQL without starting the Telegram bot, start `postgres_db` and run `ENV=local uv run python -m src.database_utils.init_db` from the host.

## CI

The GitHub Actions workflow in [tests.yml](./.github/workflows/tests.yml) currently runs:
- unit tests
- integration tests
- smoke e2e tests

## Progress Tracker

TODO:
 - separate containers for web_app, telegram bot and db ✅
 - grown up db ✅
 - implement smoke tests for web app ✅
 - implement jobs for scrapping bazos.cz and processing it with LLM & sending to user (parser & worker) ✅
