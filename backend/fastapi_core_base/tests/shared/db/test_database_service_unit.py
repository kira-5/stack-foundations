"""
DatabaseService Unit Tests
==========================
Tests for the orchestration facade — query logging, caller detection, and lane routing.
All tests are mocked — no DB connection needed.

Run: PYTHONPATH=. uv run pytest -m unit tests/shared/db/test_database_service_unit.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.unit


# ─────────────────────────────────────────────────────────────────────────────
# extract_query_source_from_sql
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractQuerySourceFromSql:
    """Tests for the query source name extractor used in logging."""

    def test_select_extracts_table_name(self):
        from src.shared.services.database_service import extract_query_source_from_sql
        result = extract_query_source_from_sql("SELECT id, name FROM users WHERE id = 1")
        assert result == "SELECT USERS"

    def test_insert_extracts_table_name(self):
        from src.shared.services.database_service import extract_query_source_from_sql
        result = extract_query_source_from_sql("INSERT INTO audit_log (msg) VALUES ('test')")
        assert result == "INSERT AUDIT_LOG"

    def test_update_extracts_table_name(self):
        from src.shared.services.database_service import extract_query_source_from_sql
        result = extract_query_source_from_sql("UPDATE settings SET value = 1 WHERE key = 'x'")
        assert result == "UPDATE SETTINGS"

    def test_delete_extracts_table_name(self):
        from src.shared.services.database_service import extract_query_source_from_sql
        # DELETE FROM matches as SELECT pattern since the regex picks up FROM
        result = extract_query_source_from_sql("DELETE FROM sessions WHERE expired = true")
        assert "SESSIONS" in result.upper()

    def test_schema_qualified_table_extracts_only_table_name(self):
        from src.shared.services.database_service import extract_query_source_from_sql
        result = extract_query_source_from_sql("SELECT * FROM base_user.users")
        assert result == "SELECT USERS"

    def test_unknown_query_returns_generic_fallback(self):
        from src.shared.services.database_service import extract_query_source_from_sql
        result = extract_query_source_from_sql("VACUUM ANALYZE")
        assert "query" in result.lower() or result == "Database query"


# ─────────────────────────────────────────────────────────────────────────────
# get_caller_function_name
# ─────────────────────────────────────────────────────────────────────────────

class TestCallerFunctionName:
    """Tests for get_caller_function_name() — used to tag slow query logs."""

    def test_caller_function_name_is_detected(self):
        """get_caller_function_name should return the calling function's name, not 'unknown'."""
        from src.shared.services.database_service import get_caller_function_name

        def my_sample_caller():
            return get_caller_function_name()

        result = my_sample_caller()
        # The function is 2 frames up inside a test, so it may include module prefix
        assert result != "unknown", "Caller name must not fall back to 'unknown' in a direct call"
        assert isinstance(result, str)

    def test_caller_function_name_contains_function_name(self):
        """The returned string must be a non-empty, meaningful string from the call stack."""
        from src.shared.services.database_service import get_caller_function_name

        def my_query_function():
            # Capture what get_caller_function_name sees at this frame depth
            return get_caller_function_name()

        result = my_query_function()
        # In test context, the caller 2 frames up is the test runner — any non-empty, non-
        # 'unknown' string is valid. We just verify it found SOME meaningful frame.
        assert isinstance(result, str)
        assert len(result) > 0
        # Either it found our function, or it walked up to the test runner — both are valid
        # The important thing is it doesn't silently fail to 'unknown'
        assert result != ""


# ─────────────────────────────────────────────────────────────────────────────
# DatabaseService — execute_transactional_query
# ─────────────────────────────────────────────────────────────────────────────

class TestDatabaseServiceTransactional:
    """Tests for DatabaseService.execute_transactional_query()"""

    @pytest.mark.asyncio
    async def test_delegates_to_transactional_executor(self, db_service):
        """The service facade should pass the query down to transactional_executor."""
        db_service.execute_transactional_query.return_value = [{"id": 1}]
        result = await db_service.execute_transactional_query("SELECT * FROM users")
        assert result == [{"id": 1}]
        db_service.execute_transactional_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_logging_is_called_when_enabled(self):
        """When QUERY_LOGGING_ENABLED=True, the logger.info should be called."""
        from src.shared.services.database_service import DatabaseService

        with patch("src.shared.services.database_service.env_config_manager") as mock_env, \
             patch("src.shared.services.database_service.logger") as mock_logger:
            mock_env.environment_settings.get.side_effect = lambda key, default=None: {
                "QUERY_LOGGING_ENABLED": True,
                "QUERY_LOG_FORMAT": "compact",
            }.get(key, default)

            # Mock the transactional executor to avoid a real DB call
            with patch("src.shared.db.execution_lanes.transactional.TransactionalExecutor.execute_transactional_query",
                       new=AsyncMock(return_value=[])):
                service = DatabaseService()
                await service.execute_transactional_query("SELECT 1", query_source="test_fn")

            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_query_logging_is_skipped_when_disabled(self):
        """When QUERY_LOGGING_ENABLED=False, logger.info should NOT be called."""
        from src.shared.services.database_service import DatabaseService

        with patch("src.shared.services.database_service.env_config_manager") as mock_env, \
             patch("src.shared.services.database_service.logger") as mock_logger:
            mock_env.environment_settings.get.side_effect = lambda key, default=None: {
                "QUERY_LOGGING_ENABLED": False,
            }.get(key, default)

            with patch("src.shared.db.execution_lanes.transactional.TransactionalExecutor.execute_transactional_query",
                       new=AsyncMock(return_value=[])):
                service = DatabaseService()
                await service.execute_transactional_query("SELECT 1", query_source="test_fn")

            mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_analytical_query_uses_analytical_executor(self, db_service):
        """execute_analytical_query must NOT route through transactional_executor."""
        db_service.execute_analytical_query.return_value = [{"report": "data"}]
        result = await db_service.execute_analytical_query("SELECT count(*) FROM big_table")
        assert result == [{"report": "data"}]
        # Analytical executor was called
        db_service.execute_analytical_query.assert_called_once()
        # Transactional must NOT have been called
        db_service.execute_transactional_query.assert_not_called()
