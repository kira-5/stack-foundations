"""
Master Test Configuration (tests/conftest.py)
=============================================
This is the single source of truth for ALL test fixtures.

HOW TO USE:
-----------
When writing a test, you NEVER write mock or DB connection logic.
Just pick a fixture that matches what you need:

  UNIT (no real DB):
    - db_service       → mocked DatabaseService
    - api_client       → FastAPI TestClient with mocked DB

  INTEGRATION (real DB from .secrets.toml):
    - real_db_service  → real DatabaseService
    - real_api_client  → FastAPI TestClient with real DB

RUNNING:
--------
  Unit only (fast):          pytest -m unit
  Integration only (real DB): pytest -m integration --run-integration
  Everything:                 pytest --run-integration
"""

import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that connect to a real database",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: fast test — no real DB, uses mocks")
    config.addinivalue_line("markers", "integration: real DB test — requires --run-integration")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return
    skip = pytest.mark.skip(reason="Pass --run-integration to run this test")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


# =============================================================================
# SHARED MOCK HELPERS
# =============================================================================

def _make_mock_db_service(return_value=None):
    """Create a mocked DatabaseService that returns the given value on all query calls."""
    mock = MagicMock()
    mock.execute_transactional_query = AsyncMock(return_value=return_value or [])
    mock.execute_analytical_query = AsyncMock(return_value=return_value or [])
    mock.execute_batch_query = AsyncMock(return_value=return_value or [])
    mock.execute_bulk_query = AsyncMock(return_value=return_value or [])
    return mock


# =============================================================================
# LAYER 1: DB SERVICE FIXTURES
# Use these when testing standalone functions that call database_service directly
# =============================================================================

@pytest.fixture
def db_service():
    """
    UNIT: A fully mocked DatabaseService.
    All query methods return [] by default. Override in your test if needed.

    Example:
        def test_something(db_service):
            db_service.execute_transactional_query.return_value = [{"id": 1}]
    """
    return _make_mock_db_service()


@pytest.fixture
async def real_db_service():
    """
    INTEGRATION: A real DatabaseService connected to your local/dev Postgres.
    Credentials come from toml_config/.secrets.toml automatically.
    """
    from src.shared.db.core.connection_manager import PostgresConnection
    from src.shared.services.database_service import DatabaseService

    PostgresConnection.initialize(database_driver="asyncpg")
    service = DatabaseService()
    yield service
    await PostgresConnection.close()


# =============================================================================
# LAYER 2: ENV CONFIG FIXTURE
# Use this when testing code that reads dynamic settings (timeouts, thresholds)
# =============================================================================

@pytest.fixture
def mock_env(settings: dict | None = None):
    """
    UNIT: Mocked env_config_manager with sensible defaults.
    Pass a dict to override specific values.

    Example:
        def test_timeout(mock_env):
            mock_env.get_dynamic_setting.return_value = "5min"
    """
    defaults = {
        "DB_STMT_TIMEOUT_WRITE": "10min",
        "DB_STMT_TIMEOUT_READ": "30s",
        "DB_LCK_TIMEOUT": "10s",
        "DB_BATCH_SIZE": 1000,
        "WATCHDOG_THRESHOLD_SECONDS": 2.0,
        "WATCHDOG_DEBOUNCE_SECONDS": 300,
        "QUERY_LOGGING_ENABLED": False,
    }
    if settings:
        defaults.update(settings)

    with patch("src.shared.configuration.config.env_config_manager") as mock:
        mock.get_dynamic_setting.side_effect = lambda key, default=None: defaults.get(key, default)
        mock.environment_settings.get.side_effect = lambda key, default=None: defaults.get(key, default)
        yield mock


# =============================================================================
# LAYER 3: FASTAPI TEST CLIENT FIXTURES
# Use these when testing HTTP routes / API endpoints
# =============================================================================

@asynccontextmanager
async def _null_lifespan(_app):
    """No-op lifespan for unit tests: skips startup_event (GCP, Redis, WebSocket)."""
    yield


@pytest.fixture
def api_client(db_service):
    """
    UNIT: A synchronous FastAPI TestClient with a fully mocked DB.
    Lifespan is replaced with a no-op so no external services are contacted.

    Example:
        def test_health_check(api_client):
            response = api_client.get("/api/v1/health")
            assert response.status_code == 200
    """
    from fastapi.testclient import TestClient
    from src.app.main import app
    from src.shared.middleware.database import DatabaseSessionMiddleware
    from src.shared.middleware.maintenance import MaintenanceMiddleware
    from src.shared.services.database_service import database_service

    # Swap lifespan → no-op so startup_event (GCP/Redis/WS) never fires
    app.router.lifespan_context = _null_lifespan

    # Remove DatabaseSessionMiddleware and MaintenanceMiddleware for unit tests
    middlewares_to_remove = [DatabaseSessionMiddleware, MaintenanceMiddleware]
    if any(m.cls in middlewares_to_remove for m in app.user_middleware):
        app.user_middleware = [m for m in app.user_middleware if m.cls not in middlewares_to_remove]
        app.middleware_stack = None  # Rebuild stack on next request

    # Patch the singleton instance methods so all modules see the mock
    with patch.object(database_service, "execute_transactional_query", db_service.execute_transactional_query), \
         patch.object(database_service, "execute_analytical_query", db_service.execute_analytical_query), \
         patch.object(database_service, "execute_batch_query", db_service.execute_batch_query), \
         patch.object(database_service, "execute_bulk_query", db_service.execute_bulk_query):
        
        with TestClient(app, raise_server_exceptions=True) as client:
            yield client


@pytest.fixture
async def async_api_client(db_service):
    """
    UNIT: An async FastAPI TestClient with a fully mocked DB.
    Lifespan is replaced with a no-op so startup_event (GCP/Redis/WebSocket)
    never fires — making tests instant with zero network calls.

    Example:
        async def test_user_access(async_api_client):
            response = await async_api_client.get("/api/v1/user/access")
            assert response.status_code == 200
    """
    from src.app.main import app
    from src.shared.middleware.database import DatabaseSessionMiddleware
    from src.shared.middleware.maintenance import MaintenanceMiddleware
    from src.shared.services.database_service import database_service

    # Swap lifespan → no-op so no external services are contacted
    app.router.lifespan_context = _null_lifespan

    # Remove DatabaseSessionMiddleware and MaintenanceMiddleware for unit tests
    middlewares_to_remove = [DatabaseSessionMiddleware, MaintenanceMiddleware]
    if any(m.cls in middlewares_to_remove for m in app.user_middleware):
        app.user_middleware = [m for m in app.user_middleware if m.cls not in middlewares_to_remove]
        app.middleware_stack = None  # Rebuild stack on next request

    # Patch the singleton instance methods
    with patch.object(database_service, "execute_transactional_query", db_service.execute_transactional_query), \
         patch.object(database_service, "execute_analytical_query", db_service.execute_analytical_query), \
         patch.object(database_service, "execute_batch_query", db_service.execute_batch_query), \
         patch.object(database_service, "execute_bulk_query", db_service.execute_bulk_query):

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client


@pytest.fixture
async def real_api_client(real_db_service):
    """
    INTEGRATION: An async FastAPI TestClient connected to real Postgres.
    All API endpoints will execute against your actual database.

    Example:
        async def test_real_user_access(real_api_client):
            response = await real_api_client.get("/api/v1/user/access?user_code=1")
            assert response.status_code == 200
    """
    with patch("src.shared.services.database_service.database_service", real_db_service):
        from src.app.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client
