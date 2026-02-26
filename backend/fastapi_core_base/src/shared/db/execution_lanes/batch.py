from src.shared.db.core.connection_manager import PostgresConnection


class BatchExecutor:
    """LANE 3: High-speed Batch Ingestion using executemany."""

    async def execute_batch_query(
        self,
        query: str,
        data: list[tuple] | list[list],
        driver: str = "asyncpg",
    ) -> str:
        """
        Execute a high-speed batch write using executemany.
        Best for batches of 100-10,000 rows.

        Args:
            query (str): The SQL query with $1, $2 placeholders.
            data (list[tuple]): List of data rows to insert.
            driver (str): Currently only optimized for 'asyncpg'.

        Returns:
            str: Completion status.
        """
        if driver != "asyncpg":
            raise ValueError("execute_batch_query is currently only optimized for 'asyncpg' driver (native).")

        async with PostgresConnection.get_connection() as conn:
            # executemany returns None in asyncpg, but we can verify success
            await conn.executemany(query, data)
            return f"Successfully executed batch query for {len(data)} rows."
