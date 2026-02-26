import time

import polars as pl

from src.shared.db.engines.adbc import get_adbc_connection_url
from src.shared.db.intelligence.watchdog import PerformanceWatchdog


class AnalyticalExecutor:
    """Executor for high-performance analytical queries using ADBC and Polars."""

    def execute_analytical_query(
        self,
        query: str,
        query_source: str = "unknown",
    ) -> pl.DataFrame:
        """
        Executes a query and returns a Polars DataFrame using the ADBC driver.
        This bypasses the Python object overhead for large datasets.

        Args:
            query (str): The SQL query to execute.
            query_source (str): The origin of the query for Watchdog tracking.

        Returns:
            pl.DataFrame: The resulting data as a Polars DataFrame.
        """
        connection_url = get_adbc_connection_url()

        start_time = time.perf_counter()

        try:
            # pl.read_database uses ADBC under the hood when engine="adbc"
            # and the postgresql:// scheme is used.
            result = pl.read_database(
                query=query,
                connection=connection_url,
                engine="adbc"
            )
            return result
        finally:
            duration = time.perf_counter() - start_time
            PerformanceWatchdog.audit_query(
                query_name=query_source,
                query=query,
                params=None,  # ADBC driver in Polars doesn't explicitly take standard parameterized dicts in this interface natively
                duration=duration
            )
