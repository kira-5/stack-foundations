import functools

from src.shared.db.core.connection_manager import PostgresConnection
from src.shared.db.core.driver_context import DatabaseDriverManager
from src.shared.db.intelligence.query_analyzer import QueryAnalyzer


def handle_streaming_lifetime(func):
    """Decorator to ensure session lifetime is handled for both direct and streamed results."""
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        fetch_strategy = kwargs.get("fetch_strategy")
        auto_select_strategy = kwargs.get("auto_select_strategy", True)
        query = kwargs.get("query")
        driver = kwargs.get("driver")

        if not driver:
            driver = DatabaseDriverManager.get_db_driver()
            kwargs["driver"] = driver

        # Intelligence: Predict strategy if not forced
        if fetch_strategy is None and auto_select_strategy and query:
            fetch_strategy = QueryAnalyzer.auto_select_fetch_strategy(query, driver=driver or "sqlalchemy")
            kwargs["fetch_strategy"] = fetch_strategy

        if fetch_strategy in ["batch", "stream"]:
            # Returns an async generator that keeps the session context alive
            return self._stream_with_context(func, *args, **kwargs)
        else:
            # Standard direct execution
            async with PostgresConnection.get_connection() as session:
                kwargs["session"] = session
                return await func(self, *args, **kwargs)

    return wrapper
