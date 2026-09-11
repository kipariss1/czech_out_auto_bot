# Quickstart: Validating the Parsed Advertisement Cache

Prerequisites: repo checked out on this feature's branch, `uv` installed, dependencies installed
(`uv pip install -e .`). All commands run from the repository root.

## 1. Apply the schema change

```bash
export ENV=test
uv run python -m src.database_utils.init_test_db   # (re)build the local SQLite test DB
uv run alembic upgrade head                         # applies the new cached_at column
```

Expected outcome: no errors; `Parsed_Advertisements_Cache` now has a `cached_at` column (verify
with `sqlite3 src/db/local.db ".schema Parsed_Advertisements_Cache"` if you want to inspect it
directly).

## 2. Confirm a cache hit skips the LLM

Using the existing `build_mock_db` fixture pattern from
`tests/integration_tests/queue_svc/test_parser_worker.py`:

1. Seed `Car_Models`, `Car_Searches`, and one `Parsed_Advertisements_Cache` row whose `bazos_id`
   matches a fixture advertisement's id and whose `car_id` matches the seeded car model.
2. Build a `BazosWorker` with `worker.llm` replaced by `Mock(process=Mock())` (as the existing
   integration test already does).
3. Run `asyncio.run(worker.process_queue())` against a queue containing that same advertisement.
4. Assert `worker.llm.process.assert_not_called()` and that the notification/matching logic ran
   using the seeded `parsed_result` — i.e. behavior is identical to what a fresh LLM call would
   have produced for that same result.

Expected outcome: the mocked LLM is never invoked for the cached advertisement; matching and
notification behavior is unchanged from today's uncached path.

## 3. Confirm a cache miss still calls the LLM and writes a new entry

Same setup as above but with no seeded `Parsed_Advertisements_Cache` row for that advertisement.

Expected outcome: `worker.llm.process` **is** called once; after `process_queue()` returns, a
`Parsed_Advertisements_Cache` row now exists for that `(bazos_id, car_id)` pair holding the LLM's
result.

## 4. Confirm expired entries are cleaned up and fresh ones are not

1. Seed two `Parsed_Advertisements_Cache` rows directly with explicit `cached_at` values: one
   older than `settings.parsed_ad_cache_retention_days` days ago, one recent (the existing
   `build_mock_db` fixture's `#ConvertStr2Datetime` tag can express these as ISO datetime strings
   in the seed payload).
2. Invoke the new cleanup step directly (unit test) or via `asyncio.run(run_cycle())`
   (integration test) with `db_handler` pointed at the mock session.
3. Query `Parsed_Advertisements_Cache` afterward.

Expected outcome: the expired row is gone; the recent row is still present, unchanged.

## 5. Full regression pass

```bash
export ENV=test
uv run pytest tests/unit_tests -v
uv run pytest tests/integration_tests -v
```

Expected outcome: all existing tests plus the new cache/cleanup tests pass — no regressions to
existing parser/worker/matching/notification behavior (Constitution Principle I).
