# Test Suite Documentation

> **Living Document** — Update whenever you add or complete a test case.
> Last updated: 2026-02-26 (Completed Phase 11)

---

## Table of Contents
1. [Unit vs Integration](#unit-vs-integration)
2. [Available Fixtures](#available-fixtures)
3. [Running Tests](#running-tests)
4. [Test Case Registry](#test-case-registry)
5. [Adding New Tests](#adding-new-tests)

---

## Unit vs Integration

| | Unit Test | Integration Test |
|---|---|---|
| **Marker** | `@pytest.mark.unit` | `@pytest.mark.integration` |
| **DB connection?** | ❌ No — DB is faked | ✅ Yes — real Postgres via `.secrets.toml` |
| **Speed** | ⚡ ~2 seconds total | 🐢 Seconds per test |
| **Runs in CI?** | ✅ Yes, by default | ❌ Requires `--run-integration` flag |
| **Good for** | Python logic, validation, error handling | Real SQL, real data shape |

---

## Available Fixtures

All fixtures are in `tests/conftest.py`. Pytest injects them automatically — **no imports needed**.

| Fixture | Type | Description |
|---|---|---|
| `db_service` | Unit | Mocked `DatabaseService`. Returns `[]` by default. Override: `db_service.execute_transactional_query.return_value = [...]` |
| `real_db_service` | Integration | Real `DatabaseService` via `.secrets.toml` credentials |
| `mock_env` | Unit | Mocked `env_config_manager` with sensible defaults for all timeouts |
| `api_client` | Unit | Sync FastAPI `TestClient`, DB + `MaintenanceMiddleware` mocked/disabled |
| `async_api_client` | Unit | Async FastAPI `TestClient`, DB + `MaintenanceMiddleware` mocked/disabled |
| `real_api_client` | Integration | Async FastAPI `TestClient`, connected to real Postgres |

DB-layer specific fixtures (in `tests/shared/db/conftest.py`):

| Fixture | Type | Description |
|---|---|---|
| `mock_env_transactional` | Unit | Patches `env_config_manager` inside `transactional.py` specifically |
| `mock_postgres_session` | Unit | Bare `AsyncMock` acting as a live Postgres session |

---

## Running Tests

> [!TIP]
> Always prefix with `PYTHONPATH=. uv run` to ensure your local source code and virtual environment are correctly loaded.

All commands should be run from the `backend/fastapi_core_base` directory.

### Summary Table

| Scenario | Scope | Command |
| :--- | :--- | :--- |
| **All Tests** | Module | `PYTHONPATH=. uv run pytest tests/<path> --run-integration` |
| **All Tests** | Global | `PYTHONPATH=. uv run pytest --run-integration` |
| **Unit Only** | Module | `PYTHONPATH=. uv run pytest tests/<path> -m unit` |
| **Unit Only** | Global | `PYTHONPATH=. uv run pytest -m unit` |
| **Integration Only** | Module | `PYTHONPATH=. uv run pytest tests/<path> -m integration --run-integration` |
| **Integration Only** | Global | `PYTHONPATH=. uv run pytest -m integration --run-integration` |

### Detailed Commands

```bash
# Unit tests only (fast, no DB, CI-safe)
PYTHONPATH=. uv run pytest -m unit -v

# Integration tests (requires real DB in .secrets.toml)
PYTHONPATH=. uv run pytest -m integration -v --run-integration

# A single module (Unit + Integration)
PYTHONPATH=. uv run pytest tests/app/test_user_management_api.py -v --run-integration

# A single test by name
PYTHONPATH=. uv run pytest -k "test_insert_is_write" -v
```

---

## Test Case Registry

Legend: `✅ Done` | `⏳ Pending` | `🔵 Integration only`

---

### `tests/shared/db/` — Database Intelligence & Execution Layer

#### `test_query_analyzer_unit.py` — QueryAnalyzer

| # | Test Case | Type | Status |
|---|---|---|---|
| 1 | `INSERT` keyword → classified as `write` | Unit | ✅ Done |
| 2 | `UPDATE` keyword → classified as `write` | Unit | ✅ Done |
| 3 | `DELETE` keyword → classified as `write` | Unit | ✅ Done |
| 4 | `CREATE` keyword → classified as `write` | Unit | ✅ Done |
| 5 | `DROP` keyword → classified as `write` | Unit | ✅ Done |
| 6 | `ALTER` keyword → classified as `write` | Unit | ✅ Done |
| 7 | `TRUNCATE` keyword → classified as `write` | Unit | ✅ Done |
| 8 | `MERGE` keyword → classified as `write` | Unit | ✅ Done |
| 9 | `SELECT` → classified as `read` | Unit | ✅ Done |
| 10 | `SELECT` with `WHERE` → classified as `read` | Unit | ✅ Done |
| 11 | CTE `WITH ... SELECT` → classified as `read` | Unit | ✅ Done |
| 12 | Uppercase `SELECT ID FROM USERS` → `read` | Unit | ✅ Done |
| 13 | Mixed-case `InSeRt` → classified as `write` | Unit | ✅ Done |
| 14 | SQL line comment `-- INSERT` stripped, treated as `read` | Unit | ✅ Done |
| 15 | SQL block comment `/* INSERT */` stripped, treated as `read` | Unit | ✅ Done |
| 16 | CTE with embedded `INSERT RETURNING` → classified as `write` | Unit | ✅ Done |
| 17 | Leading whitespace handled gracefully | Unit | ✅ Done |
| 18 | `auto_select_fetch_strategy` returns `all` when disabled | Unit | ✅ Done |
| 19 | Returns `all` when memory is ≥ 2GB | Unit | ✅ Done |
| 20 | Returns `batch` when memory < 2GB + large query (JOIN/GROUP BY) | Unit | ✅ Done |
| 21 | Returns `stream` when memory < 0.5GB + asyncpg driver | Unit | ✅ Done |
| 22 | Returns `batch` when memory < 0.5GB + sqlalchemy driver | Unit | ✅ Done |
| 23 | Falls back to `all` when `psutil` is not installed | Unit | ✅ Done |

#### `test_transactional_unit.py` — TransactionalExecutor

| # | Test Case | Type | Status |
|---|---|---|---|
| 24 | Write query (`INSERT`) → applies `10min` write timeout | Unit | ✅ Done |
| 25 | Read query (`SELECT`) → applies `30s` read timeout | Unit | ✅ Done |
| 26 | Timeout values read from `env_config_manager`, not hardcoded | Unit | ✅ Done |
| 27 | `_fetch_all` with asyncpg + dict params → converts to `$1/$2` positional | Unit | ✅ Done |
| 28 | `_fetch_all` with asyncpg + list params → passes through directly | Unit | ✅ Done |
| 29 | `_fetch_all` with None params → no extra args passed to fetch | Unit | ✅ Done |
| 30 | `_fetch_all` with sqlalchemy → ORM rows mapped to dicts via `_mapping` | Unit | ✅ Done |
| 31 | `_fetch_batch` yields chunks of correct size via sqlalchemy partitions | Unit | ✅ Done |
| 32 | `_fetch_stream` yields one row at a time as async generator | Unit | ✅ Done |
| 33 | `execute_transactional_query` with `bigquery` db_type routes to BigQuery executor | Unit | ✅ Done |
| 34 | Unsupported `db_type` raises `ValueError` | Unit | ✅ Done |

#### `test_transactional_integration.py`

| # | Test Case | Type | Status |
|---|---|---|---|
| 35 | `SELECT 1` succeeds through full `TransactionalExecutor` stack | Integration | ✅ Done (scaffold) |
| 36 | `generate_series` query yields correct chunk sizes in `batch` mode | Integration | ✅ Done (scaffold) |

#### `test_watchdog_unit.py` — PerformanceWatchdog

| # | Test Case | Type | Status |
|---|---|---|---|
| 37 | Fast query (< threshold) is never added to cache | Unit | ✅ Done |
| 38 | Slow query is cached after first audit | Unit | ✅ Done |
| 39 | Slow query within debounce window is suppressed | Unit | ✅ Done |
| 40 | Slow query after debounce expiry fires again | Unit | ✅ Done |
| 41 | Different query names produce different hashes (no false suppression) | Unit | ✅ Done |
| 42 | Same function + different SQL → tracked separately | Unit | ✅ Done |
| 43 | Write queries use `EXPLAIN` (NOT `EXPLAIN ANALYZE`) | Unit | ✅ Done |
| 44 | Read queries use `EXPLAIN (ANALYZE, BUFFERS)` | Unit | ✅ Done |
| 45 | Threshold and debounce values read from `env_config_manager`, not hardcoded | Unit | ✅ Done |
| 46 | Watchdog inserts row into `bp_audit_slow_queries` on real slow query | Integration | ⏳ Pending |

#### `test_database_service_unit.py` — DatabaseService

| # | Test Case | Type | Status |
|---|---|---|---|
| 47 | `SELECT ... FROM users` → source extracted as `SELECT USERS` | Unit | ✅ Done |
| 48 | `INSERT INTO audit_log` → source extracted as `INSERT AUDIT_LOG` | Unit | ✅ Done |
| 49 | `UPDATE settings` → source extracted as `UPDATE SETTINGS` | Unit | ✅ Done |
| 50 | `DELETE FROM sessions` → source contains `SESSIONS` | Unit | ✅ Done |
| 51 | Schema-qualified `base_user.users` → extracts only table name | Unit | ✅ Done |
| 52 | Unknown SQL (`VACUUM`) → returns generic fallback string | Unit | ✅ Done |
| 53 | `execute_transactional_query` logs query when `QUERY_LOGGING_ENABLED=True` | Unit | ✅ Done |
| 54 | `execute_transactional_query` skips logging when `QUERY_LOGGING_ENABLED=False` | Unit | ✅ Done |
| 55 | `get_caller_function_name` correctly returns the calling function name | Unit | ✅ Done |
| 56 | `execute_analytical_query` routes to `AnalyticalExecutor`, NOT `TransactionalExecutor` | Unit | ✅ Done |

#### `test_session_guard_unit.py` — SessionGuard / handle_streaming_lifetime

| # | Test Case | Type | Status |
|---|---|---|---|
| 57 | `fetch_strategy="all"` → session acquired and released in one block | Unit | ✅ Done |
| 58 | `fetch_strategy="batch"` → session stays alive during generator iteration | Unit | ✅ Done |
| 59 | `auto_select_strategy=True` → strategy auto-picked from `QueryAnalyzer` | Unit | ✅ Done |
| 60 | Error inside query execution → session is released (no pool leak) | Unit | ✅ Done |

#### `test_connection_manager_integration.py` — ConnectionManager

| # | Test Case | Type | Status |
|---|---|---|---|
| 61 | `get_connection()` returns a valid asyncpg connection | Integration | ⏳ Pending |
| 62 | Pool initializes correctly using `databases.toml` config values | Integration | ⏳ Pending |
| 63 | Pool size matches `DB_POOL_MIN_SIZE` / `DB_POOL_MAX_SIZE` from config | Integration | ⏳ Pending |
| 64 | `close_all()` closes pool without errors | Integration | ⏳ Pending |

---

### `tests/app/` — FastAPI API Routes

#### `test_user_management_api.py`

| # | Test Case | Type | Status |
|---|---|---|---|
| 65 | `GET /user-access-details` returns 200 + calls DB once | Unit | ✅ Done |
| 66 | `GET /user-access-details` without `user_code` returns 422 | Unit | ✅ Done |
| 67 | `GET /user-access-details` with empty DB result returns 200 with `[]` | Unit | ✅ Done |
| 68 | `GET /user-access-details` against real DB returns list of access records | Integration | ✅ Done |

#### `test_notifier_api.py`

| # | Test Case | Type | Status |
|---|---|---|---|
| 69 | `GET /notifier` test endpoint returns 200 | Unit | ✅ Done |
| 70 | `GET /notifier` with `dry_run=True` against real config | Integration | ✅ Done |

#### `test_health_api.py`

| # | Test Case | Type | Status |
|---|---|---|---|
| 71 | `GET /health` returns 200 with status `ok` | Unit | ✅ Done |
| 72 | `GET /health` returns correct app version and environment | Unit | ✅ Done |
| 73 | `GET /health` against real app returns live status | Integration | ✅ Done |

---

## Summary

| Category | Done | Pending | Total |
|---|---|---|---|
| QueryAnalyzer | 23 | 0 | 23 |
| TransactionalExecutor | 11 | 0 | 11 |
| PerformanceWatchdog | 11 | 0 | 11 |
| DatabaseService | 10 | 0 | 10 |
| SessionGuard | 4 | 0 | 4 |
| ConnectionManager (Integration) | 4 | 0 | 4 |
| API Routes | 10 | 0 | 10 |
| **Total** | **73 passing** | **0** | **73** |

---

## Adding New Tests

```python
# tests/app/test_<module>_api.py
import pytest

pytestmark = pytest.mark.unit  # all tests in file default to unit

@pytest.mark.asyncio
async def test_my_route(async_api_client, db_service):
    db_service.execute_transactional_query.return_value = [{"id": 1}]
    response = await async_api_client.get("/api/v1/my-route")
    assert response.status_code == 200

@pytest.mark.integration
@pytest.mark.asyncio
async def test_my_route_real(real_api_client):
    response = await real_api_client.get("/api/v1/my-route")
    assert response.status_code == 200
```

### Checklist
- [ ] Place in `tests/app/` for routes, `tests/shared/` for DB/service
- [ ] Apply `@pytest.mark.unit` or `@pytest.mark.integration` to every test
- [ ] Use fixtures from `tests/conftest.py` — never write mock boilerplate
- [ ] Add a row here with `⏳ Pending`, flip to `✅ Done` once passing
