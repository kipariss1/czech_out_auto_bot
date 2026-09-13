<!--
Sync Impact Report
- Version change: 1.0.0 → 2.0.0
- Modified principles:
  - II. Environment Isolation (Test vs. Production) — redefined: the test/non-test split is no
    longer SQLite vs. PostgreSQL. Every environment (`ENV=test`, `ENV=local`, `ENV=production`) now
    targets PostgreSQL; the test database is a disposable instance that starts empty, identical in
    engine to production, isolated only by being empty and separate rather than by a different
    database technology.
- Added principles: none
- Added sections: none
- Removed sections: none
- Templates requiring updates:
  - .specify/templates/plan-template.md ⚠ pending manual review for constitution alignment
  - .specify/templates/spec-template.md ⚠ pending manual review for constitution alignment
  - .specify/templates/tasks-template.md ⚠ pending manual review for constitution alignment
- Follow-up TODOs: none
-->

# Czech Out Auto Bot Constitution

## Core Principles

### I. Test-First Coverage for Parser & Worker Logic (NON-NEGOTIABLE)
Every new or modified parser (`queue_svc/parser`) or worker (`queue_svc/worker`) behavior MUST
ship with unit test coverage in `tests/unit_tests` before it is considered done. Changes touching
shared logic in `src/` that affect matching, LLM extraction, or persistence MUST also be exercised
by `tests/integration_tests`. A pull request into `main` MUST pass unit, integration, and e2e smoke
tests (as run by the GitHub Actions workflow) before merge; failing or skipped CI checks are
grounds for blocking the merge. Rationale: the parser/worker pipeline runs unattended on a fixed
schedule against a third-party site with no human in the loop, so regressions are silent until a
user misses a real match.

### II. Environment Isolation (Test vs. Production)
Every environment (`ENV=test`, `ENV=local`, `ENV=production`) MUST target PostgreSQL; no environment
may be backed by a different database engine. The test database is isolated from local-development
and production data by state, not by engine: it MUST always start empty and disposable, distinct
from the local-development and production databases, and MUST NOT persist data across runs beyond
what a given test run itself seeds. Code MUST resolve database connections exclusively through
`src.database_utils.db_handler`; hardcoded connection strings or credentials are forbidden anywhere
in application code. Rationale: running tests against the same database engine as production
eliminates an entire class of bugs that only surface from engine-specific behavior (type coercion,
constraint enforcement, SQL dialect differences); keeping the test database empty and separate
still guarantees tests stay deterministic and never touch real data.

### III. Migration-Only Schema Changes
Any change to a SQLAlchemy model in `src/models/` MUST be accompanied by a new Alembic revision
generated with `alembic revision --autogenerate`. Existing files under `alembic/versions/` MUST
NOT be edited once created — schema history is append-only. Rationale: the Telegram bot container
applies migrations on startup as a side effect of boot; a hand-edited or missing migration breaks
production schema state in a way that is hard to detect until the bot container fails.

### IV. Respectful External Scraping
Code that interacts with Bazos.cz MUST avoid aggressive concurrent requests and MUST preserve
existing rate-limiting/backoff behavior in the parser. New scraping logic MUST NOT bypass or
tighten the existing request cadence without an explicit, documented reason. Rationale: Bazos.cz
is the project's only data source; an IP ban or rate-limit response ends the bot's ability to
function entirely.

### V. Secrets & Config Hygiene
`.env` files, API keys, bot tokens, and other secrets MUST NOT be committed to the repository.
Configuration MUST be supplied via environment variables and validated at service startup rather
than assumed. Rationale: the project ships multiple Docker services (web, bot, queue, ollama) that
each depend on the same secret material; a leaked credential in git history is effectively
permanent.

## Technology & Service Boundaries

The project is a multi-service system: **web_app** (FastAPI + Jinja2 UI), **telegram_bot**
(pytelegrambotapi, also runs DB migrations/seed on startup), **queue** (scheduled parser + worker
cycle every 2 hours), **postgres_db**, and **ollama** (local LLM), orchestrated via Docker Compose.
Shared business logic (DB models, Pydantic schemas, DB utilities) lives in `src/` and MUST be
reused by all services rather than duplicated per-service. Database sessions in FastAPI endpoints
MUST be obtained through dependency injection (e.g. `Depends(get_db_session)`), not constructed ad
hoc. SQLAlchemy models MUST be centralized in `src/models/models.py`. Heavy database queries MUST
NOT be executed directly inside Jinja templates.

## Development Workflow

Branches follow `<ProjectKey>-<TicketNumber>-<short-description>` (e.g. `TCP-1234-fix-parser`) and
commits follow `[TCP-1234] Description of changes`. Work is tracked in Jira under the default
project **TCP**; tickets are assigned before work begins and transitioned through "In Progress" /
"In Review" as work progresses. Before opening a pull request, changes MUST be verified locally
against the disposable PostgreSQL test database (`ENV=test`). Pull requests into `main` are gated by the GitHub
Actions pipeline running unit, integration, and e2e smoke tests. `readme.md` MUST be updated for
user-facing changes; `boring_readme_for_devs.md` MUST be updated for architecture, testing, or
Docker-related changes.

## Governance

This constitution supersedes ad hoc practice for any conflict between the two. `AGENTS.md` is the
day-to-day operational guidance file (commands, directory layout, known gotchas) and MUST stay
consistent with this constitution; where they conflict, this constitution wins and `AGENTS.md`
MUST be updated to match.

Amendments are made by editing this file and MUST update the Sync Impact Report at the top of the
document and the version line below, following semantic versioning:
- **MAJOR**: backward-incompatible removal or redefinition of a principle.
- **MINOR**: a new principle or materially expanded section is added.
- **PATCH**: wording, clarification, or non-semantic fixes.

Pull requests that touch parser/worker logic, database models, migrations, scraping behavior, or
secrets handling MUST be reviewed for compliance with the Core Principles above before merge.
Complexity or deviation from a principle MUST be justified explicitly in the PR description.

**Version**: 2.0.0 | **Ratified**: 2026-09-11 | **Last Amended**: 2026-09-11
