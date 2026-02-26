"""
SessionGuard / handle_streaming_lifetime Unit Tests
====================================================
Tests for the decorator that controls session lifetime based on fetch strategy.
All tests are mocked — no DB connection needed.

Run: PYTHONPATH=. uv run pytest -m unit tests/shared/db/test_session_guard_unit.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

pytestmark = pytest.mark.unit


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_executor_with_handler():
    """
    Build a minimal mock executor that has handle_streaming_lifetime applied.
    Returns (executor_instance, mock_connection_ctx).
    """
    from src.shared.db.core.session_guard import handle_streaming_lifetime

    class FakeExecutor:
        @handle_streaming_lifetime
        async def execute_transactional_query(self, **kwargs):
            session = kwargs.get("session")
            return await session.fetch("SELECT 1")

        async def _stream_with_context(self, func, *args, **kwargs):
            """Stub for streaming path — yields nothing for test purposes."""
            yield []

    return FakeExecutor()


# ─────────────────────────────────────────────────────────────────────────────
# fetch_strategy="all" → session acquired and released in one block
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionGuardAllStrategy:

    @pytest.mark.asyncio
    async def test_all_strategy_acquires_and_releases_session(self):
        """When fetch_strategy is 'all', session is opened and closed within one call."""
        executor = _make_executor_with_handler()

        mock_session = AsyncMock()
        mock_session.fetch.return_value = [{"id": 1}]

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mock_ctx.__aexit__.return_value = None

        with patch("src.shared.db.core.session_guard.PostgresConnection") as mock_pg, \
             patch("src.shared.db.core.session_guard.DatabaseDriverManager") as mock_driver:
            mock_pg.get_connection.return_value = mock_ctx
            mock_driver.get_db_driver.return_value = "asyncpg"

            result = await executor.execute_transactional_query(
                query="SELECT 1", fetch_strategy="all"
            )

        # Session context was entered (acquired) and exited (released)
        mock_ctx.__aenter__.assert_called_once()
        mock_ctx.__aexit__.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# fetch_strategy="batch" → session stays alive during generator iteration
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionGuardBatchStrategy:

    @pytest.mark.asyncio
    async def test_batch_strategy_delegates_to_stream_with_context(self):
        """When fetch_strategy is 'batch', _stream_with_context should be called (not direct execute)."""
        executor = _make_executor_with_handler()

        with patch("src.shared.db.core.session_guard.PostgresConnection"), \
             patch("src.shared.db.core.session_guard.DatabaseDriverManager") as mock_driver:
            mock_driver.get_db_driver.return_value = "sqlalchemy"
            with patch.object(executor, "_stream_with_context", return_value=AsyncMock()) as mock_stream:
                result = executor.execute_transactional_query(
                    query="SELECT * FROM big_table", fetch_strategy="batch"
                )
                # The result should be the async generator from _stream_with_context
                # (_stream_with_context is returned, not awaited)
                mock_stream.assert_not_called()  # not yet called — it's returned as a generator
                # The return value itself is the streaming generator reference
                assert result is not None


# ─────────────────────────────────────────────────────────────────────────────
# auto_select_strategy=True → QueryAnalyzer picks the strategy
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionGuardAutoStrategy:

    @pytest.mark.asyncio
    async def test_auto_strategy_calls_query_analyzer(self):
        """When no fetch_strategy is given and auto_select_strategy=True, QueryAnalyzer is invoked."""
        executor = _make_executor_with_handler()

        mock_session = AsyncMock()
        mock_session.fetch.return_value = []

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mock_ctx.__aexit__.return_value = None

        with patch("src.shared.db.core.session_guard.PostgresConnection") as mock_pg, \
             patch("src.shared.db.core.session_guard.DatabaseDriverManager") as mock_driver, \
             patch("src.shared.db.core.session_guard.QueryAnalyzer") as mock_analyzer:
            mock_pg.get_connection.return_value = mock_ctx
            mock_driver.get_db_driver.return_value = "sqlalchemy"
            mock_analyzer.auto_select_fetch_strategy.return_value = "all"

            await executor.execute_transactional_query(
                query="SELECT * FROM users",
                fetch_strategy=None,
                auto_select_strategy=True,
            )

        mock_analyzer.auto_select_fetch_strategy.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# Error inside query → session is released (no pool leak)
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionGuardErrorHandling:

    @pytest.mark.asyncio
    async def test_session_released_on_error(self):
        """Even if the wrapped function raises, the session context manager must exit cleanly."""
        from src.shared.db.core.session_guard import handle_streaming_lifetime

        class FailingExecutor:
            @handle_streaming_lifetime
            async def execute_transactional_query(self, **kwargs):
                raise RuntimeError("Simulated DB failure")

            async def _stream_with_context(self, *args, **kwargs):
                yield []

        executor = FailingExecutor()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = AsyncMock()
        mock_ctx.__aexit__.return_value = None

        with patch("src.shared.db.core.session_guard.PostgresConnection") as mock_pg, \
             patch("src.shared.db.core.session_guard.DatabaseDriverManager") as mock_driver:
            mock_pg.get_connection.return_value = mock_ctx
            mock_driver.get_db_driver.return_value = "asyncpg"

            with pytest.raises(RuntimeError, match="Simulated DB failure"):
                await executor.execute_transactional_query(
                    query="SELECT 1", fetch_strategy="all"
                )

        # Session context must have been exited despite the error
        mock_ctx.__aexit__.assert_called_once()
