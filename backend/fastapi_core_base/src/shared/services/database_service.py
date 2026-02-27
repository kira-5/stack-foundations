import inspect
import re
from typing import Literal

import polars as pl

from src.shared.configuration.config import env_config_manager
from src.shared.db.core.connection_manager import PostgresConnection
from src.shared.db.execution_lanes import (
    AnalyticalExecutor,
    BatchExecutor,
    BulkExecutor,
    TransactionalExecutor,
)
from src.shared.logging import get_logger

logger = get_logger(name="database_service")


# Cache separator string to avoid repeated string multiplication
_QUERY_LOG_SEPARATOR = "─" * 75


def get_caller_function_name() -> str:
    """Get the name of the function that called execute_*_query.

    Optimized to minimize stack traversal overhead by limiting frame
    access.

    :return: Function name (e.g., "get_user_by_email") or "unknown" if
        not found
    """
    try:
        # Get the call stack (minimal traversal)
        # Frame 0: current function (get_caller_function_name)
        # Frame 1: execute_transactional_query (or similar)
        # Frame 2: caller of execute_transactional_query (what we want)
        frame = inspect.currentframe()
        if frame and frame.f_back and frame.f_back.f_back:
            caller_frame = frame.f_back.f_back
            function_name = caller_frame.f_code.co_name
            # Only get module name if needed (avoid expensive lookup)
            module_name = caller_frame.f_globals.get("__name__", "")
            if module_name:
                module_name = module_name.split(".")[-1]
                if module_name and module_name != function_name:
                    return f"{module_name}.{function_name}"
            return function_name
    except Exception:
        pass
    return "unknown"


def extract_query_source_from_sql(query: str) -> str:
    """Auto-detect query name from SQL query (fallback).

    Tries to extract table name from SQL patterns.

    :param query: SQL query string
    :return: Detected query name or operation type
    """
    query_upper = query.strip().upper()

    # Extract table name from common patterns
    patterns = [
        (r"FROM\s+([a-zA-Z_][a-zA-Z0-9_.]*)", "SELECT"),  # SELECT ... FROM table
        (r"INTO\s+([a-zA-Z_][a-zA-Z0-9_.]*)", "INSERT"),  # INSERT INTO table
        (r"UPDATE\s+([a-zA-Z_][a-zA-Z0-9_.]*)", "UPDATE"),  # UPDATE table
        (r"DELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_.]*)", "DELETE"),  # DELETE FROM table
        (r"CALL\s+([a-zA-Z_][a-zA-Z0-9_.]*)", "CALL"),  # CALL function
    ]

    for pattern, operation in patterns:
        match = re.search(pattern, query_upper, re.IGNORECASE)
        if match:
            table_name = match.group(1).split(".")[-1]  # Get last part (table name)
            return f"{operation} {table_name}"

    # Fallback: extract operation type
    if query_upper.startswith("SELECT"):
        return "SELECT query"
    elif query_upper.startswith("INSERT"):
        return "INSERT query"
    elif query_upper.startswith("UPDATE"):
        return "UPDATE query"
    elif query_upper.startswith("DELETE"):
        return "DELETE query"
    elif query_upper.startswith("CALL"):
        return "CALL query"
    else:
        return "Database query"


class DatabaseService:
    def __init__(self):
        self.transactional_executor = TransactionalExecutor()
        self.analytical_executor = AnalyticalExecutor()
        self.batch_executor = BatchExecutor()
        self.bulk_executor = BulkExecutor()

    async def execute_transactional_query(
        self,
        query: str,
        params: dict | list | None = None,
        db_type: str = "postgres",
        query_source: str | None = None,
        fetch_strategy: Literal["all", "batch", "stream"] | None = None,
        batch_size: int = 1000,
        auto_select_strategy: bool = True,
    ):
        # Auto-detect query source if not provided, needed for both Logging and Watchdog
        if query_source is None:
            caller_name = get_caller_function_name()
            if caller_name != "unknown":
                query_source = caller_name
            else:
                query_source = extract_query_source_from_sql(query)

        query_logging_enabled = env_config_manager.environment_settings.get(
            "QUERY_LOGGING_ENABLED",
            False,
        )

        if query_logging_enabled:

            query_log_format = env_config_manager.environment_settings.get(
                "QUERY_LOG_FORMAT",
                "compact",
            ).lower()

            if query_log_format == "detailed":
                query_log_message = (
                    f"{_QUERY_LOG_SEPARATOR}\n"
                    f"Query Source: {query_source}\n"
                    f"Params: {params}\n"
                    f"Cache: false | Executing from database\n"
                    f"{_QUERY_LOG_SEPARATOR}\n"
                    f"\n"
                    f"{query}\n"
                    f"\n"
                    f"{_QUERY_LOG_SEPARATOR}"
                )
            else:
                query_log_message = (
                    f"Query: {query_source} | Params: {params} | "
                    f"Cache: false | Source: database\n{query}"
                )

            logger.info(query_log_message)

        # Execute the query with params and strategy
        result = await self.transactional_executor.execute_transactional_query(
            query,
            params=params,
            db_type=db_type,
            fetch_strategy=fetch_strategy,
            batch_size=batch_size,
            auto_select_strategy=auto_select_strategy,
            query_source=query_source,
        )

        return result

    async def execute_analytical_query(
        self,
        query: str,
        db_type: Literal["postgres", "duckdb", "federated", "ray", "spark"] | None = None,
        query_source: str | None = None,
    ) -> pl.DataFrame:
        """
        Execute a high-performance analytical query returning a Polars DataFrame.
        Engine is automatically selected via QueryAnalyzer if not provided.
        """
        from src.shared.db.intelligence.query_analyzer import QueryAnalyzer
        from src.shared.db.core.tenant_context import TenantContext

        # 1. Identify query source for logging
        if query_source is None:
            caller_name = get_caller_function_name()
            query_source = caller_name if caller_name != "unknown" else extract_query_source_from_sql(query)

        # 2. Dynamic Routing if db_type is not explicitly passed
        if db_type is None:
            tenant_id = TenantContext.get_tenant_id()
            db_type = QueryAnalyzer.route_query(query, tenant_id=tenant_id)
            logger.info(f"Smart Routing: Decided on '{db_type}' for query '{query_source}'")

        return self.analytical_executor.execute_analytical_query(
            query=query, 
            query_source=query_source,
            db_type=db_type
        )

    async def execute_batch_query(
        self,
        query: str,
        data: list[tuple] | list[list],
        query_source: str | None = None,
    ) -> str:
        """
        High-speed batch insert/update using executemany.
        Best for 1,000 - 10,000 rows.
        """
        if query_source is None:
            query_source = get_caller_function_name()

        logger.info(f"Batch Query: {query_source} | Rows: {len(data)}")
        return await self.batch_executor.execute_batch_query(query, data)

    async def execute_bulk_query(
        self,
        table_name: str,
        columns: list[str],
        data: list[tuple],
        query_source: str | None = None,
    ) -> str:
        """
        Ultra-fast binary COPY protocol.
        Best for 100,000+ rows.
        """
        if query_source is None:
            query_source = get_caller_function_name()

        logger.info(f"Bulk Query: {query_source} | Table: {table_name} | Rows: {len(data)}")
        return await self.bulk_executor.execute_bulk_query(table_name, columns, data)

    async def get_pool_status(self) -> dict:
        """Get the health status of database pools."""
        return await PostgresConnection.get_pool_status()


# Create a single instance of DatabaseService
database_service = DatabaseService()
