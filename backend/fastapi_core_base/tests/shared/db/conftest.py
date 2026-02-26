"""
DB-Layer Test Fixtures (tests/shared/db/conftest.py)
=====================================================
This file extends the root tests/conftest.py with fixtures specific to
testing database internals (TransactionalExecutor, ConnectionManager, etc.).

Root conftest (tests/conftest.py) handles:
  - Markers (unit / integration)
  - db_service, real_db_service, mock_env, api_client, async_api_client, real_api_client

This file adds:
  - mock_env_transactional  : patches env_config_manager inside transactional.py specifically
  - mock_postgres_session   : a bare AsyncMock representing a live Postgres session
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_env_transactional():
    """
    Patches env_config_manager inside transactional.py only.
    Use this when testing TransactionalExecutor directly
    (not through DatabaseService).

    Example:
        async def test_something(mock_env_transactional):
            mock_env_transactional.get_dynamic_setting.return_value = "5min"
    """
    with patch("src.shared.db.execution_lanes.transactional.env_config_manager") as mock_env:
        mock_env.get_dynamic_setting.side_effect = lambda key, default=None: {
            "DB_STMT_TIMEOUT_WRITE": "10min",
            "DB_STMT_TIMEOUT_READ": "30s",
            "DB_LCK_TIMEOUT": "10s",
            "DB_BATCH_SIZE": 1000,
        }.get(key, default)
        yield mock_env


@pytest.fixture
def mock_postgres_session():
    """
    A bare AsyncMock that behaves like an asyncpg or sqlalchemy session.
    Use this when calling executor methods directly.

    Example:
        async def test_fetch(mock_postgres_session):
            mock_postgres_session.fetch.return_value = [{"id": 1}]
    """
    session = AsyncMock()
    session.fetch.return_value = []
    session.execute.return_value = None
    return session
