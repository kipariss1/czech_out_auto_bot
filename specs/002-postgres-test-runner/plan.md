# Implementation Plan: Local Test Runner with Postgres Test Database

**Branch**: `002-postgres-test-runner` | **Date**: 2026-09-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-postgres-test-runner/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Replace the SQLite-backed `ENV=test` database with a dedicated, disposable PostgreSQL container, and
add three `uv run` console scripts: one that starts just that empty test database (for ad hoc local
debugging), one that runs the local **component-test** flow (start the test database, apply
migrations, run the unit and integration suites, report a pass/fail result — no web app involved),
and one that runs the local **e2e-test** flow (start the test database, apply migrations, start the
web app against it, run the Playwright smoke suite, report a pass/fail result) — mirroring the
sequence the CI workflow's `unit-tests`/`integration-tests` jobs and `smoke-e2e-tests` job
respectively already use. Every remaining SQLite reference for the persistent `ENV=test` database
(code and docs) is removed; the unrelated in-memory SQLite fixture used to mock the DB inside
individual unit/integration test cases (`build_mock_db`) is left untouched.

**Revision note**: This plan supersedes the earlier single-`run-local-tests`-command design. Per
explicit user direction, the local test runner is split into two independent commands (component vs.
e2e) instead of one combined command, so a developer can get fast component-test feedback without
paying the cost of starting the web app and a browser every time.

## Technical Context

**Language/Version**: Python 3.11 (existing `uv`-managed scripts); Node.js 20 for the existing Playwright smoke tests (unchanged)

**Primary Dependencies**: `uv` (script runner), Docker & Docker Compose v2 (container orchestration), SQLAlchemy 2.0 + Alembic (ORM/migrations), FastAPI/uvicorn (web app under test, e2e command only), pytest (unit/integration suites, component command), Playwright (smoke e2e suite, e2e command)

**Storage**: PostgreSQL 15 for every environment (`test`, `local`, `production`). `ENV=test` now points at a new, dedicated, ephemeral Postgres container (image `postgres:15`, no persistent volume), distinct from the existing `postgres_db` local-development container. Both new test-running commands independently start/prepare this same container.

**Testing**: pytest (`tests/unit_tests`, `tests/integration_tests`) run by the component-test command; Playwright/TypeScript (`tests/e2e_smoke_tests`) run by the separate e2e-test command — this feature is itself the local test-orchestration tooling that runs those suites.

**Target Platform**: Developer workstations (macOS/Linux) with Docker Desktop or Docker Engine + Compose v2 installed.

**Project Type**: Single project — local developer tooling (three new `uv run` console scripts) layered onto the existing multi-service Docker Compose application. No new deployable service is introduced.

**Performance Goals**: N/A — this is local developer tooling, not a runtime service. The relevant goal is developer wall-clock convenience: the component command in particular should let a developer skip the web-app/browser startup cost when they only need unit/integration feedback.

**Constraints**: MUST NOT disturb an already-running local-development Postgres container (distinct container name and published port); MUST guarantee an empty database at the start of each command's own run; MUST fail fast with an actionable error instead of hanging when a prerequisite is missing or a step fails; MUST clean up its own container/process resources on normal completion and on interruption (e.g. Ctrl+C); the component-test and e2e-test commands are not required to support being run concurrently against the shared test database (single-developer local tool, run one at a time).

**Scale/Scope**: Single-developer local execution; one dedicated test database container shared sequentially by both new commands; no concurrency requirements beyond safely coexisting with the local-development database container.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This feature required amending the constitution before it could pass this gate: Principle II
("Environment Isolation") previously hard-required SQLite for `ENV=test`, which this feature
directly contradicts. Per explicit user direction, the constitution was amended in place (version
1.0.0 → 2.0.0) so the test/non-test split is defined by database *state* (empty and disposable vs.
persistent) rather than by database *engine* — every environment now targets PostgreSQL. The gate
below is evaluated against the amended constitution and is unaffected by the later component/e2e
command split (that split changes tooling shape, not database engine or isolation semantics).

| Principle | Status | Notes |
|---|---|---|
| I. Test-First Coverage for Parser & Worker Logic | PASS | This feature touches no parser/worker behavior. The split still satisfies the "PR MUST pass unit, integration, and e2e smoke tests" gate — the two local commands together cover the same three suites CI does; a developer just invokes them separately. |
| II. Environment Isolation (Test vs. Production) | PASS (post-amendment) | `ENV=test` now resolves to PostgreSQL via `src.database_utils.db_handler`, isolated from `local`/`production` by being a separate, empty, disposable container — not a different engine. No hardcoded connection strings are introduced. Both new test commands and the standalone start-db command share this same resolution path. |
| III. Migration-Only Schema Changes | PASS / N/A | No SQLAlchemy model changes; no new Alembic revision is needed. Existing migrations continue to apply unmodified against Postgres for `ENV=test`. |
| IV. Respectful External Scraping | PASS / N/A | Not touched by this feature. |
| V. Secrets & Config Hygiene | PASS | The test database reuses the existing `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` values already resolved through `src.settings.settings`; no new secrets are introduced and none may be hardcoded in the new scripts. |

No unjustified violations remain; Complexity Tracking is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/002-postgres-test-runner/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan; STALE, needs regeneration for the two-command split)
```

No `contracts/` directory is produced: this feature has no external API/CLI-argument contract to
document beyond the three new `uv run` entry points, which are covered in `quickstart.md`.

### Source Code (repository root)

```text
src/
├── database_utils/
│   ├── database_factory.py     # DBFactory — drops the SqliteDBHandler branch
│   ├── postgres_database.py    # PostgresDBHandler — gains a third (test) host/port branch
│   ├── migrations.py           # get_database_url() — drops the SqliteDBHandler branch
│   ├── init_db.py              # unchanged: runs migrations/seed against whatever ENV resolves to
│   ├── init_test_db.py         # unchanged: seeds sample users/searches for ENV=test
│   └── sqlite_database.py      # REMOVED
├── scripts/
│   ├── start_local_db.py             # unchanged: existing local-dev Postgres helper
│   ├── start_test_db.py              # NEW: starts/reuses the empty test Postgres container
│   ├── run_local_component_tests.py  # NEW: db → schema → unit tests → integration tests
│   ├── run_local_e2e_tests.py        # NEW: db → schema → web app → Playwright smoke e2e
│   ├── generate_migration.py         # unchanged
│   └── deploy.py                      # unchanged
├── models/                      # unchanged
└── settings/                    # settings.py: is_postgres_env now covers ENV=test too

web_app/                         # unchanged; started only by run_local_e2e_tests.py, against the test DB
telegram_bot/                    # unchanged

alembic/
└── env.py                       # simplified: Postgres-only statement rendering, no sqlite branch

tests/
├── unit_tests/                  # run by run_local_component_tests.py
├── integration_tests/           # run by run_local_component_tests.py
├── e2e_smoke_tests/              # Playwright suite, run by run_local_e2e_tests.py against the running web app
└── pytest_fixtures/
    └── common.py                # build_mock_db: UNCHANGED (stays in-memory SQLite; out of scope)

docker-compose.yml                # + new postgres_test_db service, gated behind a "test" profile
pyproject.toml                    # + new [project.scripts] entries: start-test-db, run-local-component-tests, run-local-e2e-tests
readme.md / boring_readme_for_devs.md / src/db/readme.md / AGENTS.md   # updated to describe the Postgres test workflow and the two local test commands
```

**Structure Decision**: Single project (Option 1). This feature adds three new files under
`src/scripts/` (one more than the original single-command design), extends three existing
`src/database_utils/*` modules and `alembic/env.py`, adds one Compose service, and adds three
`pyproject.toml` script entries — no new top-level service or project is introduced.

## Complexity Tracking

*No entries — the Constitution Check gate passes cleanly after the constitution amendment described above. The component/e2e split adds one extra script file relative to the original design but does not introduce a new project, service, or architectural pattern.*
