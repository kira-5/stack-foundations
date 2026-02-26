"""
QueryAnalyzer Unit Tests
========================
Tests for the intelligence layer that detects query types and auto-selects fetch strategies.
All tests are pure logic — no DB connection needed.

Run: PYTHONPATH=. uv run pytest -m unit tests/shared/db/test_query_analyzer_unit.py -v
"""

import pytest
from unittest.mock import patch

from src.shared.db.intelligence.query_analyzer import QueryAnalyzer

pytestmark = pytest.mark.unit


# ─────────────────────────────────────────────────────────────────────────────
# detect_query_type
# ─────────────────────────────────────────────────────────────────────────────

class TestDetectQueryType:
    """Tests for QueryAnalyzer.detect_query_type()"""

    # WRITE queries
    def test_insert_is_write(self):
        assert QueryAnalyzer.detect_query_type("INSERT INTO users (name) VALUES ('test')") == "write"

    def test_update_is_write(self):
        assert QueryAnalyzer.detect_query_type("UPDATE users SET name = 'x' WHERE id = 1") == "write"

    def test_delete_is_write(self):
        assert QueryAnalyzer.detect_query_type("DELETE FROM users WHERE id = 1") == "write"

    def test_create_is_write(self):
        assert QueryAnalyzer.detect_query_type("CREATE TABLE test (id INT)") == "write"

    def test_drop_is_write(self):
        assert QueryAnalyzer.detect_query_type("DROP TABLE test") == "write"

    def test_alter_is_write(self):
        assert QueryAnalyzer.detect_query_type("ALTER TABLE users ADD COLUMN age INT") == "write"

    def test_truncate_is_write(self):
        assert QueryAnalyzer.detect_query_type("TRUNCATE TABLE audit_log") == "write"

    def test_merge_is_write(self):
        assert QueryAnalyzer.detect_query_type("MERGE INTO target USING source") == "write"

    # READ queries
    def test_select_is_read(self):
        assert QueryAnalyzer.detect_query_type("SELECT * FROM users") == "read"

    def test_select_with_where_is_read(self):
        assert QueryAnalyzer.detect_query_type("SELECT id, name FROM users WHERE id = 1") == "read"

    def test_cte_read_is_read(self):
        query = "WITH cte AS (SELECT id FROM users) SELECT * FROM cte"
        assert QueryAnalyzer.detect_query_type(query) == "read"

    def test_uppercase_query_is_read(self):
        assert QueryAnalyzer.detect_query_type("SELECT ID FROM USERS") == "read"

    def test_mixed_case_insert_is_write(self):
        assert QueryAnalyzer.detect_query_type("InSeRt INTO users VALUES (1)") == "write"

    # Comment stripping
    def test_sql_line_comment_is_stripped(self):
        query = """
        -- This is a comment about INSERT
        SELECT id FROM users
        """
        assert QueryAnalyzer.detect_query_type(query) == "read"

    def test_sql_block_comment_is_stripped(self):
        query = "/* INSERT users */ SELECT id FROM users"
        assert QueryAnalyzer.detect_query_type(query) == "read"

    # Edge cases
    def test_cte_with_embedded_insert_is_write(self):
        """A SELECT that wraps an INSERT CTE must still be classified as a write."""
        query = "WITH inserted AS (INSERT INTO log (msg) VALUES ('x') RETURNING id) SELECT * FROM inserted"
        assert QueryAnalyzer.detect_query_type(query) == "write"

    def test_leading_whitespace_handled(self):
        assert QueryAnalyzer.detect_query_type("  \n  SELECT 1") == "read"


# ─────────────────────────────────────────────────────────────────────────────
# auto_select_fetch_strategy
# ─────────────────────────────────────────────────────────────────────────────

class TestAutoSelectFetchStrategy:
    """Tests for QueryAnalyzer.auto_select_fetch_strategy()"""

    def test_returns_all_when_auto_selection_disabled(self):
        result = QueryAnalyzer.auto_select_fetch_strategy("SELECT * FROM large_table", enable_auto_selection=False)
        assert result == "all"

    def test_returns_all_when_memory_is_sufficient(self):
        """With plenty of memory and a simple query, strategy should be 'all'."""
        with patch("src.shared.db.intelligence.query_analyzer.psutil") as mock_psutil:
            mock_mem = mock_psutil.virtual_memory.return_value
            mock_mem.available = 8 * (1024 ** 3)  # 8 GB available

            result = QueryAnalyzer.auto_select_fetch_strategy("SELECT id FROM users")
            assert result == "all"

    def test_returns_batch_when_memory_low_and_query_is_large(self):
        """When memory < 2GB and query has JOIN/UNION/GROUP BY, pick batch."""
        with patch("src.shared.db.intelligence.query_analyzer.psutil") as mock_psutil:
            mock_mem = mock_psutil.virtual_memory.return_value
            mock_mem.available = 1 * (1024 ** 3)  # 1 GB available

            result = QueryAnalyzer.auto_select_fetch_strategy(
                "SELECT a.id FROM users a JOIN orders b ON a.id=b.user_id GROUP BY a.id",
                driver="sqlalchemy"
            )
            assert result == "batch"

    def test_returns_stream_when_memory_critically_low_asyncpg(self):
        """When memory < 0.5GB and driver is asyncpg, pick stream."""
        with patch("src.shared.db.intelligence.query_analyzer.psutil") as mock_psutil:
            mock_mem = mock_psutil.virtual_memory.return_value
            mock_mem.available = 0.3 * (1024 ** 3)  # 300 MB available

            result = QueryAnalyzer.auto_select_fetch_strategy(
                "SELECT * FROM huge_table", driver="asyncpg"
            )
            assert result == "stream"

    def test_returns_batch_when_memory_critically_low_sqlalchemy(self):
        """When memory < 0.5GB and driver is sqlalchemy, pick batch (no server-side cursor)."""
        with patch("src.shared.db.intelligence.query_analyzer.psutil") as mock_psutil:
            mock_mem = mock_psutil.virtual_memory.return_value
            mock_mem.available = 0.3 * (1024 ** 3)  # 300 MB

            result = QueryAnalyzer.auto_select_fetch_strategy(
                "SELECT * FROM huge_table", driver="sqlalchemy"
            )
            assert result == "batch"

    def test_fallback_to_all_when_psutil_unavailable(self):
        """If psutil is not installed, strategy defaults to 'all'."""
        with patch("src.shared.db.intelligence.query_analyzer.psutil", None):
            result = QueryAnalyzer.auto_select_fetch_strategy("SELECT * FROM users")
            assert result == "all"
