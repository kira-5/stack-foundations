from src.shared.db.core.connection_manager import PostgresConnection


class BulkExecutor:
    """LANE 4: Ultra-fast Binary COPY Ingestion."""

    async def execute_bulk_query(
        self,
        table_name: str,
        columns: list[str],
        data: list[tuple],
    ) -> str:
        """
        Execute the ultra-fast binary COPY protocol.
        Best for 100,000+ rows.

        Args:
            table_name (str): Destination table.
            columns (list[str]): List of column names in order.
            data (list[tuple]): Data rows.

        Returns:
            str: Completion status.
        """
        async with PostgresConnection.get_connection() as conn:
            # This is the fastest method in asyncpg/Postgres
            await conn.copy_records_to_table(
                table_name,
                columns=columns,
                records=data
            )
            return f"Successfully executed bulk query for {len(data)} rows to {table_name} via binary protocol."
