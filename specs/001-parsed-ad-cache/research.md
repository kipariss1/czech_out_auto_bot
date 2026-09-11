# Research: Parsed Advertisement Cache

## Decision: Cache key is (advertisement, car model), not (advertisement, car search)

**Decision**: A cache entry is keyed by `bazos_id` + `car_id` (`CarModel.id`), matching the
existing `ParsedAdvertisementCache` table's unique constraint (`uq_parsed_ad_cache_bazos_car`)
exactly as it already exists. Two different `CarSearch` rows that target the same `CarModel` share
one cache entry.

**Rationale**: `LangChainCarAdClient.process(ad_text, car)` only takes the advertisement text and
the `CarModel` (manufacturer/model) as input — it never sees a search's price/year/mileage/PSC
filters. Those filters are applied afterwards, in `BazosWorker._fits_to_search_criteria`, against
the LLM's already-extracted structured data. So the LLM's output for a given advertisement is
identical no matter which search (with whatever filters) encounters it — only the car model
matters. Keying by car model rather than by search is therefore not just consistent with the
already-built table, it is the more useful and correct scope: a car parsed once for "Škoda
Octavia" is reused across every search for a Škoda Octavia, not just the one search that happened
to see it first.

**Note for spec.md**: `spec.md` describes the key informally as "advertisement/car-search
combination". That description is accurate at the level a non-technical reader needs (the same
advertisement is still evaluated once per relevant car in the system) but this plan resolves the
precise mechanism: scoping is per car *model*, which is a superset-sharing refinement of the
spec's intent, not a contradiction of it — every acceptance scenario and success criterion in
spec.md still holds under this scoping.

**Alternatives considered**: Keying by `(bazos_id, car_search_id)` was rejected — it would require
altering the already-created table's unique constraint (contradicting the user's "I already have a
prepared table" starting point) and would cause redundant LLM calls whenever two searches target
the same car model, with no benefit (search-specific filters never affect the LLM's output).

## Decision: Cache stores the raw LLM result, unaffected by the post-call price override

**Decision**: The cache stores exactly what `LangChainCarAdClient.process()` returns (the
`CarAdParseResult` dict), before `BazosWorker._process_row_in_queue` overwrites
`res["price"] = str(ad.price)` for valid ads. On both a fresh LLM call and a cache hit, that same
price-override line still runs against the freshly scraped `ad.price` before the result is used
for matching/notification.

**Rationale**: `ad.get_page_text()` (which also populates `ad.price`) already runs for every
advertisement in the queue before the per-ad loop starts, regardless of cache hit or miss — so the
current price is always available and always applied the same way. Caching the pre-override result
means a cache hit and a cache miss produce identically-shaped data flowing into the rest of the
method; no special-casing is needed in `_fits_to_search_criteria` or the notification builder.

**Alternatives considered**: Caching the price-overridden result was rejected — it would freeze a
stale scraped price into the cache, silently drifting from the real advertisement's current price
on every subsequent cache hit, which caching-the-raw-LLM-output avoids entirely by always
re-applying the live price.

## Decision: Cache read/write is an upsert via query-then-update, not a dialect-specific `ON CONFLICT`

**Decision**: Before calling the LLM, query `ParsedAdvertisementCache` by
`(bazos_id=int(ad.id), car_id=car.id)`. If a row exists and is not expired, use its
`parsed_result` and skip the LLM call. After a fresh LLM call, query again for that same key: if a
row exists, update its `parsed_result` (and refresh its timestamp); if not, insert a new row.

**Rationale**: The project runs the identical ORM code path against SQLite (`test`) and PostgreSQL
(`local`/`production`) per Constitution Principle II (Environment Isolation). A plain
query-then-update/insert using the ORM works identically on both engines; a native
`INSERT ... ON CONFLICT` would need dialect-specific SQLAlchemy constructs and would only be
justified by a write-throughput concern this feature does not have (one row per advertisement per
worker cycle, not a bulk/concurrent-write path).

**Alternatives considered**: `session.merge()` was considered but rejected — it operates on the
primary key (`id`), not the `(bazos_id, car_id)` unique constraint, so it would not find the
existing row to update and would risk violating the unique constraint on insert.

## Decision: Retention period is a `Settings` field, not a module constant

**Decision**: Add `PARSED_AD_CACHE_RETENTION_DAYS: int = 30` to `Settings`
(`src/settings/settings.py`), exposed via a `parsed_ad_cache_retention_days` property, following
the exact pattern already used for `OLLAMA_MODEL`/`GEMINI_MODEL`/etc. It is overridable via the
`PARSED_AD_CACHE_RETENTION_DAYS` environment variable (or `.env`), consistent with every other
tunable in this project.

**Rationale**: `Settings` is already the single place this project reads environment-driven
configuration through pydantic-settings, validated at startup — matching Constitution Principle V
(Secrets & Config Hygiene: "Configuration MUST be supplied via environment variables and validated
at service startup"). The alternative — a module-level constant in `queue_svc/main.py`, mirroring
`DEFAULT_INTERVAL_SECONDS` — was rejected because the retention period is a cache/domain concern
that the worker's cleanup logic needs directly; routing it through `queue_svc/main.py` first would
only add an indirection with no benefit, and would be the only piece of business configuration
living outside `Settings`.

## Decision: Cleanup runs as a third step in the existing `queue_svc/main.py` cycle

**Decision**: `run_cycle()` becomes `_run_parser()` → `_run_worker()` → `_run_cache_cleanup()`, with
`_run_cache_cleanup()` following the exact same shape as the two existing step functions: open via
its own constructor call, run the deletion, `db_handler.close_db_connection()` in a `finally`, and
log started/finished/elapsed the same way. `run_forever`'s existing try/except-per-cycle and
interval/sleep logic needs no changes.

**Rationale**: The project already has exactly one recurring schedule (the 2-hour `queue` cycle)
and Constitution's Technology & Service Boundaries section describes `queue` as the service
responsible for this kind of periodic background work. Reusing it means zero new
processes/schedulers/cron entries, and cache expiry checked roughly every 2 hours is far more
frequent than the 30-day default retention window requires.

**Alternatives considered**: A separate cron/scheduled task was rejected as unjustified
complexity — nothing about cache cleanup needs a different cadence than the cycle that already
runs, and a second scheduler would be a new moving part for no behavioral benefit.

## Decision: Cache failures are caught and logged at the point of use, falling back to direct LLM processing

**Decision**: The cache lookup before the LLM call, and the cache write after it, are each wrapped
in their own `try`/`except Exception`, logging the exception (mirroring the existing
`logger.exception(...)` style in `BazosWorker.process_queue`'s per-row loop) and continuing as if
the cache had missed. A cleanup failure is likewise caught inside `_run_cache_cleanup()`, logged,
and does not stop `run_forever`'s next scheduled cycle (which already tolerates step failures via
its own outer try/except).

**Rationale**: FR-009 requires that cache trouble never blocks advertisement processing. Catching
at the point of use (rather than around the whole per-ad loop) means a cache failure for one
advertisement does not also skip the LLM call for the *next* advertisement in the same queue row —
narrower exception scope preserves more of the existing per-ad resilience already present in
`_process_row_in_queue`.

## Resolved: no [NEEDS CLARIFICATION] markers remain

All Technical Context fields and design decisions above have concrete answers; nothing in this
feature requires further user input before proceeding to Phase 1.
