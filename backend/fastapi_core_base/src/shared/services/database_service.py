import inspect
import re

from src.shared.configuration.config import env_config_manager
from src.shared.db.async_query_executor import AsyncQueryExecutor
from src.shared.db.drivers import DatabaseDrivers
from src.shared.services.logging_service import LoggingService

logger = LoggingService.get_logger(name="database_service")


# Cache separator string to avoid repeated string multiplication
_QUERY_LOG_SEPARATOR = "─" * 75


def get_caller_function_name() -> str:
    """Get the name of the function that called execute_async_query.

    Optimized to minimize stack traversal overhead by limiting frame
    access.

    :return: Function name (e.g., "get_user_by_email") or "unknown" if
        not found
    """
    try:
        # Get the call stack (minimal traversal)
        # Frame 0: current function (get_caller_function_name)
        # Frame 1: execute_async_query
        # Frame 2: caller of execute_async_query (what we want)
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
        self.executor = AsyncQueryExecutor()

    async def execute_async_query(
        self,
        query: str,
        is_caching_enabled: bool = False,
        cache_key: str = "",
        db_type: str = "postgres",
        is_cache_query: bool = False,
        query_source: str | None = None,
        session_user_id: int | str | None = "",
    ):
        query_logging_enabled = env_config_manager.environment_settings.get(
            "QUERY_LOGGING_ENABLED",
            False,
        )

        if query_logging_enabled:
            # Auto-detect query source if not provided
            # Performance: Only do expensive caller detection if query_source not provided
            if query_source is None:
                caller_name = get_caller_function_name()
                if caller_name != "unknown":
                    query_source = caller_name
                else:
                    # Fallback to SQL parsing (lighter than stack inspection)
                    query_source = extract_query_source_from_sql(query)

            # Get log format from settings (defaults to "compact" if not set)
            query_log_format = env_config_manager.environment_settings.get(
                "QUERY_LOG_FORMAT",
                "compact",
            ).lower()

            # Different log formats based on QUERY_LOG_FORMAT setting
            if query_log_format == "detailed":
                # Detailed format with separators (human-readable)
                query_log_message = (
                    f"{_QUERY_LOG_SEPARATOR}\n"
                    f"Query Source: {query_source}\n"
                    f"Cache: false | Executing from database\n"
                    f"{_QUERY_LOG_SEPARATOR}\n"
                    f"\n"
                    f"{query}\n"
                    f"\n"
                    f"{_QUERY_LOG_SEPARATOR}"
                )
            else:
                # Compact format (minimal overhead, still readable)
                query_log_message = f"Query: {query_source} | Cache: false | Source: database\n" f"{query}"

            # Single log entry - all query info in one [POSTGRES] - INFO: line
            logger.info(query_log_message)

            result = await self.executor.async_execute_query(
                query,
                db_type,
                driver=DatabaseDrivers.AIO_PG,
            )

            return result

        # If not cached, execute the query
        result = await self.executor.async_execute_query(
            query,
            db_type,
            driver=DatabaseDrivers.AIO_PG,
            session_user_id=session_user_id,
        )

        return result


# Create a single instance of DatabaseService
database_service = DatabaseService()
