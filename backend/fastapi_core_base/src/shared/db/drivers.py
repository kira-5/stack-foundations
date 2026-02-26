"""
Database Driver Management
===========================
Provides a simple enum-like class for driver names and a thread-/coroutine-safe
context variable to store the active driver for the current request.

Used by:
  - startup_event.py  → DatabaseDriverManager.set_db_driver(driver) at startup
  - DatabaseSessionMiddleware → overrides driver per-request from query param
  - ConnectionManager → reads current driver via DatabaseDriverManager.get_db_driver()
"""

import contextvars


class DatabaseDrivers:
    """
    Driver name constants.  Use these instead of raw strings everywhere.
    """
    ASYNC_PG = "asyncpg"   # Low-level asyncpg (raw SQL, fastest)
    AIO_PG = "asyncpg"     # Alias used in legacy code — same as ASYNC_PG
    SQLALCHEMY = "sqlalchemy"  # SQLAlchemy async ORM sessions
    BIGQUERY = "bigquery"  # Google BigQuery driver


# Context variable: isolates the active driver per-request (async-safe)
_db_driver_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "db_driver", default=DatabaseDrivers.ASYNC_PG
)


class DatabaseDriverManager:
    """
    Manages the active database driver for the current execution context.

    Thread-safe and coroutine-safe via Python contextvars — each request
    (or coroutine) sees its own driver without interfering with others.
    """

    @classmethod
    def set_db_driver(cls, driver: str) -> None:
        """Set the active driver for the current context."""
        _db_driver_ctx.set(driver)

    @classmethod
    def get_db_driver(cls) -> str:
        """Return the active driver for the current context (default: asyncpg)."""
        return _db_driver_ctx.get()
