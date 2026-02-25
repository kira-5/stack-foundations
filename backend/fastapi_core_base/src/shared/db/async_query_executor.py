from functools import wraps

from asyncpg import Connection as AsyncpgConnection
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.user_management import utils as um_utils
from src.shared.db.connections import BigQueryConnection, PostgresConnection
from src.shared.db.drivers import DatabaseDriverManager


class AsyncQueryExecutor:
    @staticmethod
    def handle_db_errors(func):
        """Decorator for handling database operation errors with explicit session
        rollback."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            session = kwargs.get("session")
            if session is None:
                raise ValueError(
                    "The 'session' keyword argument is required for error handling.",
                )

            try:
                return await func(*args, **kwargs)
            except NoResultFound:
                return {"status": 404, "message": "No results found."}
            except IntegrityError as ie:
                await session.rollback()
                return {"status": 400, "message": f"Integrity error: {str(ie)}"}
            except Exception as e:
                await session.rollback()
                return {"status": "error", "message": str(e)}

        return wrapper

    # @handle_db_errors
    async def async_execute_postgres_query(
        self,
        query: str,
        driver: str | None,
        *params,
        session,
        session_user_id: int | str | None = "",
    ):
        """Execute a PostgreSQL query asynchronously with explicit session management.

        Args:
            query: SQL query to execute
            driver: Database driver to use (asyncpg, sqlalchemy)
            *params: Query parameters
            session: Database session
            session_user_id: User ID to set in database session.
                    - "" (empty string, default): Uses UserContextManager.get_user_id()
                    - None: Skips setting user_id entirely
                    - int: Uses the provided user_id
        """
        if driver == "asyncpg" and isinstance(session, AsyncpgConnection):
            try:
                result = await session.fetch(query, *params)
                return [dict(row) for row in result]
            except Exception as e:
                print(f"Unexpected error during asyncpg query execution: {str(e)}")
                raise
        elif driver == "sqlalchemy" and isinstance(session, AsyncSession):
            query = text(query)
            try:
                result_proxy = await session.execute(query, params)
                # Check if the query was a DML operation (INSERT, UPDATE, DELETE)
                if result_proxy.returns_rows:
                    rows = result_proxy.fetchall()
                    return [dict(row._mapping) for row in rows]
                else:
                    return {"status": 200, "message": "success"}
            except SQLAlchemyError as e:
                await session.rollback()  # Ensure rollback on error
                print(f"Database error during query execution: {str(e)}")
                raise
            except Exception as e:
                await session.rollback()
                print(f"Unexpected error during query execution: {str(e)}")
                raise

    async def async_execute_bq_query(self, query: str):
        """Executes a BigQuery query asynchronously."""
        client = BigQueryConnection.get_big_query_connection()  # Use your BigQuery connection class
        query_job = client.query(query)
        results = await query_job.result()
        return [dict(row) for row in results]

    async def async_execute_query(
        self,
        query: str,
        db_type: str = "postgres",
        driver: str | None = None,
        session_user_id: int | str | None = "",
        **kwargs,
    ):
        """Executes a query based on the database type, passing session explicitly.

        Args:
            query: SQL query to execute
            db_type: Database type (postgres, bigquery)
            driver: Database driver to use (if None, auto-detected)
            session_user_id: User ID to set in database session.
                    - "" (empty string, default): Uses UserContextManager.get_user_id()
                    - None: Skips setting user_id entirely
                    - int: Uses the provided user_id
            **kwargs: Additional parameters to pass to the query executor
        """
        if db_type == "postgres":
            # If no driver is provided, get it from the context
            if not driver:
                # driver = get_db_driver()
                driver = DatabaseDriverManager.get_db_driver()
            async with PostgresConnection.get_connection() as session:
                return await self.async_execute_postgres_query(
                    query,
                    driver,
                    session=session,
                    session_user_id=session_user_id,
                    **kwargs,
                )
        elif db_type == "bigquery":
            return await self.async_execute_bq_query(query)
        else:
            raise ValueError(f"Unsupported db_type: {db_type}")
