# Implementation Plan: Parsed Advertisement Cache

**Branch**: `001-parsed-ad-cache` | **Date**: 2026-09-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-parsed-ad-cache/spec.md`

## Summary

`BazosWorker` must stop re-invoking the LLM for an advertisement it has already parsed for a given
car model, by consulting `ParsedAdvertisementCache` before calling `LangChainCarAdClient.process`,
writing the LLM's result back to that table afterwards (upserting on the existing
`(bazos_id, car_id)` unique constraint), and periodically deleting cache rows older than a
configurable retention period (default 30 days). The cache and cleanup are additive to the
existing per-ad loop in `_process_row_in_queue` and the existing `queue_svc/main.py` cycle —
no new services, no new scheduler, and no change to scraping behavior.

## Technical Context

**Language/Version**: Python >= 3.11 (existing project baseline)

**Primary Dependencies**: SQLAlchemy 2.0 (existing `ParsedAdvertisementCache` model), Alembic
(schema migration for a new timestamp column), pydantic-settings (`src/settings/settings.py`,
for the retention-period setting), no new third-party dependencies

**Storage**: PostgreSQL (`local`/`production`) and SQLite (`test`), via the existing
`Parsed_Advertisements_Cache` table — extended with one new timestamp column

**Testing**: pytest (`tests/unit_tests`, `tests/integration_tests`), using the existing
`build_mock_db` in-memory SQLite fixture and `monkeypatch`-based LLM/DB mocking already used in
`tests/integration_tests/queue_svc/test_parser_worker.py`

**Target Platform**: Linux container (`queue` Docker Compose service), unattended background
worker — no user-facing surface

**Project Type**: Single project (existing monorepo layout: `src/`, `queue_svc/`, `tests/`) — no
new top-level project/service

**Performance Goals**: No new explicit throughput target; a cache lookup/write is a single indexed
query per advertisement (covered by the existing `uq_parsed_ad_cache_bazos_car` unique constraint),
negligible next to the LLM call and HTTP scrape it replaces

**Constraints**: Cache read/write failures MUST NOT block advertisement processing (FR-009);
cleanup MUST run automatically without a new schedule, reusing the existing 2-hour `queue` cycle

**Scale/Scope**: Single worker instance, one `Parsed_Advertisements_Cache` row per distinct
(advertisement, car model) pair seen within the retention window — small, personal-project scale

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
|---|---|---|
| I. Test-First Coverage for Parser & Worker Logic (NON-NEGOTIABLE) | New cache read/write/upsert logic in the worker and new cleanup logic MUST ship with unit tests (`tests/unit_tests`) and, since it touches shared persistence in `src/models`, integration coverage (`tests/integration_tests`) extending the existing `test_parser_worker.py` pattern | PASS (planned in Phase 1 / enforced at `/speckit-tasks` + implementation) |
| II. Environment Isolation (Test vs. Production) | All cache access goes through `self.db` obtained via `db_handler.get_db_connection()`, exactly like every other query in `BazosWorker`; no hardcoded connection strings introduced | PASS |
| III. Migration-Only Schema Changes | The new timestamp column is added via a new Alembic revision (`down_revision` = current head `60b4deb1bd84`) | **DEVIATION (user-approved)** — see Complexity Tracking below |
| IV. Respectful External Scraping | Every advertisement's page is still fetched exactly once per cycle via the existing `ad.get_page_text()` call before the cache check runs; the cache changes only whether the LLM is invoked, not scraping cadence or concurrency | PASS |
| V. Secrets & Config Hygiene | The retention period is a plain integer setting (`PARSED_AD_CACHE_RETENTION_DAYS`, default 30) following the existing `Settings` pattern in `src/settings/settings.py`; no secret material involved | PASS |

One violation, explicitly approved by the user during implementation — see Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-parsed-ad-cache/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

No `contracts/` directory: this feature has no external interface (no new API endpoint, CLI
command, or public library surface) — it only changes internal behavior of the `queue` service's
worker and its recurring cycle.

### Source Code (repository root)

```text
src/
├── models/
│   └── models.py                     # ParsedAdvertisementCache: add cached_at column
└── settings/
    └── settings.py                   # add PARSED_AD_CACHE_RETENTION_DAYS setting

alembic/versions/
└── <new_revision>_add_cached_at_to_parsed_advertisement_cache.py

queue_svc/
├── main.py                           # run_cycle(): add cache-cleanup step after _run_worker()
└── worker/
    └── bazos_worker.py               # _process_row_in_queue: cache lookup before LLM call,
                                       # cache write after LLM call

tests/
├── unit_tests/
│   └── worker/                       # new: cache lookup/write/upsert + cleanup unit tests
└── integration_tests/
    └── queue_svc/
        └── test_parser_worker.py     # extend: seed Parsed_Advertisements_Cache rows,
                                       # assert LLM is/isn't called
```

**Structure Decision**: Single existing project (Option 1). This is a targeted change inside the
already-established `src/`, `queue_svc/`, `tests/` layout — no new service, package, or directory
tree is introduced.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|---------------------------------------|
| Editing already-created migration `60b4deb1bd84_add_parsed_advertisement_cache.py` (Constitution Principle III) | While implementing T004, verifying `ENV=test uv run alembic upgrade head` revealed this pre-existing migration hardcodes `postgresql.JSONB` for `parsed_result` with no SQLite branch, so it fails outright on the SQLite test database — unrelated to the `cached_at` column this feature adds. `54e2c7c7af01_initial_schema.py` already established a dialect-aware pattern (`_json_type()`/`_created_at_default()`, branching on `op.get_context().dialect.name`) for exactly this situation; the later migration simply didn't follow it. The user was asked and explicitly chose to fix it inline as part of this feature. | Leaving it broken would mean the new `9b04abf82c79` migration could never be verified end-to-end on SQLite (it depends on `60b4deb1bd84` succeeding first), and the project's own documented dev workflow (`ENV=test uv run alembic upgrade head`, per `boring_readme_for_devs.md`) would stay broken for this table. The fix only changes the SQLite-side type (`JSON` instead of failing to render `JSONB`); Postgres still gets `JSONB` exactly as before — no behavioral change for production. |

The fix: `60b4deb1bd84` now derives its `parsed_result` column type from a local `_json_type()`
helper (mirroring `54e2c7c7af01`'s pattern) instead of an unconditional `postgresql.JSONB(...)`.
