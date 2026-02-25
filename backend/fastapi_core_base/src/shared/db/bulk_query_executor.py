import polars as pl
from src.shared.db.connections import PostgresConnection


class BulkQueryExecutor:
    """Executor for high-performance analytical queries using ADBC and Polars."""

    def execute_analytical_query(
        self,
        query: str,
    ) -> pl.DataFrame:
        """
        Executes a query and returns a Polars DataFrame using the ADBC driver.
        This bypasses the Python object overhead for large datasets.

        Args:
            query (str): The SQL query to execute.

        Returns:
            pl.DataFrame: The resulting data as a Polars DataFrame.
        """
        connection_url = PostgresConnection.get_adbc_connection_url()
        
        # pl.read_database uses ADBC under the hood when engine="adbc"
        # and the postgresql:// scheme is used.
        return pl.read_database(
            query=query,
            connection=connection_url,
            engine="adbc"
        )
