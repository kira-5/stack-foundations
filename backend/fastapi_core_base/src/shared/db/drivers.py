import contextvars
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseDrivers:
    """Class to hold constants for database driver names."""

    ASYNC_PG: str = "asyncpg"
    AIO_PG: str = "aiopg"
    SQL_ALCHEMY: str = "sqlalchemy"


class DatabaseDriverManager:
    """Class to manage the current database driver using context variables."""

    _current_db_driver: contextvars.ContextVar[str | None] = contextvars.ContextVar(
        "current_db_driver",
        default=None,
    )

    @classmethod
    def set_db_driver(cls, driver_name: str) -> None:
        """Set the current database driver in the context variable.

        Args:
            driver_name (str): The name of the database driver to set.
        """
        cls._current_db_driver.set(driver_name)

    @classmethod
    def get_db_driver(cls) -> str | None:
        """Get the current database driver from the context variable.

        Returns:
            Optional[str]: The name of the current database driver, or None if not set.
        """
        return cls._current_db_driver.get()

    @classmethod
    def reset_db_driver(cls, token) -> None:
        """Reset the current database driver to its previous value.

        Args:
            token: The token returned by the context variable when setting the driver.
        """
        cls._current_db_driver.reset(token)

    @classmethod
    def db_driver_context(cls, driver_name: str):
        """Context manager for temporarily setting the database driver."""

        class _DatabaseDriverContext:
            def __init__(self, driver_name: str):
                self.driver_name = driver_name
                self.token = cls._current_db_driver.set(driver_name)

            def __enter__(self):
                return self.driver_name

            def __exit__(self, exc_type, exc_value, traceback):
                cls.reset_db_driver(self.token)

        return _DatabaseDriverContext(driver_name)
