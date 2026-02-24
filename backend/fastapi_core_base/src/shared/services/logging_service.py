import logging
from typing import ClassVar


class LoggingService:
    """Service singleton class for managing logger instances.

    This class implements the singleton pattern to ensure only one
    instance of the logger service exists throughout the application
    lifecycle.
    """

    _instance: ClassVar["LoggingService | None"] = None
    _loggers: dict[str, logging.Logger]

    def __new__(cls) -> "LoggingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loggers = {}  # Store logger instances
        return cls._instance

    @classmethod
    def configure(cls) -> None:
        """Explicitly configure the logging system."""
        try:
            from src.shared.logging.logger_factory import LoggerFactory
            LoggerFactory.create_logger()
        except ImportError:
            pass

    def __init__(self) -> None:
        """Initialize the logger service."""

        # Initialize only once
        if not hasattr(self, "_loggers"):
            self._loggers = {}

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance with the specified name."""

        instance = cls()
        if name not in instance._loggers:
            # Check if the logger already has handlers (configured elsewhere)
            logger = logging.getLogger(name)

            # If not configured, we can try to initialize it using our shared logging logic
            # Note: We import here to avoid circular dependencies if factories import the service
            if not logger.handlers:
                try:
                    from src.shared.logging.logger_factory import LoggerFactory
                    configured_logger = LoggerFactory.create_logger()
                    if configured_logger:
                        logger = configured_logger
                except ImportError:
                    # Fallback to standard logging if factory is unavailable
                    pass

            instance._loggers[name] = logger

        return instance._loggers[name]
