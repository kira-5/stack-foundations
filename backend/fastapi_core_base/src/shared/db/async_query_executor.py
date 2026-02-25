# mport re
# from functools import wraps
# from typing import Optional

# from aiopg import Connection as AiopgConnection
# from app.db.connections import BigQueryConnection, PostgresConnection
# from app.db.drivers import DatabaseDriverManager
# from asyncpg import Connection as AsyncpgConnection
# from sqlalchemy import text
# from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
# from sqlalchemy.ext.asyncio import AsyncSession


# class AsyncQueryExecutor:
#     @staticmethod
#     def handle_db_errors(func):
#         """Decorator for handling database operation errors with explicit session
#         rollback."""

#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             session = kwargs.get("session")
#             if session is None:
#                 raise ValueError(
#                     "The 'session' keyword argument is required for error handling.",
#                 )

#             try:
#                 return await func(*args, **kwargs)
#             except NoResultFound:
#                 return {"status": 404, "message": "No results found."}
#             except IntegrityError as ie:
#                 await session.rollback()
#                 return {"status": 400, "message": f"Integrity error: {str(ie)}"}
#             except SQLAlchemyError as e:
#                 await session.rollback()
#                 return {"status": "error", "message": str(e)}

#         return wrapper

#     @staticmethod
#     def _convert_named_params_to_positional(query: str) -> str:
#         """Convert :param style parameters to $1, $2, etc."""

#         param_names = re.findall(r":([a-zA-Z_]\w*)", query)
#         for i, name in enumerate(param_names, 1):
#             query = query.replace(f":{name}", f"${i}")
#         return query

#     @staticmethod
#     def _convert_named_params_to_pyformat(query: str) -> str:
#         """Convert :param style parameters to %(param)s style."""
#         return re.sub(r":([a-zA-Z_]\w*)", r"%(\1)s", query)

#     @staticmethod
#     def _is_dollar_style_params(query: str) -> bool:
#         """Check if query uses $1, $2 style parameters."""
#         return bool(re.search(r"\$\d+", query))

#     @staticmethod
#     def _is_named_params(query: str) -> bool:
#         """Check if query uses :param style parameters."""
#         return bool(re.search(r":[a-zA-Z_]\w*", query))

#     @staticmethod
#     def _convert_params_to_driver_style(
#         query: str,
#         params: Optional[dict | tuple] = None,
#         target_style: str = "asyncpg",
#     ) -> tuple[str, Optional[dict | tuple]]:
#         """Convert query parameters to the target driver's style."""
#         if params is None:
#             return query, None

#         if target_style == "asyncpg":
#             if isinstance(params, dict):
#                 # Convert named params to positional
#                 param_names = re.findall(
#                     r":([a-zA-Z_]\w*)|%\(([a-zA-Z_]\w*)\)s|\?",
#                     query,
#                 )
#                 param_names = [
#                     name[0] or name[1] for name in param_names if name[0] or name[1]
#                 ]

#                 # Replace all parameter styles with $1, $2, etc.
#                 for i, name in enumerate(param_names, 1):
#                     query = re.sub(rf":{name}|%\({name}\)s|\?", f"${i}", query)

#                 # Convert dict to tuple maintaining order
#                 params = tuple(params[name] for name in param_names)
#             else:
#                 # Convert other styles to $1, $2
#                 query = re.sub(
#                     r"\?|%s",
#                     lambda m, c=iter(range(1, len(params) + 1)): f"${next(c)}",
#                     query,
#                 )

#         elif target_style == "aiopg":
#             if isinstance(params, dict):
#                 # Convert to %(name)s style
#                 query = re.sub(r":([a-zA-Z]\w*)", r"%(\1)s", query)
#             else:
#                 # Convert to %s style
#                 query = re.sub(r"\$\d+|\?", "%s", query)

#         return query, params

#     async def _execute_asyncpg_query(
#         self,
#         query: str,
#         params: Optional[dict | tuple],
#         session,
#     ) -> list[dict]:
#         query, params = self._convert_params_to_driver_style(query, params, "asyncpg")
#         execute_params = ()
#         if params:
#             execute_params = params if isinstance(params, tuple) else (params,)
#         result = await session.fetch(query, *execute_params)
#         return [dict(row) for row in result]

#     async def _execute_aiopg_query(
#         self,
#         query: str,
#         params: Optional[dict | tuple],
#         session,
#     ) -> list[dict] | dict:
#         query, params = self._convert_params_to_driver_style(query, params, "aiopg")
#         async with session.cursor() as cursor:
#             await cursor.execute(query, params)
#             if cursor.description:
#                 columns = [desc.name for desc in cursor.description]
#                 rows = await cursor.fetchall()
#                 return [dict(zip(columns, row)) for row in rows]
#             return {"status": 200, "message": "success"}

#     async def _execute_sqlalchemy_query(
#         self,
#         query: str,
#         params: Optional[dict | tuple],
#         session,
#     ) -> list[dict] | dict:
#         result_proxy = await session.execute(text(query), params)
#         rows = result_proxy.fetchall()
#         if rows:
#             return [row._asdict() for row in rows]
#         return {"status": 200, "message": "success"}

#     async def async_execute_postgres_query(
#         self,
#         query: str,
#         driver: Optional[str],
#         session,
#         params: Optional[dict | tuple] = None,
#     ) -> list[dict] | dict:
#         """Execute a PostgreSQL query asynchronously with parameter binding."""
#         try:
#             if driver == "asyncpg" and isinstance(session, AsyncpgConnection):
#                 return await self._execute_asyncpg_query(query, params, session)
#             elif driver == "aiopg" and isinstance(session, AiopgConnection):
#                 return await self._execute_aiopg_query(query, params, session)
#             elif driver == "sqlalchemy" and isinstance(session, AsyncSession):
#                 return await self._execute_sqlalchemy_query(query, params, session)
#             raise ValueError(f"Unsupported driver: {driver}")
#         except SQLAlchemyError as e:
#             if isinstance(session, AsyncSession):
#                 await session.rollback()
#             return {"status": "error", "message": str(e)}

#     async def async_execute_bq_query(self, query: str):
#         """Executes a BigQuery query asynchronously."""
#         client = (
#             BigQueryConnection.get_big_query_connection()
#         )  # Use your BigQuery connection class
#         query_job = client.query(query)
#         results = query_job.result()
#         return [dict(row) for row in results]

#     async def async_execute_query(
#         self,
#         query: str,
#         db_type: str = "postgres",
#         driver: Optional[str] = None,
#         **kwargs,
#     ):
#         """Executes a query based on the database type, passing session explicitly."""
#         if db_type == "postgres":
#             # If no driver is provided, get it from the context
#             if not driver:
#                 driver = DatabaseDriverManager.get_db_driver()
#             async with PostgresConnection.get_connection() as session:
#                 return await self.async_execute_postgres_query(
#                     query,
#                     driver,
#                     session=session,
#                     **kwargs,
#                 )
#         elif db_type == "bigquery":
#             return await self.async_execute_bq_query(query)
#         else:
#             raise ValueError(f"Unsupported db_type: {db_type}")


from functools import wraps

from aiopg import Connection as AiopgConnection
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
        driver: str,
        *params,
        session,
        session_user_id: int | str | None = "",
    ):
        """Execute a PostgreSQL query asynchronously with explicit session management.

        Args:
            query: SQL query to execute
            driver: Database driver to use (asyncpg, aiopg, sqlalchemy)
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
        elif driver == "aiopg" and isinstance(session, AiopgConnection):
            # elif driver == "aiopg":
            async with session.cursor() as cursor:
                if session_user_id is not None:
                    effective_user_id = session_user_id if session_user_id != "" else um_utils.get_user_id()
                    if effective_user_id is not None and effective_user_id != "":
                        await cursor.execute(
                            "SET app.current_user_code = %s",
                            (str(effective_user_id),),
                        )

                await cursor.execute(query, *params)
                if cursor.description:
                    columns = [desc.name for desc in cursor.description]
                    rows = await cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]

                # reset user_id with RESET
                await cursor.execute("RESET app.current_user_code")

                return {"status": 200, "message": "success"}
                # try:
                #     await cursor.execute(query, *params)
                #     if cursor.description:
                #         columns = [desc.name for desc in cursor.description]
                #         rows = await cursor.fetchall()
                #         return [dict(zip(columns, row)) for row in rows]
                #     return {"status": 200, "message": "success"}
                # except Exception as e:
                #     print(f"Unexpected error during aiopg query execution: {str(e)}")
                #     raise core_exceptions.RuntimeErrorException(str(e))
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
