# Phase 1 Data Model: Local Test Runner with Postgres Test Database

This feature introduces local developer tooling, not application data. There are no new persisted
domain tables, and no changes to `src/models/models.py`. The "entities" below are operational
concepts the new scripts and Compose service reason about, captured here for clarity going into
`/speckit-tasks`.

**Revision note**: The previous version of this document had one `Local Test Run` entity for a single
combined command. Per the component/e2e command split, that is now two entities — `Local Component
Test Run` and `Local E2E Test Run` — that both build on the same `Test Database` entity.

## Test Database (container)

Represents the dedicated, disposable PostgreSQL instance backing `ENV=test`.

| Field | Description |
|---|---|
| `container_name` | Fixed identifier (`postgres_test_db`) distinct from the local-dev container (`postgres_db`), used for health checks, force-recreate, and teardown. |
| `image` | `postgres:15` — same image/version as the local-development and production database, per the amended constitution's "same engine everywhere" rule. |
| `host` / `port` | `localhost:5433` as seen from the host machine (where tests, migrations, and the web app under test run); distinct from the local-dev database's `localhost:5432` so both can run concurrently. |
| `credentials` | Reuses the existing `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` values already resolved through `src.settings.settings`; no separate test credentials are introduced. |
| `persistence` | None — no volume is mounted, so removing the container discards all data. This is what makes "empty" a structural guarantee rather than a scripted convention. |
| `lifecycle_state` | `absent` → `starting` → `healthy` → (`in use`) → `stopped/removed`. `start-test-db` may leave it `healthy` and running after the command returns (User Story 3). `run-local-component-tests` and `run-local-e2e-tests` each independently drive it from `absent`/`healthy` back to `stopped/removed` by the end of their own run (FR-010) — whichever of the two ran last owns the teardown for that invocation. |

**Validation / invariants**:
- Neither `run-local-component-tests` nor `run-local-e2e-tests` may proceed to schema initialization
  until the container reports healthy (FR-011 — fail fast with a clear error otherwise, rather than
  hanging).
- Both test-running commands MUST force-recreate this container before use, so no state from a
  previous run of either command (or from a `start-test-db` debugging session) leaks into the current
  run's results (FR-005).
- This container's port/name MUST NOT collide with the local-development database's (FR-009).
- The two test-running commands are not required to coordinate if run concurrently against this one
  container (see spec Edge Cases and research.md Decision 7) — this is an accepted limitation, not an
  invariant to enforce in code.

## Local Component Test Run

Represents one end-to-end invocation of `run-local-component-tests`.

| Field | Description |
|---|---|
| `stages` | Ordered: `ensure_empty_test_db` → `init_schema` → `run_unit_tests` → `run_integration_tests` → `teardown`. |
| `stage_result` | Per stage: `passed` or `failed`. |
| `overall_result` | `passed` only if every stage reports `passed`; otherwise `failed`. Drives the process exit code (FR-002, User Story 1 Acceptance Scenario 2). |
| `teardown_trigger` | Normal completion (pass or fail) or interruption (e.g. Ctrl+C) — both MUST reach the `teardown` stage so no test-only container is left running (FR-010, edge case on interruption). |

**Validation / invariants**:
- `teardown` MUST run regardless of whether earlier stages passed, failed, or the run was
  interrupted — implemented as a `finally`/signal-handled cleanup path.
- The reported `overall_result` MUST name which suite(s) failed, not collapse to a bare non-zero exit
  code with no explanation.
- This entity never starts the web app — that belongs exclusively to `Local E2E Test Run`.

## Local E2E Test Run

Represents one end-to-end invocation of `run-local-e2e-tests`.

| Field | Description |
|---|---|
| `stages` | Ordered: `ensure_empty_test_db` → `init_schema` → `start_web_app` → `run_smoke_e2e_tests` → `teardown`. |
| `stage_result` | Per stage: `passed`, `failed`, or `skipped` (e.g. the e2e stage is marked failed-fast if `start_web_app` never reports ready, per FR-011, rather than attempting to run Playwright against a dead server). |
| `overall_result` | `passed` only if every stage that was expected to run reports `passed`; otherwise `failed`. Drives the process exit code (FR-003, User Story 2 Acceptance Scenario 2). |
| `teardown_trigger` | Normal completion (pass or fail) or interruption (e.g. Ctrl+C) — both MUST reach the `teardown` stage so no test-only container or web app process is left running (FR-010, edge case on interruption). |

**Validation / invariants**:
- `teardown` MUST stop the web app subprocess (if started) in addition to removing the test database
  container — the superset of what `Local Component Test Run`'s teardown does.
- The reported `overall_result` MUST name which stage failed (Acceptance Scenario 2).
