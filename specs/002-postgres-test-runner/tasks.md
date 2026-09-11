---

description: "Task list template for feature implementation"
---

# Tasks: Local Test Runner with Postgres Test Database

**Input**: Design documents from `/specs/002-postgres-test-runner/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification — no separate test-writing tasks are
included. `run_local_component_tests.py` and `run_local_e2e_tests.py` (built in User Stories 1 and 2)
*run* the existing `tests/unit_tests`, `tests/integration_tests`, and `tests/e2e_smoke_tests` suites;
they do not add new ones.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of
each story. This revision reflects the split of the local test runner into a component-tests command
(User Story 1) and an e2e-tests command (User Story 2), superseding the earlier single-command design.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single project (per plan.md) — `src/`, `tests/`, `alembic/`, `docker-compose.yml`, `pyproject.toml`
at the repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Declare the new test-database container as a project resource, before any code routes
`ENV=test` to it.

- [ ] T001 Add a `postgres_test_db` service to `docker-compose.yml`: image `postgres:15`, `container_name: postgres_test_db`, reuse the existing `<<: *common-env` anchor for `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`, publish port `"5433:5432"` (distinct from `postgres_db`'s `5432`), **no** `volumes:` entry (must stay disposable/empty), a healthcheck of `["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]`, `profiles: ["test"]` so plain `docker compose up` never starts it, and reuse the `logging: *stdout-file-logging` anchor

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Route `ENV=test` to PostgreSQL and retire the SQLite-backed handler. User Stories 1, 2,
and 3 all depend on this being in place.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] In `src/database_utils/postgres_database.py`, add `TEST_POSTGRES_HOST = "localhost"` and `TEST_POSTGRES_PORT = 5433` constants, extend `_db_url_for_host` to accept a `port: int = POSTGRES_PORT` parameter, and add an `env == "test"` branch to `PostgresDBHandler.db_url()` that returns `_db_url_for_host(TEST_POSTGRES_HOST, TEST_POSTGRES_PORT)`
- [ ] T003 [P] In `src/settings/settings.py`, update `Settings.is_postgres_env` to return `True` for `self.env in ("production", "local", "test")` (currently only `"production"`/`"local"`)
- [ ] T004 In `src/database_utils/database_factory.py`, remove the `from src.database_utils.sqlite_database import SqliteDBHandler` import and the `if settings.env == 'test': return SqliteDBHandler(Base)` branch from `DBFactory.create_db_handler`, leaving only the `settings.is_postgres_env` branch and the `ValueError` fallback (depends on T002, T003)
- [ ] T005 [P] In `src/database_utils/migrations.py`, remove the `from src.database_utils.sqlite_database import SqliteDBHandler` import and the `if settings.env == "test": return SqliteDBHandler.db_url()` branch from `get_database_url`, leaving only the `settings.is_postgres_env` branch and the `ValueError` fallback (depends on T002, T003)
- [ ] T006 [P] In `alembic/env.py`, replace `render_as_batch=url.startswith("sqlite")` in `run_migrations_offline` and `render_as_batch=connection.dialect.name == "sqlite"` in `run_migrations_online` with `render_as_batch=False` in both functions, since every environment now runs against PostgreSQL
- [ ] T007 Delete `src/database_utils/sqlite_database.py` — no remaining code path references `SqliteDBHandler` after T004 and T005 (depends on T004, T005)

**Checkpoint**: `ENV=test` now resolves exclusively to PostgreSQL through `src.database_utils.db_handler`. User story implementation can begin.

---

## Phase 3: User Story 1 - Run local component tests with one command (Priority: P1) 🎯 MVP

**Goal**: A single local command starts the test database, prepares its schema, runs the unit and
integration suites, and reports a pass/fail result — without starting the web app.

**Independent Test**: Run `uv run run-local-component-tests` against a clean checkout with nothing
else running; confirm it starts a database, runs both suites, reports an overall pass/fail result,
never touches the web app or Node/Playwright, and leaves no test-only container running afterward.

### Implementation for User Story 1

- [ ] T008 [US1] Create `src/scripts/run_local_component_tests.py` with a `main()` entry point that checks for `docker-compose.yml` in the current directory (mirroring the existing check in `src/scripts/start_local_db.py` and `src/scripts/deploy.py`) and exits with a clear error if not run from the repo root
- [ ] T009 [US1] In `src/scripts/run_local_component_tests.py`, implement `ensure_empty_test_db()`: run `docker rm -f postgres_test_db` (tolerating a "no such container" error), then `docker compose --profile test up -d postgres_test_db`, then poll `docker inspect --format='{{json .State.Health.Status}}' postgres_test_db` until it reports `"healthy"`, failing with a clear, specific error message after a bounded number of retries instead of hanging (FR-005, FR-011)
- [ ] T010 [US1] In `src/scripts/run_local_component_tests.py`, implement `init_schema()`: with `ENV=test` set in the process environment, call `src.database_utils.init_db.init_db()` to apply Alembic migrations and seed car data against the freshly-started test database
- [ ] T011 [US1] In `src/scripts/run_local_component_tests.py`, implement `run_unit_tests()`: run `pytest tests/unit_tests -v` as a subprocess with `ENV=test` (and `BOT_TOKEN` defaulted to a placeholder if unset) in its environment, capturing the pass/fail result without raising on a non-zero exit code
- [ ] T012 [US1] In `src/scripts/run_local_component_tests.py`, implement `run_integration_tests()`: run `pytest tests/integration_tests -v` as a subprocess with `ENV=test` in its environment, capturing the pass/fail result without raising on a non-zero exit code
- [ ] T013 [US1] In `src/scripts/run_local_component_tests.py`, implement `teardown()` — remove the `postgres_test_db` container — and wire it into `main()` via a `try`/`finally` plus a `SIGINT`/`SIGTERM` handler so it always executes, including when the developer interrupts the run with Ctrl+C (FR-010, interruption edge case)
- [ ] T014 [US1] In `src/scripts/run_local_component_tests.py`, implement `main()` orchestration that runs `ensure_empty_test_db()` → `init_schema()` → `run_unit_tests()` → `run_integration_tests()` in order, always calls `teardown()` (T013), prints a summary naming every suite's pass/fail status, and exits with a non-zero status if either suite failed (Acceptance Scenario 2) or `0` only if both passed
- [ ] T015 [US1] Add `run-local-component-tests = "src.scripts.run_local_component_tests:main"` to `[project.scripts]` in `pyproject.toml`

**Checkpoint**: `uv run run-local-component-tests` is fully functional and independently testable — User Story 1 delivers the MVP.

---

## Phase 4: User Story 2 - Run local e2e tests with one command (Priority: P2)

**Goal**: A single local command starts the test database, prepares its schema, starts the web app
against it, runs the Playwright smoke suite, and reports a pass/fail result.

**Independent Test**: Run `uv run run-local-e2e-tests` against a clean checkout with nothing else
running; confirm it starts a database, starts the web app, runs the smoke suite, reports an overall
pass/fail result, and leaves no test-only container or web app process running afterward.

### Implementation for User Story 2

- [ ] T016 [US2] Create `src/scripts/run_local_e2e_tests.py` with a `main()` entry point that checks for `docker-compose.yml` in the current directory (same pattern as T008) and exits with a clear error if not run from the repo root
- [ ] T017 [US2] In `src/scripts/run_local_e2e_tests.py`, implement `ensure_empty_test_db()`: run `docker rm -f postgres_test_db` (tolerating a "no such container" error), then `docker compose --profile test up -d postgres_test_db`, then poll `docker inspect --format='{{json .State.Health.Status}}' postgres_test_db` until it reports `"healthy"`, failing with a clear, specific error message after a bounded number of retries instead of hanging (FR-005, FR-011) — this mirrors T009's logic; each command owns its own copy rather than sharing a helper module, per plan.md's file structure
- [ ] T018 [US2] In `src/scripts/run_local_e2e_tests.py`, implement `init_schema()`: with `ENV=test` set in the process environment, call `src.database_utils.init_db.init_db()` to apply Alembic migrations and seed car data against the freshly-started test database
- [ ] T019 [US2] In `src/scripts/run_local_e2e_tests.py`, implement `start_web_app()`: launch `uvicorn web_app.main:app --host 0.0.0.0 --port 8000` as a background subprocess with `ENV=test` in its environment, poll `http://127.0.0.1:8000/` until it responds, and report a clear failure (not a hang) if it does not become ready within a bounded timeout (FR-011, edge case: web app never becomes ready)
- [ ] T020 [US2] In `src/scripts/run_local_e2e_tests.py`, implement `run_smoke_e2e_tests()`: from `tests/e2e_smoke_tests`, run `npm ci` only if `node_modules` is missing, then `npx playwright install --with-deps`, `npm run build`, and `npm run test:playwright`, capturing the pass/fail result; if `start_web_app()` did not report ready, mark this stage failed with that reason instead of attempting to run Playwright against a dead server
- [ ] T021 [US2] In `src/scripts/run_local_e2e_tests.py`, implement `teardown()` — stop the web app subprocess started by `start_web_app()` (if any) and remove the `postgres_test_db` container — and wire it into `main()` via a `try`/`finally` plus a `SIGINT`/`SIGTERM` handler so it always executes, including when the developer interrupts the run with Ctrl+C (FR-010, interruption edge case)
- [ ] T022 [US2] In `src/scripts/run_local_e2e_tests.py`, implement `main()` orchestration that runs `ensure_empty_test_db()` → `init_schema()` → `start_web_app()` → `run_smoke_e2e_tests()` in order, always calls `teardown()` (T021), prints a summary naming the stage that failed (if any), and exits with a non-zero status on failure (Acceptance Scenario 2) or `0` only if the suite passed
- [ ] T023 [US2] Add `run-local-e2e-tests = "src.scripts.run_local_e2e_tests:main"` to `[project.scripts]` in `pyproject.toml`

**Checkpoint**: `uv run run-local-component-tests` and `uv run run-local-e2e-tests` both work independently — User Stories 1 and 2 together restore full local/CI parity, now as two separate commands.

---

## Phase 5: User Story 3 - Start an empty test database on demand (Priority: P3)

**Goal**: A single local command starts (or reuses) just the empty Postgres test database, for
targeted debugging without running either full test command.

**Independent Test**: Run `uv run start-test-db` with no test database running; confirm an empty
Postgres database becomes available and ready to accept connections, and that it can run alongside
an already-running local-development database without conflict.

### Implementation for User Story 3

- [ ] T024 [US3] Create `src/scripts/start_test_db.py` with a `main()` entry point that checks for `docker-compose.yml` in the current directory (same pattern as T008/T016) and exits with a clear error if not run from the repo root
- [ ] T025 [US3] In `src/scripts/start_test_db.py`, implement startup logic: if `postgres_test_db` is already reporting `"healthy"` (via `docker inspect --format='{{json .State.Health.Status}}'`), reuse it as-is; otherwise run `docker compose --profile test up -d postgres_test_db` and poll for healthy status, failing with a clear error after a bounded number of retries — unlike User Stories 1/2's `ensure_empty_test_db()`, this MUST NOT force-remove an existing container (FR-001, FR-009, and the "on demand" framing distinct from either full test-run command)
- [ ] T026 [US3] In `src/scripts/start_test_db.py`, after the container reports healthy, call `src.database_utils.init_db.init_db()` with `ENV=test` set in the process environment so a freshly-started container has schema and seed data ready to use
- [ ] T027 [US3] Add `start-test-db = "src.scripts.start_test_db:main"` to `[project.scripts]` in `pyproject.toml`

**Checkpoint**: `uv run start-test-db`, `uv run run-local-component-tests`, and `uv run run-local-e2e-tests` all work independently, and can run concurrently with `uv run start-local-db`.

---

## Phase 6: User Story 4 - Consistent Postgres-based test database references throughout the project (Priority: P4)

**Goal**: No documentation or code comment anywhere still describes the retired SQLite-based
`ENV=test` workflow or the old single-command design.

**Independent Test**: Search the repository for the retired SQLite-based `ENV=test` database
path/handler and confirm none remain outside the unrelated in-memory `build_mock_db` mocking
fixture.

### Implementation for User Story 4

- [ ] T028 [P] [US4] Update `boring_readme_for_devs.md`: replace the "Local Development Startup With SQLite Tests" section (currently describing `export ENV=test && uv run python -m src.database_utils.init_test_db` against `src/db/local.db`) with the Postgres test container workflow, describing all three commands (`uv run start-test-db`, `uv run run-local-component-tests`, `uv run run-local-e2e-tests`), and update the "Database Migrations" paragraph and the "throwaway SQLite database" Alembic example that currently state `ENV=test` uses SQLite
- [ ] T029 [P] [US4] Update `src/db/readme.md`: replace "SQLite at `local.db` is only used for `ENV=test`." with a description of the dedicated, disposable `postgres_test_db` container used for `ENV=test`
- [ ] T030 [P] [US4] Update `AGENTS.md`: the "Database" bullet (`PostgreSQL (Production), SQLite (Local/Test)`), the "Local Dev Startup" steps referencing `src.database_utils.init_test_db` and SQLite, the PR checklist line ("Test locally against the SQLite test DB"), and the "Test Database Targeting" note (currently: "the system switches between PostgreSQL and SQLite based on the `ENV` variable") — all MUST describe the Postgres test container workflow and the two separate test commands instead, per the constitution's requirement that `AGENTS.md` stay consistent with `.specify/memory/constitution.md`
- [ ] T031 [US4] Search the repository (`grep -rn "sqlite" src/ alembic/ web_app/ telegram_bot/ queue_svc/ readme.md boring_readme_for_devs.md src/db/readme.md AGENTS.md`) and confirm zero remaining references to the retired SQLite-based `ENV=test` database, outside of `tests/pytest_fixtures/common.py`'s `build_mock_db` fixture, which is explicitly out of scope (SC-005) (depends on T007, T028, T029, T030)

**Checkpoint**: All user stories are independently functional, and no stale SQLite or single-command references remain.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final end-to-end validation across all delivered stories.

- [ ] T032 Run all seven scenarios in `specs/002-postgres-test-runner/quickstart.md` (standalone start-test-db reuse behavior, component-test run with a deliberately failing suite, e2e-test run with a deliberately failing suite, concurrent local-dev + test databases, empty-database-on-every-run, zero remaining SQLite references, and cleanup on Ctrl+C interruption for both commands) and fix any discrepancy found

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup (T001) — BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) completion. No dependency on User Story 2, 3, or 4.
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) completion. No dependency on User Story 1, 3, or 4 — it does not reuse `run_local_component_tests.py`'s code.
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) completion. No dependency on User Story 1, 2, or 4.
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) for T031's verification to be meaningful (T007 must already be done), and touches documentation that describes the commands built in Phases 3–5, so it is sequenced last even though its own file edits (T028–T030) have no code dependency on Phases 3–5.
- **Polish (Phase 7)**: Depends on Phases 1–6 all being complete (quickstart.md exercises all three new commands and the doc/code sweep).

### Within Each User Story

- User Story 1: T008 (skeleton) → T009 (db) → T010 (schema) → T011, T012 (test suites) → T013 (teardown) → T014 (orchestration) → T015 (entry point registration). All edit the same file (`run_local_component_tests.py`) except T015, so they are sequenced rather than parallelized.
- User Story 2: T016 (skeleton) → T017 (db) → T018 (schema) → T019 (web app) → T020 (e2e) → T021 (teardown) → T022 (orchestration) → T023 (entry point registration). Same-file sequencing as User Story 1, in its own file (`run_local_e2e_tests.py`).
- User Story 3: T024 (skeleton) → T025 (start/reuse) → T026 (schema) → T027 (entry point registration).
- User Story 4: T028, T029, T030 (independent files) can run in parallel; T031 depends on all three plus T007.

### Parallel Opportunities

- T002 and T003 (Foundational) touch different files and have no dependency on each other — run in parallel.
- T004 and T005 (Foundational) touch different files and both only depend on T002+T003 — run in parallel.
- T006 (Foundational) has no dependency on the SQLite-removal work at all — run in parallel with any other Foundational task.
- Once Foundational (Phase 2) is complete, User Story 1 (Phase 3), User Story 2 (Phase 4), and User Story 3 (Phase 5) can all be staffed and implemented in parallel by different developers — none of the three reads or writes another's file.
- T028, T029, T030 (User Story 4) touch three different documentation files — run in parallel.

---

## Parallel Example: Foundational Phase

```bash
# Launch independent Foundational tasks together:
Task: "Extend PostgresDBHandler with a test host/port branch in src/database_utils/postgres_database.py"
Task: "Update Settings.is_postgres_env in src/settings/settings.py"
Task: "Simplify render_as_batch in alembic/env.py"
```

## Parallel Example: User Stories 1, 2, and 3 (after Foundational)

```bash
# Three developers, three independent new files:
Task: "Build src/scripts/run_local_component_tests.py end-to-end (T008-T015)"
Task: "Build src/scripts/run_local_e2e_tests.py end-to-end (T016-T023)"
Task: "Build src/scripts/start_test_db.py end-to-end (T024-T027)"
```

## Parallel Example: User Story 4

```bash
# Launch all documentation updates for User Story 4 together:
Task: "Update boring_readme_for_devs.md's SQLite-based test workflow section"
Task: "Update src/db/readme.md's database data files note"
Task: "Update AGENTS.md's Database/Local Dev Startup/PR checklist/Test Database Targeting sections"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T007) — CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T008–T015)
4. **STOP and VALIDATE**: Run `uv run run-local-component-tests` against a clean checkout and confirm the pass/fail report and cleanup behavior
5. This alone delivers the feature's fastest-feedback core value: one command replaces manual db setup for the unit/integration loop

### Incremental Delivery

1. Setup + Foundational → PostgreSQL backs `ENV=test`, SQLite handler retired from code paths
2. Add User Story 1 → validate independently → developers get fast component-test feedback (MVP)
3. Add User Story 2 → validate independently → developers get full local/CI e2e parity
4. Add User Story 3 → validate independently → developers get a fast, targeted debugging command
5. Add User Story 4 → validate independently → no stale SQLite or single-command documentation remains anywhere
6. Polish → run the full `quickstart.md` scenario set as a final sign-off

### Parallel Team Strategy

With three developers: all complete Setup + Foundational together, then Developer A takes User Story
1, Developer B takes User Story 2, and Developer C takes User Story 3 (no shared files between any of
the three); any of them can pick up User Story 4's three documentation files in parallel once
Foundational's T007 has landed.

---

## Notes

- `tests/pytest_fixtures/common.py`'s `build_mock_db` fixture (in-memory `sqlite:///:memory:`) is
  intentionally untouched by every phase above, per the spec's Assumptions and explicit user
  clarification — it is not part of this feature's scope.
- `run_local_component_tests.py` and `run_local_e2e_tests.py` each implement their own copy of
  `ensure_empty_test_db()`, `init_schema()`, and `teardown()` rather than sharing a helper module —
  this keeps the file structure exactly as documented in plan.md, at the cost of a small amount of
  duplicated logic between the two scripts (research.md Decision 2/3).
- [P] tasks = different files, no dependency on an incomplete task
- [Story] label maps task to specific user story for traceability
- Verify `uv run run-local-component-tests` and `uv run run-local-e2e-tests` each actually exit
  non-zero on a failing suite before considering their respective stories done (Acceptance Scenario 2
  for both User Story 1 and User Story 2)
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
