# Data Model: Parsed Advertisement Cache

## Entity: ParsedAdvertisementCache (existing table, one new column)

Represents one previously computed LLM parse result for one advertisement, scoped to one car
model (see `research.md` for why the scope is per car model rather than per car search).

| Field | Type | Notes |
|---|---|---|
| `id` | Integer, PK, autoincrement | Existing — unchanged |
| `bazos_id` | BIGINT, not null | Existing — the advertisement's numeric Bazos listing id (`int(ad.id)`) |
| `car_id` | Integer, FK → `Car_Models.id`, not null | Existing — unchanged |
| `parsed_result` | JSONB (Postgres) / JSON (SQLite), not null | Existing — the raw `CarAdParseResult` dict returned by `LangChainCarAdClient.process`, stored **before** the worker's post-call price override |
| `cached_at` | DateTime (timezone-aware), not null, `server_default=func.now()` | **New** — when this row was last written (inserted or refreshed on upsert); the only column cleanup and cache-hit validity checks read |

**Unique constraint** (existing, unchanged): `uq_parsed_ad_cache_bazos_car` on `(bazos_id, car_id)`
— exactly one live cache row per (advertisement, car model) pair.

**Relationships** (existing, unchanged): `car` → `CarModel` (many-to-one).

### Validation / invariants

- A row is considered a valid cache hit only while `cached_at` is within
  `settings.parsed_ad_cache_retention_days` days of the current time; older rows are treated as a
  miss even before cleanup physically deletes them (guards against a cleanup cycle running late).
- Writing a result for a `(bazos_id, car_id)` pair that already has a row MUST update the existing
  row's `parsed_result` and `cached_at` in place — it must never produce a second row for the same
  pair (enforced by the existing unique constraint; violating it surfaces as an `IntegrityError`
  the write path must avoid by querying first, per `research.md`).
- `cached_at` follows the same convention as `CarSearch.created_at` / `User.created_at`
  (`Column(DateTime(timezone=True), server_default=func.now(), nullable=False)`), so inserts
  without an explicit value are stamped by the database itself; an explicit refresh on update sets
  it to "now" at the ORM layer.

### Schema change

A new Alembic revision adds `cached_at` to `Parsed_Advertisements_Cache`, with
`down_revision` set to the current head (`60b4deb1bd84`, the migration that created the table).
Existing rows (if any exist in a deployed environment) receive the column's `server_default` value
on migration, so no manual backfill is required. No existing migration file is modified, per
Constitution Principle III.

## Configuration: retention period (not a database entity)

`Settings.PARSED_AD_CACHE_RETENTION_DAYS: int = 30`, exposed as
`settings.parsed_ad_cache_retention_days`, overridable via the `PARSED_AD_CACHE_RETENTION_DAYS`
environment variable / `.env` entry, following the existing `Settings` field pattern in
`src/settings/settings.py`. Used by both the cache-hit validity check above and by the cleanup
step's `DELETE ... WHERE cached_at < now() - retention` condition.

## No other entities change

`CarModel`, `CarSearch`, `AdQueue`, `User`, and `CarAdParseResult` (the LLM's `TypedDict` return
shape) are read but not modified by this feature.
