import re
from typing import Literal

try:
    import psutil
except ImportError:
    psutil = None


class QueryAnalyzer:
    """Intelligence layer for analyzing database queries."""

    @staticmethod
    def detect_query_type(query: str) -> Literal["read", "write"]:
        """Detect if query is a read (SELECT) or write (INSERT, UPDATE, DELETE) operation.
        Err on the side of caution: if ANY write keyword is present, treat as write.
        """
        query_lower = query.strip().lower()
        query_clean = re.sub(r"--.*$", "", query_lower, flags=re.MULTILINE)
        query_clean = re.sub(r"/\*.*?\*/", "", query_clean, flags=re.DOTALL)

        # SAFETY FIRST: If the query contains ANY write keywords as isolated words,
        # we treat it as a write.
        write_keywords = ["insert", "update", "delete", "create", "drop", "alter", "truncate", "merge"]

        for kw in write_keywords:
            if re.search(rf"\b{kw}\b", query_clean):
                return "write"

        return "read"

    @staticmethod
    def auto_select_fetch_strategy(
        query: str,
        enable_auto_selection: bool = True,
        driver: str = "sqlalchemy",
    ) -> Literal["all", "batch", "stream"]:
        """Automatically select fetch strategy based on query and system memory."""
        if not enable_auto_selection:
            return "all"

        available_gb = 4.0
        if psutil:
            try:
                mem = psutil.virtual_memory()
                available_gb = mem.available / (1024**3)
            except Exception:
                pass

        query_lower = query.lower()
        large_query_indicators = ["union", "join", "group by"]
        is_potentially_large = any(ind in query_lower for ind in large_query_indicators)

        if available_gb < 0.5:
            return "stream" if driver == "asyncpg" else "batch"
        elif available_gb < 2.0 and is_potentially_large:
            return "batch"

        return "all"
