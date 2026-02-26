from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DatabaseError
from starlette.middleware.base import BaseHTTPMiddleware

from src.shared.db.core.connection_manager import PostgresConnection
from src.shared.db.drivers import DatabaseDriverManager, DatabaseDrivers


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # Get the database driver from the query parameter
        db_driver = request.query_params.get(
            "db_driver",
            DatabaseDrivers.AIO_PG,
        )  # Default to asyncpg

        # Set the database driver for the context variable
        DatabaseDriverManager.set_db_driver(db_driver)

        # Set the database driver for the connection manager
        PostgresConnection.initialize(db_driver)

        # Capture the request body and store it in state
        try:
            body = await request.body()
            request.state.body = body  # Store the body in request state
        except (ValueError, TypeError) as e:
            return JSONResponse({"error": str(e)}, status_code=500)

        try:
            async with PostgresConnection.get_connection() as conn:
                request.state.db = conn
                response = await call_next(request)
                return response
        except (ConnectionError, DatabaseError) as e:
            # Handle database-specific exceptions
            return JSONResponse({"error": str(e)}, status_code=500)
