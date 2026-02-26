import time
from collections.abc import AsyncGenerator
from typing import Literal

from sqlalchemy import text

from src.shared.configuration.config import env_config_manager
from src.shared.db.core.connection_manager import PostgresConnection
from src.shared.db.core.session_guard import handle_streaming_lifetime
from src.shared.db.engines.bigquery import BigQueryConnection
from src.shared.db.intelligence.query_analyzer import QueryAnalyzer
from src.shared.db.intelligence.watchdog import PerformanceWatchdog
from src.shared.logging import get_logger

logger = get_logger(name="transactional_executor")


class TransactionalExecutor:
    """LANE 1: Standard CRUD execution lane (formerly AsyncQueryExecutor)."""

    async def _configure_session_timeouts(
        self,
        session: any,
        driver: str,
        query: str,
    ) -> None:
        """Add session safety by setting automatic statement and lock timeouts."""
        query_type = QueryAnalyzer.detect_query_type(query)
        stmt_timeout = (
            env_config_manager.get_dynamic_setting("DB_STMT_TIMEOUT_WRITE", "10min")
            if query_type == "write"
            else env_config_manager.get_dynamic_setting("DB_STMT_TIMEOUT_READ", "30s")
        )
        lck_timeout = env_config_manager.get_dynamic_setting("DB_LCK_TIMEOUT", "10s")

        timeout_sql = f"SET statement_timeout = '{stmt_timeout}'; SET lock_timeout = '{lck_timeout}';"

        try:
            if driver == "sqlalchemy":
                await session.execute(text(timeout_sql))
            elif driver == "asyncpg":
                await session.execute(timeout_sql)
        except Exception as e:
            logger.warning(f"Failed to set session timeouts: {e}")

    async def _fetch_all(
        self,
        query: str,
        driver: str,
        session: any,
        params: any,
    ) -> list[dict] | dict:
        """Fetch all results at once (Standard strategy)."""
        if driver == "asyncpg":
            if isinstance(params, dict):
                keys = list(params.keys())
                sorted_keys = sorted(keys, key=len, reverse=True)
                for i, key in enumerate(sorted_keys):
                    query = query.replace(f":{key}", f"${i + 1}")
                values = [params[key] for key in sorted_keys]
                result = await session.fetch(query, *values)
            elif isinstance(params, (list, tuple)):
                result = await session.fetch(query, *params)
            else:
                result = await session.fetch(query)
            return [dict(row) for row in result]

        elif driver == "sqlalchemy":
            query_obj = text(query)
            result_proxy = await session.execute(query_obj, params or {})
            if result_proxy.returns_rows:
                rows = result_proxy.fetchall()
                return [dict(row._mapping) for row in rows]
            return {"status": 200, "message": "success"}

        return {"status": "error", "message": f"Unsupported driver: {driver}"}

    async def _fetch_stream(
        self,
        query: str,
        driver: str,
        session: any,
        params: any,
        batch_size: int | None = None,
    ) -> AsyncGenerator[list[dict], None]:
        """Stream results using server-side cursors."""
        if batch_size is None:
            batch_size = int(env_config_manager.get_dynamic_setting("DB_BATCH_SIZE", 1000))

        if driver == "asyncpg":
            if isinstance(params, dict):
                keys = list(params.keys())
                sorted_keys = sorted(keys, key=len, reverse=True)
                for i, key in enumerate(sorted_keys):
                    query = query.replace(f":{key}", f"${i + 1}")
                values = [params[key] for key in sorted_keys]
                async for row in session.cursor(query, *values):
                    yield [dict(row)]
            elif isinstance(params, (list, tuple)):
                async for row in session.cursor(query, *params):
                    yield [dict(row)]
            else:
                async for row in session.cursor(query):
                    yield [dict(row)]
        else:
            async for batch in self._fetch_batch(query, driver, session, params, batch_size):
                yield batch

    async def _fetch_batch(
        self,
        query: str,
        driver: str,
        session: any,
        params: any,
        batch_size: int | None = None,
    ) -> AsyncGenerator[list[dict], None]:
        """Fetch results in batches."""
        if batch_size is None:
            batch_size = int(env_config_manager.get_dynamic_setting("DB_BATCH_SIZE", 1000))

        if driver == "sqlalchemy":
            query_obj = text(query)
            result_proxy = await session.stream(query_obj, params or {})
            async for partition in result_proxy.partitions(batch_size):
                yield [dict(row._mapping) for row in partition]
        else:
            async for row_list in self._fetch_stream(query, driver, session, params, batch_size):
                yield row_list

    async def async_execute_postgres_query(
        self,
        query: str,
        driver: str,
        params: dict | list | None,
        session,
        fetch_strategy: Literal["all", "batch", "stream"] | None = None,
        batch_size: int | None = None,
        **kwargs
    ) -> list[dict] | dict | AsyncGenerator[list[dict], None]:
        """Worker method for Postgres execution. Usually called via execute_transactional_query."""
        if batch_size is None:
            batch_size = int(env_config_manager.get_dynamic_setting("DB_BATCH_SIZE", 1000))

        await self._configure_session_timeouts(session, driver, query)

        strategy = fetch_strategy or "all"
        logger.info(f"Executing query with strategy: {strategy}")

        start_time = time.perf_counter()
        query_source = kwargs.get("query_source", kwargs.get("query_name", "unknown"))

        try:
            if strategy == "all":
                return await self._fetch_all(query, driver, session, params)
            elif strategy == "batch":
                return self._fetch_batch(query, driver, session, params, batch_size)
            elif strategy == "stream":
                return self._fetch_stream(query, driver, session, params, batch_size)

            return await self._fetch_all(query, driver, session, params)
        finally:
            if strategy == "all":
                duration = time.perf_counter() - start_time
                PerformanceWatchdog.audit_query(query_source, query, params, duration)

    async def _stream_with_context(self, func, *args, **kwargs):
        """Internal helper to keep session alive during async iteration."""
        async with PostgresConnection.get_connection() as session:
            kwargs["session"] = session
            async_gen = await func(self, *args, **kwargs)
            async for item in async_gen:
                yield item

    async def async_execute_bq_query(self, query: str):
        """Executes a BigQuery query asynchronously."""
        client = BigQueryConnection.get_big_query_connection()
        query_job = client.query(query)
        rows = query_job.result()
        return [dict(row) for row in rows]

    @handle_streaming_lifetime
    async def execute_transactional_query(
        self,
        query: str,
        params: dict | list | None = None,
        db_type: str = "postgres",
        driver: str = "asyncpg",
        fetch_strategy: Literal["all", "batch", "stream"] | None = None,
        batch_size: int | None = None,
        auto_select_strategy: bool = True,
        session: any = None,  # Provided by @handle_streaming_lifetime
        query_source: str = "unknown",
    ):
        """Unified entry point for transactional queries. Correctly handles pooling & session lifetime."""
        if batch_size is None:
            batch_size = int(env_config_manager.get_dynamic_setting("DB_BATCH_SIZE", 1000))

        if db_type == "postgres":
            return await self.async_execute_postgres_query(
                query=query,
                driver=driver,
                params=params,
                session=session,
                fetch_strategy=fetch_strategy,
                batch_size=batch_size,
                query_source=query_source,
            )
        elif db_type == "bigquery":
            return await self.async_execute_bq_query(query)
        else:
            raise ValueError(f"Unsupported db_type: {db_type}")
