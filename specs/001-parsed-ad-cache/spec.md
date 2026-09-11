# Feature Specification: Parsed Advertisement Cache

**Feature Branch**: `001-parsed-ad-cache`

**Created**: 2026-09-11

**Status**: Draft

**Input**: User description: "мне нужно добавить кэширование результатов парсинга llm объявлений bazos_worker'ом, у меня уже есть заготовленная таблица ParsedAdvertisementCache, добавь в нее добавления результатов парса и удаление старых результатов после определенного времени, например после месяца"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reuse a previously parsed advertisement (Priority: P1)

When the worker encounters an advertisement it has already had the LLM parse before (for the same
car search), it reuses the stored result instead of asking the LLM to parse the same advertisement
again.

**Why this priority**: This is the entire reason to cache: without reuse, adding a cache table has
no observable effect. Reusing prior results is what actually cuts down on repeated, costly LLM
parsing work every time the recurring scraping cycle re-encounters an advertisement.

**Independent Test**: Seed a cached parse result for a given advertisement/car-search combination,
then run the worker against that same advertisement again. Verify the worker produces the same
outcome (valid/invalid match, extracted data) as the cached result and does not issue a new LLM
call for it.

**Acceptance Scenarios**:

1. **Given** an advertisement was already parsed for a car search and its result is still within
   the retention window, **When** the worker processes that same advertisement for that same car
   search again, **Then** the worker uses the stored result and does not call the LLM again.
2. **Given** an advertisement has never been parsed for a given car search, **When** the worker
   processes it, **Then** the worker calls the LLM as it does today (no behavior change).

---

### User Story 2 - Persist a new parse result (Priority: P2)

After the LLM parses an advertisement for a car search, the result is saved so it can be reused
later (per User Story 1).

**Why this priority**: Without saving results, there is nothing to reuse — this is the write-side
counterpart that makes User Story 1 possible on subsequent cycles.

**Independent Test**: Run the worker against an advertisement that has no existing cached result.
After processing, verify a cache entry now exists containing the LLM's parse result for that
advertisement/car-search combination.

**Acceptance Scenarios**:

1. **Given** an advertisement with no existing cache entry for a car search, **When** the LLM
   finishes parsing it, **Then** a new cache entry is created holding that result.
2. **Given** an advertisement whose previous cache entry has expired (see User Story 3), **When**
   the LLM parses it again, **Then** the existing entry is updated with the fresh result rather
   than left duplicated or untouched.

---

### User Story 3 - Automatic expiration of old results (Priority: P3)

Cached parse results that have been sitting around longer than a set retention period (by default,
about a month) are automatically removed, so the cache doesn't accumulate stale data forever.

**Why this priority**: Keeps the cache from growing without bound and avoids indefinitely reusing
very old results; lower priority than P1/P2 because the feature is still useful (just growing)
without it in the short term.

**Independent Test**: Seed a cache entry with a cached-at time older than the retention period and
one within the retention period, run the cleanup, and verify only the expired entry is removed.

**Acceptance Scenarios**:

1. **Given** a cache entry older than the retention period, **When** the periodic cleanup runs,
   **Then** that entry is deleted.
2. **Given** a cache entry within the retention period, **When** the periodic cleanup runs,
   **Then** that entry is left untouched.
3. **Given** no expired entries exist, **When** the periodic cleanup runs, **Then** it completes
   without error and removes nothing.

---

### Edge Cases

- What happens when the same physical advertisement matches two different car searches (different
  car models)? Each advertisement/car-search combination is cached and expires independently.
- What happens when an advertisement's cache entry expired between two processing cycles? It is
  treated as a fresh advertisement: the LLM parses it again and the entry is refreshed.
- What happens if reading from or writing to the cache fails unexpectedly? The worker still
  processes the advertisement via the LLM as a fallback, so cache trouble never blocks the
  existing scraping/notification pipeline.
- What happens when the cleanup runs and the underlying advertisement, its car model, or the
  search itself no longer exists? The cache entry is still removed once it is past its retention
  period, regardless of whether related data still exists.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Before asking the LLM to parse an advertisement for a given car search, the system
  MUST check whether a non-expired cached parse result already exists for that exact advertisement
  and car search.
- **FR-002**: When a non-expired cached result exists, the system MUST use it in place of calling
  the LLM, with no change to how the rest of the worker's matching/notification logic behaves.
- **FR-003**: When no cached result exists, or the existing one has expired, the system MUST call
  the LLM to parse the advertisement, exactly as it does today.
- **FR-004**: After the LLM produces a parse result, the system MUST save that result to the cache
  for future reuse.
- **FR-005**: If a cache entry already exists for that advertisement/car-search combination (e.g.,
  it had expired and was reprocessed), the system MUST replace its stored result rather than create
  a duplicate or fail.
- **FR-006**: The system MUST automatically delete cached results once they are older than a
  retention period, defaulting to 30 days.
- **FR-007**: The removal of expired cached results MUST happen automatically on a recurring basis,
  without requiring a person to trigger it manually.
- **FR-008**: Cached results MUST be scoped per advertisement/car-search combination — the same
  advertisement matched against different car searches is cached and expires independently.
- **FR-009**: A failure to read or write the cache MUST NOT prevent an advertisement from being
  processed; the system falls back to direct LLM parsing for that advertisement.

### Key Entities

- **Parsed Advertisement Cache Entry**: A previously computed LLM parse result for one
  advertisement in the context of one car search/model. Key attributes: which advertisement it is
  for, which car model/search it was parsed against, the structured parse outcome itself, and when
  it was cached (used to determine when it expires). Independent per advertisement/car-search
  combination.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When the same advertisement is re-encountered for the same car search within the
  retention window, zero additional LLM parsing calls are made for it compared to today's
  behavior, where every encounter triggers a new LLM call.
- **SC-002**: Cached results past the retention period (default 30 days) are removed within one
  processing cycle after they expire, with no manual cleanup required.
- **SC-003**: Advertisements that have never been parsed, or whose cached result has expired, are
  parsed and matched with the exact same outcome as before this feature existed.
- **SC-004**: The number of cache entries older than the retention window trends to zero over time
  as cleanup keeps running, instead of growing indefinitely.

## Assumptions

- "Caching" is understood to include reuse: the worker actively skips re-parsing an advertisement
  via the LLM when a valid cached result already exists for that advertisement/car-search pair, not
  just recording results for later inspection.
- The cache key is the combination of advertisement and car model/search, matching how the
  existing `ParsedAdvertisementCache` table is already uniquely constrained.
- Default retention period is 30 days, per the user's own example ("after a month"); this is a
  default, not a hard requirement of exactly one calendar month.
- Reprocessing an advertisement whose cache entry has expired is treated the same as processing it
  for the first time: a fresh LLM call and a refreshed cache entry.
- Expired-entry cleanup is expected to piggyback on the existing recurring processing cycle rather
  than introduce a wholly separate schedule.
- Out of scope: invalidating a cached result because the source advertisement's content changed on
  the listing site before the cache entry's age-based expiration. A cached result is treated as
  valid until it expires by age.
