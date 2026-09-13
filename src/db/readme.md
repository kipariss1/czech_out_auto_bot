### Database Data Files

PostgreSQL is used for `ENV=production`, `ENV=local`, and `ENV=test`.
`ENV=test` targets a dedicated, disposable `postgres_test_db` container (`localhost:5433`) — start
it with `uv run start-test-db`, or use `uv run run-local-component-tests` / `uv run run-local-e2e-tests`
to run it as part of a full local test flow.
