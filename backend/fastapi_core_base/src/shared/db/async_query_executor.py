import functools
import re
import asyncio
import time
from typing import AsyncGenerator, Literal, Optional, Union

try:
    import psutil
except ImportError:
    psutil = None

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.connections import BigQueryConnection, PostgresConnection
from src.shared.db.drivers import DatabaseDriverManager
from src.shared.services.logging_service import LoggingService

logger = LoggingService.get_logger(name="async_query_executor")


class PerformanceWatchdog:
    """Zero-Block Background Auditor for tracking slow queries."""

    # Simple debounce cache to prevent spamming EXPLAIN on the same query
    _explained_cache: dict[str, float] = {}
    _DEBOUNCE_SECONDS = 300  # 5 minutes

    @classmethod
    def audit_query(
        cls,
        query_name: str,
        query: str,
        params: any,
        duration: float,
        threshold_seconds: float = 2.0,
    ) -> None:
        if duration <= threshold_seconds:
            return

        query_hash = hash(query_name + query)
        current_time = time.time()

        if query_hash in cls._explained_cache:
            if current_time - cls._explained_cache[query_hash] < cls._DEBOUNCE_SECONDS:
                return

        cls._explained_cache[query_hash] = current_time

        # Fire and forget safely depending on sync vs async context
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                cls._run_auto_explain(query_name, query, params, duration)
            )
        except RuntimeError:
            # We are in a purely synchronous thread (no event loop)
            import threading
            threading.Thread(
                target=lambda: asyncio.run(cls._run_auto_explain(query_name, query, params, duration)),
                daemon=True
            ).start()

    @staticmethod
    async def _run_auto_explain(query_name: str, query: str, params: any, duration: float) -> None:
        await asyncio.sleep(0.5)
        try:
            from src.shared.db.connections import PostgresConnection
            
            async with PostgresConnection.get_connection() as conn:
                check_sql = """
                SELECT 1 FROM base_pricing.bp_audit_slow_queries 
                WHERE query_name = $1 AND DATE(created_at) = CURRENT_DATE
                """
                
                insert_sql = """
                INSERT INTO base_pricing.bp_audit_slow_queries (query_name, raw_sql, execution_time_ms, explain_plan)
                VALUES ($1, $2, $3, $4)
                """
                
                if PostgresConnection.database_driver == "asyncpg":
                    
                    already_logged = await conn.fetchval(check_sql, query_name)
                    if already_logged:
                        return
                    
                    # SECURITY: Only use EXPLAIN ANALYZE for reads to avoid double execution of writes
                    # Even if an INSERT contains a SELECT, the presence of 'insert' flags it as a write.
                    query_lower = query.strip().lower()
                    query_clean = re.sub(r"--.*$", "", query_lower, flags=re.MULTILINE)
                    query_clean = re.sub(r"/\*.*?\*/", "", query_clean, flags=re.DOTALL)
                    
                    write_keywords = ["insert", "update", "delete", "create", "drop", "alter", "truncate", "merge"]
                    is_write = any(re.search(rf"\b{kw}\b", query_clean) for kw in write_keywords)
                    
                    if is_write:
                        explain_query = f"EXPLAIN {query}"
                    else:
                        explain_query = f"EXPLAIN (ANALYZE, BUFFERS) {query}"
                    
                    if isinstance(params, dict):
                        keys = list(params.keys())
                        sorted_keys = sorted(keys, key=len, reverse=True)
                        for i, key in enumerate(sorted_keys):
                            explain_query = explain_query.replace(f":{key}", f"${i + 1}")
                        values = [params[key] for key in sorted_keys]
                        plan_rows = await conn.fetch(explain_query, *values)
                    elif isinstance(params, (list, tuple)):
                        plan_rows = await conn.fetch(explain_query, *params)
                    else:
                        plan_rows = await conn.fetch(explain_query)
                        
                    explain_plan = "\n".join(row[0] for row in plan_rows)
                    
                    await conn.execute(insert_sql, query_name, query, duration * 1000, explain_plan)
                    
                    logger.critical(
                        f"\n{'='*50}\n"
                        f"🚨 WATCHDOG ALERT: SLOW QUERY DETECTED ({duration:.2f}s) 🚨\n"
                        f"Query Name: {query_name}\n"
                        f"Plan:\n{explain_plan}\n"
                        f"{'='*50}"
                    )
                elif PostgresConnection.database_driver == "sqlalchemy":
                    logger.critical(f"Slow query detected: {query_name} took {duration:.2f}s")
                
        except Exception as e:
            logger.error(f"Watchdog failed to explain slow query: {e}")


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
            fetch_strategy = self._auto_select_fetch_strategy(query, driver=driver or "sqlalchemy")
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


class AsyncQueryExecutor:
    """Executor for database queries with built-in intelligence and safety."""

    @staticmethod
    def _detect_query_type(query: str) -> Literal["read", "write"]:
        """Detect if query is a read (SELECT) or write (INSERT, UPDATE, DELETE) operation.
        Err on the side of caution: if ANY write keyword is present, treat as write.
        """
        query_lower = query.strip().lower()
        query_clean = re.sub(r"--.*$", "", query_lower, flags=re.MULTILINE)
        query_clean = re.sub(r"/\*.*?\*/", "", query_clean, flags=re.DOTALL)

        # SAFETY FIRST: If the query contains ANY write keywords as isolated words, 
        # we treat it as a write. This easily catches:
        # - "INSERT INTO ... SELECT ..."
        # - "WITH cte AS (SELECT ...) UPDATE ..."
        write_keywords = ["insert", "update", "delete", "create", "drop", "alter", "truncate", "merge"]
        
        for kw in write_keywords:
            if re.search(rf"\b{kw}\b", query_clean):
                return "write"
                
        return "read"

    def _auto_select_fetch_strategy(
        self,
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

    async def _configure_session_timeouts(
        self,
        session: Union[AsyncSession, any],
        driver: str,
        query: str,
    ) -> None:
        """Add session safety by setting automatic statement and lock timeouts."""
        query_type = self._detect_query_type(query)
        stmt_timeout = "10min" if query_type == "write" else "30s"
        lck_timeout = "10s"

        timeout_sql = f"SET statement_timeout = '{stmt_timeout}'; SET lock_timeout = '{lck_timeout}';"

        try:
            if driver == "sqlalchemy" and isinstance(session, AsyncSession):
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
    ) -> Union[list[dict], dict]:
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
        batch_size: int = 1000,
    ) -> AsyncGenerator[list[dict], None]:
        """Stream results using server-side cursors."""
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
        batch_size: int = 1000,
    ) -> AsyncGenerator[list[dict], None]:
        """Fetch results in batches."""
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
        fetch_strategy: Optional[Literal["all", "batch", "stream"]] = None,
        batch_size: int = 1000,
        **kwargs
    ) -> Union[list[dict], dict, AsyncGenerator[list[dict], None]]:
        """Worker method for Postgres execution. Usually called via async_execute_query."""
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
        fetch_strategy: Optional[Literal["all", "batch", "stream"]] = None,
        batch_size: int = 1000,
        auto_select_strategy: bool = True,
        session: any = None,  # Provided by @handle_streaming_lifetime
        query_source: str = "unknown",
    ):
        """Unified entry point for database queries. Correctly handles pooling & session lifetime."""
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
