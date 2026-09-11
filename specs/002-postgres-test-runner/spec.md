# Feature Specification: Local Test Runner with Postgres Test Database

**Feature Branch**: `002-postgres-test-runner`

**Created**: 2026-09-11

**Status**: Draft

**Input**: User description: "Сделай мне uv скрипт, который прогоняет тесты локально (то бишь поднимает дб, поднимает вебапп и прогоняет тесты). Опирайся на то, как это сделано в smoke-e2e-tests в джобе в гитлабе. Также замени мне тестовую дб с sqlite на пустой postgres контейнер. И добавь uv скрипт на поднятие этого тестового контейнера с дб. Также замени все референсы в коде с sqlite на новый подход с тестовым контейнером postgres." — subsequently refined: "переадаптируй спецификации под splitting the local test runner into a component-tests command and an e2e-tests command."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run local component tests with one command (Priority: P1)

A developer working on the bot wants fast local feedback on whether their change breaks the unit or
integration suites, without paying the cost of starting the web app and a browser-driven test run
every time. They want one local command that starts a test database, prepares it, runs the unit and
integration suites, and reports a trustworthy pass/fail result.

**Why this priority**: This is the test loop a developer runs most often while iterating, so it's the
highest-value, most frequently used piece of the feature. It's independent of the e2e flow and
delivers value on its own.

**Independent Test**: Can be fully tested by running the new component-test command against a clean
checkout and confirming it starts a database, runs the unit and integration test suites, and reports
an overall pass/fail result — without starting the web app or requiring a browser.

**Acceptance Scenarios**:

1. **Given** a clean checkout with no database running, **When** the developer runs the local
   component-test command, **Then** the system starts a test database, prepares its schema, runs the
   unit and integration test suites, and reports an overall pass/fail result.
2. **Given** the component-test command is running, **When** a suite fails, **Then** the command
   identifies which suite failed and exits with a non-zero status, without reporting a false success.
3. **Given** the component-test command has finished, whether it passed or failed, **When** the
   developer inspects their machine afterward, **Then** no leftover test data or dangling process
   remains to affect the next local run.

---

### User Story 2 - Run local e2e tests with one command (Priority: P2)

A developer wants to know, before pushing, whether their change would pass the browser-driven smoke
checks CI runs. They want one local command that starts a test database, prepares it, starts the web
app against it, runs the Playwright smoke suite, and reports a trustworthy pass/fail result.

**Why this priority**: This is the slower, more expensive check (it needs a running web app and a
browser), so a developer reaches for it less often than the component-test loop — but it's still
essential for full local/CI parity before pushing.

**Independent Test**: Can be fully tested by running the new e2e-test command against a clean
checkout and confirming it starts a database, starts the web app, runs the smoke e2e suite, and
reports an overall pass/fail result.

**Acceptance Scenarios**:

1. **Given** a clean checkout with no database or web app running, **When** the developer runs the
   local e2e-test command, **Then** the system starts a test database, prepares its schema, starts the
   web app against it, runs the smoke e2e suite, and reports an overall pass/fail result.
2. **Given** the e2e-test command is running, **When** the smoke suite fails, **Then** the command
   identifies the failure and exits with a non-zero status, without reporting a false success.
3. **Given** the e2e-test command has finished, whether it passed or failed, **When** the developer
   inspects their machine afterward, **Then** no leftover test database container or web app process
   remains to affect the next local run.

---

### User Story 3 - Start an empty test database on demand (Priority: P3)

A developer wants to bring up just the test database — to run a single test file by hand, inspect the
schema, or debug a failing test from either the component or e2e suite — without running either full
local test command.

**Why this priority**: Supports faster, targeted iteration once the two main commands (User Stories 1
and 2) exist; useful on its own but not the primary value driver.

**Independent Test**: Can be fully tested by running the database-only command and confirming an
empty, ready-to-use Postgres test database becomes available, independent of whether either test
command ever runs.

**Acceptance Scenarios**:

1. **Given** no test database is running, **When** the developer runs the command to start the test
   database, **Then** an empty Postgres database dedicated to tests becomes available and ready to
   accept connections.
2. **Given** a local development database is already running for non-test use, **When** the developer
   starts the test database, **Then** both run side by side without port or naming conflicts.

---

### User Story 4 - Consistent Postgres-based test database references throughout the project (Priority: P4)

A developer reading the code, tests, or docs for the `ENV=test` database workflow should see one
consistent story: a Postgres test container, not a SQLite file. No leftover instructions, code paths,
or comments should still point at the retired SQLite-based test database.

**Why this priority**: Cleanup and consistency matter for maintainability, but the feature already
delivers its core value through User Stories 1–3 even before every reference is swept.

**Independent Test**: Can be fully tested by searching the codebase and documentation for the old
SQLite-based `ENV=test` database path/handler and confirming none remain, outside of the unrelated
in-memory test-mocking fixture.

**Acceptance Scenarios**:

1. **Given** the `ENV=test` environment is selected, **When** any code path resolves a database
   connection or migration target, **Then** it resolves to the Postgres test container, never to the
   retired SQLite file.
2. **Given** the project documentation describes how to work with the `ENV=test` database, **When** a
   developer follows those instructions, **Then** the instructions describe the Postgres test
   container workflow, not the retired SQLite workflow.

---

### Edge Cases

- What happens when the developer runs either local test command while a test database container
  from a previous run is still up? The system should not fail outright; it should reuse or cleanly
  restart the container so the run still proceeds against an empty database.
- What happens when the developer runs the component-test and e2e-test commands at the same time?
  Both target the same disposable test database, so running them concurrently is not supported — this
  is a single-developer local tool, and the two commands are expected to be run one at a time against
  the shared test database.
- What happens when the test database container's port collides with another service already running
  on the machine? The developer should see a clear error identifying the conflict, rather than a hang
  or an opaque failure deep inside a test.
- What happens when the developer interrupts a local test run partway through (e.g., Ctrl+C)?
  Test-only resources (database container, and — for the e2e command — the web app process) should
  not be left running indefinitely in the background.
- What happens when Docker is not installed or not running? Either command should fail fast with a
  message identifying what's missing, rather than hanging while waiting for a container that will
  never start.
- What happens when the web app does not become ready within the expected time (e2e-test command
  only)? The command should fail with a clear message identifying that the web app didn't start,
  rather than proceeding to run tests against a non-functional app.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a local command that starts an empty, disposable Postgres database
  dedicated to tests, kept separate from the Postgres container used for local development.
- **FR-002**: System MUST provide a local command that runs the component-test flow end-to-end: start
  the test database, prepare its schema, run the unit and integration test suites, and report a
  pass/fail result — without starting the web app.
- **FR-003**: System MUST provide a separate local command that runs the e2e-test flow end-to-end:
  start the test database, prepare its schema, start the web app against that test database, run the
  smoke e2e test suite, and report a pass/fail result.
- **FR-004**: Each of the two local test commands MUST follow the same sequence of steps used by its
  corresponding CI job(s) — the component-test command mirrors the database-preparation step used by
  the CI unit-test and integration-test jobs; the e2e-test command mirrors the CI job that starts a
  database and the web app before running tests — so a passing local run is representative of a
  passing CI run.
- **FR-005**: The test database MUST start empty at the beginning of each command's run; no data from
  a previous run may carry over unless a test explicitly seeds it during that run.
- **FR-006**: The persistent `ENV=test` database MUST be backed by the Postgres test container instead
  of the current SQLite file, for every consumer of that environment (local service startup, schema
  migrations, and both local test commands).
- **FR-007**: Every code path that determines the database connection or migration target for
  `ENV=test` MUST resolve to the Postgres test container; none may still resolve to the retired
  SQLite file.
- **FR-008**: The in-memory SQLite fixture used solely to mock database access within individual
  unit/integration test cases MUST remain unchanged, as it is unrelated to the persistent `ENV=test`
  database and serves a different purpose (fast, isolated per-test mocking).
- **FR-009**: The test database MUST be able to run at the same time as the local-development database
  without conflicting with it (e.g., distinct identity/address).
- **FR-010**: System MUST provide a way to stop and remove the test database's resources after use, so
  a finished local test run — from either command — does not leave stray state or consume resources
  indefinitely.
- **FR-011**: System MUST report a clear, actionable error — instead of hanging or failing silently —
  when a required prerequisite is unavailable or a step fails (container engine unavailable, database
  not becoming ready, web app not starting).
- **FR-012**: Project documentation describing the `ENV=test` database workflow MUST be updated to
  describe the Postgres test container and the two local test commands instead of the retired SQLite
  file and single combined command.

### Key Entities

- **Test Database**: A disposable Postgres database instance dedicated to the `ENV=test` environment;
  distinct from the local-development and production databases; starts empty at the beginning of
  every command run.
- **Local Component Test Run**: The end-to-end sequence triggered by the component-test command —
  starting the test database, preparing its schema, executing the unit and integration suites, and
  reporting results.
- **Local E2E Test Run**: The end-to-end sequence triggered by the e2e-test command — starting the
  test database, preparing its schema, starting the web app, executing the smoke e2e suite, and
  reporting results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can get a complete component-test result (unit + integration) by running a
  single command, without manually starting a database themselves.
- **SC-002**: A developer can get a complete e2e-test result by running a single command, without
  manually starting a database or the web app themselves.
- **SC-003**: A local run of each command and its corresponding CI job(s) produce the same pass/fail
  outcome for the same code changes in at least 95% of runs.
- **SC-004**: Every local test run, from either command, starts from an empty database, so results
  from one run never affect the outcome of the next.
- **SC-005**: Searching the codebase and documentation for the retired SQLite-based `ENV=test`
  database turns up zero references outside of the unrelated in-memory test-mocking fixture.
- **SC-006**: Starting the dedicated test database never disrupts an already-running
  local-development database, and vice versa.

## Assumptions

- Docker and Docker Compose are available on the developer's machine, matching the project's existing
  stated requirements.
- "Component tests" means the same two suites the CI workflow's `unit-tests` and `integration-tests`
  jobs run today; "e2e tests" means the same Playwright smoke suite the CI workflow's
  `smoke-e2e-tests` job runs. Together they still cover everything the original single-command design
  covered — the split changes how a developer invokes them, not what gets tested.
- The component-test command starts and prepares the test database the same way the e2e-test command
  does (for CI parity with the "Init DB" step both `unit-tests` and `integration-tests` CI jobs run),
  even though it does not start the web app.
- Running the component-test and e2e-test commands at the same time, against the same shared test
  database, is out of scope — they are expected to be run one at a time, consistent with this being a
  single-developer local tool.
- Per explicit user direction, the in-memory SQLite fixture used only for per-test database mocking in
  unit/integration tests is out of scope for this migration; only the persistent `ENV=test` database
  moves to Postgres.
- The test database container is ephemeral (no persisted data volume across restarts), matching the
  request for an "empty" Postgres container, and is a separate resource from the existing
  local-development database container.
- The project's existing script/dependency runner is reused as the mechanism for exposing the local
  commands, consistent with how equivalent local commands are already exposed in the project today.
