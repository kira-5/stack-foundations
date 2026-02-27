import re
from typing import Literal
from src.shared.db.constants import Schemas, RouteStrategy

try:
    import psutil
except ImportError:
    psutil = None


class QueryAnalyzer:
    """Intelligence layer for analyzing database queries."""

    @staticmethod
    def detect_query_type(query: str) -> Literal["read", "write"]:
        """Detect if query is a read (SELECT) or write (INSERT, UPDATE, DELETE) operation."""
        query_lower = query.strip().lower()
        query_clean = re.sub(r"--.*$", "", query_lower, flags=re.MULTILINE)
        query_clean = re.sub(r"/\*.*?\*/", "", query_clean, flags=re.DOTALL)

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

    @staticmethod
    def get_query_tables(query: str) -> list[str]:
        """Extract all table names from a SELECT query, preserving schema if present."""
        patterns = [
            r"from\s+([a-z0-9_\.]+)",
            r"join\s+([a-z0-9_\.]+)"
        ]
        tables = []
        query_lower = query.lower()
        for pattern in patterns:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                table = match.group(1)
                if table not in tables:
                    tables.append(table)
        return tables

    @staticmethod
    def route_query(
        query: str, tenant_id: str | None = None
    ) -> Literal["postgres", "duckdb", "federated", "ray", "spark"]:
        """
        Dynamically route the query. DuckDB is the primary analytical engine.
        """
        _ = tenant_id

        # 1. Check for manual hints
        query_lower = query.lower()
        if "/* engine: postgres */" in query_lower:
            return "postgres"
        if "/* engine: ray */" in query_lower:
            return "ray"
        if "/* engine: spark */" in query_lower:
            return "spark"
        if "/* engine: duckdb */" in query_lower:
            return "duckdb"

        # 2. Extract tables
        tables = QueryAnalyzer.get_query_tables(query)
        if not tables:
            return "postgres"

        # 3. Dynamic Engine Discovery
        engines = set()
        tenant_schema = Schemas().TENANT_APP_SCHEMA.lower()
        pg_global_schemas = ["public", "global"]
        pg_global_tables = ["users", "tenants"]

        for table in tables:
            # Case A: Schema-Qualified (Postgres)
            if "." in table:
                schema_name = table.split(".")[0]
                if schema_name == tenant_schema or schema_name in pg_global_schemas:
                    engines.add("postgres")
                else:
                    # External schemas or analytical schemas default to postgres/federated
                    engines.add("postgres")
            
            # Case B: Global Tables (Postgres)
            elif any(gt == table for gt in pg_global_tables):
                engines.add("postgres")

            # Case C: Dynamic Routing via RouteStrategy
            else:
                engine = RouteStrategy.get_engine(table)
                engines.add(engine)

        # 4. Result Selection
        if len(engines) > 1:
            return "federated"
        return list(engines)[0] if engines else "postgres"
