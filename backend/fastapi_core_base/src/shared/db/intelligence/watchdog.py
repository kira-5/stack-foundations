import asyncio
import re
import time
import typing

from src.shared.configuration.config import env_config_manager
from src.shared.logging import get_logger

logger = get_logger(name="query_watchdog")


class PerformanceWatchdog:
    """Zero-Block Background Auditor for tracking slow queries."""

    # Simple debounce cache to prevent spamming EXPLAIN on the same query
    _explained_cache: dict[int, float] = {}

    @classmethod
    def audit_query(
        cls,
        query_name: str,
        query: str,
        params: typing.Any,
        duration: float,
        threshold_seconds: float | None = None,
    ) -> None:
        if threshold_seconds is None:
            threshold_seconds = float(env_config_manager.get_dynamic_setting("WATCHDOG_THRESHOLD_SECONDS", 2.0))

        if duration <= threshold_seconds:
            return

        query_hash = hash(query_name + query)
        current_time = time.time()
        debounce_seconds = int(env_config_manager.get_dynamic_setting("WATCHDOG_DEBOUNCE_SECONDS", 300))

        if query_hash in cls._explained_cache:
            if current_time - cls._explained_cache[query_hash] < debounce_seconds:
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
    async def _run_auto_explain(query_name: str, query: str, params: typing.Any, duration: float) -> None:
        await asyncio.sleep(0.5)
        try:
            from src.shared.db.core.connection_manager import PostgresConnection

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
                        f"\n{'=' * 50}\n"
                        f"🚨 WATCHDOG ALERT: SLOW QUERY DETECTED ({duration:.2f}s) 🚨\n"
                        f"Query Name: {query_name}\n"
                        f"Plan:\n{explain_plan}\n"
                        f"{'=' * 50}"
                    )
                elif PostgresConnection.database_driver == "sqlalchemy":
                    logger.critical(f"Slow query detected: {query_name} took {duration:.2f}s")

        except Exception as e:
            logger.error(f"Watchdog failed to explain slow query: {e}")
