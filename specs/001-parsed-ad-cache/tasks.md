# Tasks: Parsed Advertisement Cache

**Input**: Design documents from `/specs/001-parsed-ad-cache/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included as required tasks — Constitution Principle I ("Test-First Coverage for Parser &
Worker Logic (NON-NEGOTIABLE)") mandates unit + integration coverage for any new parser/worker
behavior, so test tasks are not optional for this feature.

**Organization**: Tasks are grouped by user story (from spec.md: US1 = P1, US2 = P2, US3 = P3) to
enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Every task includes its exact file path

## Path Conventions

Single existing project — paths are relative to the repository root (`src/`, `queue_svc/`,
`alembic/`, `tests/`), per plan.md's Structure Decision. No new top-level directories.

---

## Phase 1: Setup

**Purpose**: Confirm the environment is ready before touching schema or code

- [ ] T001 Confirm branch `001-parsed-ad-cache` is checked out and the local SQLite test DB is
      current by running `export ENV=test && uv run python -m src.database_utils.init_test_db`
      from the repository root (per quickstart.md step 1)

**Checkpoint**: Environment ready — no dependency changes needed for this feature (no new
third-party packages per plan.md's Technical Context)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema and configuration changes that every user story depends on

**⚠️ CRITICAL**: No user story task may begin until this phase is complete

- [ ] T002 [P] In `src/models/models.py`, add a `cached_at` column to `ParsedAdvertisementCache`:
      `Column(DateTime(timezone=True), server_default=func.now(), nullable=False)` — the same
      pattern already used for `CarSearch.created_at` / `User.created_at` — per data-model.md's
      field table (type "DateTime (timezone-aware)", "not null", `server_default=func.now()`)
- [ ] T003 [P] In `src/settings/settings.py`, add `PARSED_AD_CACHE_RETENTION_DAYS: int = 30` to the
      `Settings` class and a `parsed_ad_cache_retention_days` property returning it, following the
      exact existing pattern used for `OLLAMA_MODEL`/`ollama_model` (per research.md's "Retention
      period is a `Settings` field" decision)
- [ ] T004 Generate a new Alembic migration adding the `cached_at` column to
      `Parsed_Advertisements_Cache` via `uv run alembic revision --autogenerate -m "add cached_at
      to parsed advertisement cache"` in `alembic/versions/`, verifying its `down_revision` points
      at the current head `60b4deb1bd84` (depends on T002; do not hand-edit `60b4deb1bd84_...py`
      itself, per Constitution Principle III)

**Checkpoint**: Schema and settings exist — user story implementation can now begin

---

## Phase 3: User Story 1 - Reuse a previously parsed advertisement (Priority: P1) 🎯 MVP

**Goal**: Before calling the LLM for an advertisement, the worker checks
`Parsed_Advertisements_Cache` for a non-expired result for that `(bazos_id, car_id)` pair and uses
it instead of calling the LLM again.

**Independent Test**: Seed a `Parsed_Advertisements_Cache` row for a fixture advertisement/car
model, run `BazosWorker.process_queue()` against a queue containing that same advertisement, and
verify the mocked LLM's `process` is never called while matching/notification behavior is
unchanged.

### Tests for User Story 1

- [ ] T005 [P] [US1] Unit test in `tests/unit_tests/worker/test_bazos_worker.py` for the
      cache-lookup helper: returns the stored result when a row exists with `cached_at` within
      `settings.parsed_ad_cache_retention_days` days, returns `None` when no row exists for that
      `(bazos_id, car_id)`, and returns `None` when the row's `cached_at` is older than the
      retention period
- [ ] T006 [P] [US1] Integration test in
      `tests/integration_tests/queue_svc/test_parser_worker.py`: seed a `Parsed_Advertisements_Cache`
      row matching a fixture ad's `bazos_id`/`car_id`, run the worker, and assert the mocked
      `worker.llm.process` is never called while the existing matching/notification assertions
      still pass using the seeded `parsed_result`

### Implementation for User Story 1

- [ ] T007 [US1] Implement `_get_cached_parse_result(self, bazos_id: int, car_id: int)` in
      `queue_svc/worker/bazos_worker.py`: query `ParsedAdvertisementCache` filtered by
      `bazos_id`/`car_id`, return `row.parsed_result` if found and
      `row.cached_at >= now - settings.parsed_ad_cache_retention_days days`, else `None`; wrap the
      whole method body in `try`/`except Exception` that logs via `logger.exception(...)` and
      returns `None` on failure (depends on T002, T003; per research.md's failure-isolation
      decision so a cache read failure never raises into the caller)
- [ ] T008 [US1] In `_process_row_in_queue` (`queue_svc/worker/bazos_worker.py`), before calling
      `self.llm.process(ad_text=ad.text, car=car)`, call
      `self._get_cached_parse_result(int(ad.id), car.id)`; if it returns a non-`None` result use
      it as `res` and skip the LLM call, leaving the existing `res["price"] = str(ad.price)`
      override and all downstream matching/notification logic untouched (depends on T007)

**Checkpoint**: User Story 1 is independently functional and testable — cache hits skip the LLM
call with no change to matching/notification behavior

---

## Phase 4: User Story 2 - Persist a new parse result (Priority: P2)

**Goal**: After the LLM parses an advertisement, the result is written to
`Parsed_Advertisements_Cache` so User Story 1 can reuse it on a later cycle; reprocessing an
already-cached pair updates the existing row instead of duplicating it.

**Independent Test**: With no existing cache row for a fixture advertisement/car model, run the
worker, then verify a new `Parsed_Advertisements_Cache` row now holds the LLM's result for that
`(bazos_id, car_id)` pair; seed an existing row for that same pair, reprocess, and verify the row
is updated in place (no `IntegrityError`, no duplicate row).

### Tests for User Story 2

- [ ] T009 [P] [US2] Unit test in `tests/unit_tests/worker/test_bazos_worker.py` for the
      cache-write helper: inserts a new row when none exists for `(bazos_id, car_id)`; updates the
      existing row's `parsed_result` and `cached_at` in place (no new row, no `IntegrityError`)
      when one already exists for that same key
- [ ] T010 [P] [US2] Integration test in
      `tests/integration_tests/queue_svc/test_parser_worker.py`: with no seeded cache row, run the
      worker and assert the mocked LLM is called once and a `Parsed_Advertisements_Cache` row now
      exists holding its result

### Implementation for User Story 2

- [ ] T011 [US2] Implement `_save_parsed_result_to_cache(self, bazos_id: int, car_id: int, result:
      CarAdParseResult)` in `queue_svc/worker/bazos_worker.py`: query by `(bazos_id, car_id)`; if a
      row exists, update its `parsed_result` and `cached_at`; otherwise insert a new row; commit;
      wrap the method body in `try`/`except Exception` logging via `logger.exception(...)` so a
      write failure never raises into the caller (depends on T002, T003; per research.md's
      upsert and failure-isolation decisions)
- [ ] T012 [US2] In `_process_row_in_queue` (`queue_svc/worker/bazos_worker.py`), on the cache-miss
      path (after `res = self.llm.process(...)`, before the `res["price"] = str(ad.price)`
      override line), call `self._save_parsed_result_to_cache(int(ad.id), car.id, res)` with the
      raw LLM result, per research.md's "cache stores the raw LLM result" decision (depends on
      T011 and T008, since both edit `_process_row_in_queue`)

**Checkpoint**: User Stories 1 AND 2 both work independently — new results are cached and reused
on the next encounter

---

## Phase 5: User Story 3 - Automatic expiration of old results (Priority: P3)

**Goal**: Cache rows older than `settings.parsed_ad_cache_retention_days` (default 30) are deleted
automatically as part of the existing recurring `queue` cycle, with no manual step.

**Independent Test**: Seed one `Parsed_Advertisements_Cache` row with a `cached_at` older than the
retention period and one within it, run the cleanup step, and verify only the expired row is gone.

### Tests for User Story 3

- [ ] T013 [P] [US3] Unit test in `tests/unit_tests/worker/test_cache_cleanup.py` for the cleanup
      query: deletes rows with `cached_at` older than `settings.parsed_ad_cache_retention_days`
      days, leaves rows within the retention period untouched, and is a no-op (no error) when no
      rows are expired
- [ ] T014 [P] [US3] Integration test in `tests/integration_tests/queue_svc/test_parser_worker.py`
      (or a new `tests/integration_tests/queue_svc/test_cache_cleanup.py`): seed one expired and
      one fresh `Parsed_Advertisements_Cache` row, invoke the cleanup step, and assert only the
      expired row was deleted

### Implementation for User Story 3

- [ ] T015 [US3] Implement a cleanup method (e.g. `BazosWorker.cleanup_expired_cache()`) in
      `queue_svc/worker/bazos_worker.py` that deletes all `ParsedAdvertisementCache` rows where
      `cached_at < now - settings.parsed_ad_cache_retention_days days` and commits (depends on
      T002, T003)
- [ ] T016 [US3] In `queue_svc/main.py`, add `_run_cache_cleanup()` following the exact shape of
      `_run_parser()`/`_run_worker()` (own started_at/finished_at/elapsed logging,
      `db_handler.close_db_connection()` in a `finally`), call the method from T015, and append it
      as a third step in `run_cycle()` (`_run_parser()` → `_run_worker()` → `_run_cache_cleanup()`)
      so a cleanup failure is caught the same way the existing steps are and never stops the next
      scheduled cycle (depends on T015)

**Checkpoint**: All three user stories are independently functional — the cache is read, written,
and expired automatically

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation required by the project's Development Workflow

- [ ] T017 Run the full regression suite: `export ENV=test && uv run pytest tests/unit_tests -v`
      and `uv run pytest tests/integration_tests -v`, confirming all existing tests plus the new
      cache/cleanup tests pass (depends on T001-T016; per quickstart.md step 5 and Constitution
      Principle I)
- [ ] T018 [P] Update `boring_readme_for_devs.md` to document the parse-result cache behavior and
      the new `PARSED_AD_CACHE_RETENTION_DAYS` environment variable, per Constitution's
      Development Workflow section ("update `boring_readme_for_devs.md` for architecture, testing,
      or Docker-related changes")

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends only on Foundational
- **User Story 2 (Phase 4)**: Depends on Foundational; T012 also depends on T008 (both edit
  `_process_row_in_queue`)
- **User Story 3 (Phase 5)**: Depends only on Foundational — independent of US1/US2's code paths
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### Parallel Opportunities

- T002 and T003 (Phase 2) — different files
- T005 and T006 (US1 tests) — different files
- T009 and T010 (US2 tests) — different files
- T013 and T014 (US3 tests) — different files
- Once Phase 2 is complete, US1 and US3 implementation work can proceed in parallel (US2 must
  follow US1's T008 for the shared-file dependency at T012)
- T018 (docs) can run in parallel with T017 (regression run) since they touch different files

---

## Parallel Example: Phase 2 (Foundational)

```bash
Task: "Add cached_at column to ParsedAdvertisementCache in src/models/models.py"
Task: "Add PARSED_AD_CACHE_RETENTION_DAYS setting in src/settings/settings.py"
```

## Parallel Example: User Story 1 tests

```bash
Task: "Unit test cache-lookup helper in tests/unit_tests/worker/test_bazos_worker.py"
Task: "Integration test cache-hit skips LLM in tests/integration_tests/queue_svc/test_parser_worker.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (schema + settings)
3. Complete Phase 3: User Story 1 (cache lookup skips the LLM for seeded rows)
4. **STOP and VALIDATE**: run T005/T006 independently — the MVP delivers the cost-saving reuse
   behavior even before anything writes new cache rows on its own
5. Continue to US2 so the cache actually populates itself in production, then US3 so it doesn't
   grow forever

### Incremental Delivery

1. Setup + Foundational → schema/config ready
2. Add User Story 1 → cache reuse works (seed-only until US2 lands) → validate independently
3. Add User Story 2 → cache is now self-populating → validate independently
4. Add User Story 3 → cache stops growing unbounded → validate independently
5. Polish → full regression + docs
