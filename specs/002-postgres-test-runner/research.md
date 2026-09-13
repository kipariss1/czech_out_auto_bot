# Phase 0 Research: Local Test Runner with Postgres Test Database

No `NEEDS CLARIFICATION` markers remain in the Technical Context — every open question raised during
specification and planning (SQLite scope, the constitution's SQLite mandate, and the component/e2e
command split) was already resolved directly with the user before this phase. This document records
the design decisions made in translating the spec's requirements into a concrete approach, and the
alternatives considered for each.

**Revision note**: This supersedes the previous version of this document, which had drifted ahead of
spec.md/plan.md by describing a two-command split without the rest of the artifacts (or a complete
rationale) catching up. That drift was caught by `/speckit-analyze` and resolved by updating spec.md
first; this document now matches the current spec.

## 1. Where the test database lives: a new Compose service, not a reused one

**Decision**: Add a new `postgres_test_db` service to the existing `docker-compose.yml`, using the
same `postgres:15` image as the local-dev `postgres_db` service, published on a distinct host port
(`5433`), with no persistent volume, and gated behind a Compose `profiles: ["test"]` entry so a plain
`docker compose up` never starts it.

**Rationale**: A dedicated service keeps "empty and disposable" a structural property (no volume
means the container's data disappears the moment it's removed) rather than something a script has to
enforce by convention. A distinct container name and port guarantees it can run alongside the
existing local-dev database (FR-009, SC-006) without any coordination logic. Profile-gating keeps the
default `docker compose up` (production/local flow) behavior completely unchanged. Both new
test-running commands (component and e2e) and the standalone start-db command target this one shared
service.

**Alternatives considered**:
- *Reuse `postgres_db` with a different database/schema name*: rejected — it would let local-dev and
  test workloads share one container's lifecycle, so stopping/restarting one for local-dev reasons
  would also disrupt the test database, and a scripting bug could let test runs touch local-dev data.
- *Spin up an ad hoc container from Python (e.g. a `testcontainers`-style library)*: rejected — it
  would introduce a new dependency and a second way of managing containers when Docker Compose is
  already the project's established mechanism, used the same way for `postgres_db` and `ollama`.

## 2. Splitting the local test runner into a component-tests command and an e2e-tests command

**Decision**: Instead of one combined command that always runs unit + integration + Playwright smoke
e2e, provide two independent commands:
- `run-local-component-tests` — starts the test database, prepares its schema, runs
  `tests/unit_tests` and `tests/integration_tests`, reports pass/fail. Never starts the web app.
- `run-local-e2e-tests` — starts the test database, prepares its schema, starts the web app against
  it, runs the Playwright suite in `tests/e2e_smoke_tests`, reports pass/fail.

Each command independently owns the full lifecycle of its own run: it force-recreates
`postgres_test_db` at the start (guaranteeing an empty database per FR-005) and tears down its own
resources at the end (FR-010), regardless of which command ran most recently.

**Rationale**: The component suites (unit + integration) run in seconds and don't need a browser or a
running web app; the e2e suite is materially slower and has a heavier dependency footprint (Node,
Playwright, browser binaries). Splitting them lets a developer get fast, cheap feedback in their
normal edit-test loop (component command) and reach for the slower, heavier check (e2e command) only
when they specifically want browser-level confidence — mirroring how the CI workflow itself already
separates `unit-tests`/`integration-tests` from `smoke-e2e-tests` as distinct jobs. This was an
explicit user decision, made after the original single-command design was already planned.

**Alternatives considered**:
- *Keep the single combined `run-local-tests` command* (the original design): rejected per explicit
  user direction — it forces every local test run to pay the e2e suite's setup cost even when a
  developer only wants unit/integration feedback.
- *Split further, e.g. separate unit and integration commands*: rejected — unit and integration tests
  are both fast, in-process pytest suites with no shared heavy dependency to isolate away from each
  other, unlike the e2e suite's browser/Node footprint; splitting them further would add commands
  without a corresponding cost being avoided.

## 3. Guaranteeing an empty database on every full test run

**Decision**: Both `run-local-component-tests` and `run-local-e2e-tests` always force-remove and
recreate the `postgres_test_db` container before running migrations, guaranteeing a fresh, empty
database every time either one runs. `start-test-db` (User Story 3, the standalone command) instead
reuses an already-healthy container if one exists, only starting a fresh one when none is running.

**Rationale**: FR-005 requires every command's run to start from an empty database — recreating the
container is the simplest and most reliable definition of "empty" (no need to enumerate tables or
reset sequences), and applying this uniformly to both commands means neither one's result depends on
whether the other, or a `start-test-db` debugging session, ran first. The standalone command exists so
a developer can bring up the database for manual, possibly long-lived debugging (User Story 3);
force-wiping it on every invocation would destroy in-progress debugging state and contradict the "on
demand" framing of that story.

**Alternatives considered**:
- *`TRUNCATE` all tables instead of recreating the container*: rejected — more code (must enumerate
  every table and reset identity sequences) for no benefit over removing the container outright.
- *Always reuse the container in all three commands*: rejected — this would violate FR-005, since a
  prior run's leftover data (or a leftover schema from a stale migration state) could silently affect
  the next command's results.
- *Have only one of the two test commands force-recreate, and have the other assume the database is
  already prepared*: rejected — it would make each command's result depend on invocation order (e.g.
  running the e2e command first, then the component command, might behave differently than the
  reverse), which contradicts each command being independently, deterministically testable
  (spec Independent Test criteria for User Stories 1 and 2).

## 4. Resolving the `ENV=test` connection string

**Decision**: Extend `PostgresDBHandler.db_url()` with a third branch for `env == "test"`, pointing at
`localhost:5433` (the new dedicated port), instead of introducing a new handler class.

**Rationale**: `PostgresDBHandler` already parameterizes only the target host for `local` vs.
`production`; adding a `test` host/port pair is the smallest change that fits the existing shape.
`SqliteDBHandler` is deleted outright, along with its branches in `DBFactory` and
`src/database_utils/migrations.py::get_database_url` (FR-007). This resolution path is shared by all
three new commands — the split does not require a second handler or a second connection string.

**Alternatives considered**:
- *Introduce a distinct `TestPostgresDBHandler` class*: rejected — it would duplicate the same
  connection-string-building logic `PostgresDBHandler` already has, for a difference that's just one
  more host/port pair.

## 5. `build_mock_db` is out of scope

**Decision**: The in-memory `sqlite:///:memory:` fixture in `tests/pytest_fixtures/common.py` is left
completely unchanged.

**Rationale**: Confirmed directly with the user (see spec Assumptions). It mocks a SQLAlchemy
`Session` object for isolated, fast per-test assertions and never represents a real running database;
routing it through the Postgres test container would require that container for every unit test run
and remove the per-test isolation/speed the fixture exists to provide. This is unaffected by the
component/e2e command split — `run-local-component-tests` runs the suites that use this fixture, but
does not change how they use it.

**Alternatives considered**: None weighed — this was a direct scope decision from the user, not an
open design question.

## 6. Constitution amendment

**Decision**: Amend `.specify/memory/constitution.md` Principle II so the test/non-test split is
defined by database state (empty/disposable vs. persistent) rather than by engine (SQLite vs.
PostgreSQL); bump the constitution version 1.0.0 → 2.0.0 (principle redefinition = MAJOR, per the
constitution's own Governance rules).

**Rationale**: The constitution, as ratified, directly required SQLite for `ENV=test`. Shipping this
feature without updating it would leave the constitution actively contradicting the codebase it
governs. The user explicitly chose amendment over recording a Complexity Tracking exception. The
later component/e2e split does not require any further constitution change — Principle II is about
database engine/state, not about how many local commands invoke it.

**Alternatives considered**:
- *Record a justified deviation in Complexity Tracking, leave the constitution text stale*: this was
  offered as an option and explicitly declined by the user in favor of amending the constitution.

## 7. Concurrent invocation of the two test commands is out of scope

**Decision**: `run-local-component-tests` and `run-local-e2e-tests` are not required to support being
run at the same time against the shared `postgres_test_db` container.

**Rationale**: Both commands force-recreate the same container at startup (Decision 3). If run
concurrently, one command's force-recreate could invalidate the other's in-progress run. This is
acceptable because the tool targets a single developer working locally; serializing the two commands
is a trivial workflow constraint, and building cross-process coordination (locking, queuing) for a
scenario the spec explicitly treats as unsupported would add complexity with no corresponding user
value.

**Alternatives considered**:
- *Add file-lock-based coordination so the two commands queue behind each other*: rejected as
  unnecessary complexity for a single-developer local tool; the spec's edge case documents this as an
  accepted limitation rather than a bug to engineer around.
