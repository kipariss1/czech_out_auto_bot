# Quickstart: Local Test Runner with Postgres Test Database

This guide validates the feature end-to-end once implemented. It assumes the tasks/implementation
phase has landed the changes described in [plan.md](./plan.md) — the three new `uv run` scripts, the
new `postgres_test_db` Compose service, and the `ENV=test` → Postgres rewiring described in
[data-model.md](./data-model.md).

## Prerequisites

- Docker Desktop or Docker Engine + Compose v2, running.
- `uv` installed.
- A populated `.env` at the repo root with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`,
  `CIPHER_KEY`, and `BOT_TOKEN` (the same file already required for `start-local-db`).
- Node.js 20, for the Playwright smoke suite under `tests/e2e_smoke_tests` (only needed for Scenario 3, the e2e command).
- Run all commands from the repository root (the same convention `start-local-db` and `deploy`
  already enforce by checking for `docker-compose.yml`).

## Scenario 1 — Start just the test database (User Story 3)

```bash
uv run start-test-db
```

**Expected outcome**: a container named `postgres_test_db` becomes healthy, published on
`localhost:5433`, distinct from any `postgres_db` container. Confirm with:

```bash
docker inspect --format='{{json .State.Health.Status}}' postgres_test_db   # "healthy"
docker ps --filter name=postgres_test_db --filter name=postgres_db          # both may be listed together
```

Running the command again while the container is already healthy MUST NOT wipe it (reuse behavior —
this is the "on demand" debugging flow, distinct from either full test-run command).

## Scenario 2 — Run the local component tests (User Story 1)

```bash
uv run run-local-component-tests
```

**Expected outcome**: the command, without any other manual setup —

1. force-recreates `postgres_test_db` (empty, per FR-005),
2. applies Alembic migrations / seeds car data against it,
3. runs `tests/unit_tests` and `tests/integration_tests`,
4. prints a per-stage pass/fail summary and exits `0` only if both suites passed,
5. removes the test database container before returning — **never** starts the web app or touches
   Node/Playwright.

Validate a failure is surfaced correctly by intentionally breaking a unit test and re-running the
command — the summary MUST name the failing suite and the process MUST exit non-zero (Acceptance
Scenario 2).

## Scenario 3 — Run the local e2e tests (User Story 2)

```bash
uv run run-local-e2e-tests
```

**Expected outcome**: the command, without any other manual setup —

1. force-recreates `postgres_test_db` (empty, per FR-005),
2. applies Alembic migrations / seeds car data against it,
3. starts the web app against the test database and waits for it to respond on port 8000,
4. runs the Playwright smoke suite in `tests/e2e_smoke_tests` against that running web app,
5. prints a pass/fail result and exits `0` only if the suite passed,
6. stops the web app process and removes the test database container before returning.

Validate a failure is surfaced correctly by intentionally breaking a Playwright assertion and
re-running the command — it MUST report the failure and exit non-zero.

## Scenario 4 — Concurrent local-dev and test databases (SC-006)

```bash
uv run start-local-db              # existing command, local-dev Postgres on :5432
uv run start-test-db               # new command, test Postgres on :5433
docker ps                          # both postgres_db and postgres_test_db healthy, no port conflicts
```

## Scenario 5 — Every run starts empty (SC-004)

Both `run-local-component-tests` and `run-local-e2e-tests` tear the test container down completely
when they finish (not just its tables), so there is nothing left to inspect immediately afterward.
Instead, verify the container is destroyed and recreated — not reused — across a run, and that the
freshly-recreated container ends up empty:

```bash
uv run start-test-db
docker inspect --format='{{.Id}}' postgres_test_db   # note this container ID
docker exec postgres_test_db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "INSERT INTO \"Users\" (id, telegram_id) VALUES (999, 999);"   # or any table from src/models/models.py

uv run run-local-component-tests   # or run-local-e2e-tests — force-recreates, then tears down at the end

uv run start-test-db               # starts a brand-new container (the previous one no longer exists)
docker inspect --format='{{.Id}}' postgres_test_db   # expect: a different container ID than before
docker exec postgres_test_db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "SELECT * FROM \"Users\" WHERE id = 999;"   # expect: no rows — no volume means nothing survives destroy+recreate
```

## Scenario 6 — No remaining SQLite references (SC-005)

```bash
grep -rn "sqlite" -i src/ alembic/ web_app/ telegram_bot/ queue_svc/ readme.md boring_readme_for_devs.md src/db/readme.md AGENTS.md
grep -rn "sqlite" -i --exclude-dir=node_modules --exclude-dir=dist tests/e2e_smoke_tests/
```

**Expected outcome**: no matches. (`tests/pytest_fixtures/common.py`'s `build_mock_db` fixture is
intentionally excluded from this check — it is out of scope per the spec's Assumptions. The second
command covers the Playwright suite's own former SQLite fixture handler, discovered and migrated to
Postgres during implementation — see tasks.md Notes.)

## Scenario 7 — Interruption cleans up (edge case)

```bash
uv run run-local-e2e-tests
# press Ctrl+C partway through, e.g. during the smoke e2e stage
docker ps --filter name=postgres_test_db   # expect: not running
ps aux | grep uvicorn                       # expect: no leftover web app process
```

Repeat with `uv run run-local-component-tests`, interrupting during the integration-test stage —
`postgres_test_db` must not be left running.
