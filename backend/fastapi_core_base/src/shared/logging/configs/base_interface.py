import logging
from abc import ABC

from src.shared.logging import constants as logger_constants
from src.shared.logging import settings as logger_settings
from src.shared.logging.handlers.base_interface import LogHandlerInterface


class LogConfigInterface(ABC):
    """Base interface for logger configurations."""

    def __init__(
        self,
        handlers: list[LogHandlerInterface],
        log_level: str | None = None,
        logging_enabled: bool | None = None,
    ):
        """Initialize logger configuration."""

        self.log_level = log_level or logger_settings.get_log_level()
        self.logging_enabled = logging_enabled if logging_enabled is not None else logger_settings.is_logging_enabled()

        # Validate log level before proceeding
        self.validate_log_level(self.log_level)

        self.handlers = handlers
        self._root_logger = logging.getLogger()

    def setup(self) -> None:
        """Set up logging configuration."""

        if not self.logging_enabled:
            self.disable()
            return

        # Configure root logger
        self._root_logger.setLevel(self.log_level.upper())
        self._clear_existing_handlers()
        self.add_handlers()

        # Configure Python's logging defaults
        logging.basicConfig(
            level=self.log_level.upper(),
            handlers=self._root_logger.handlers,
            force=True,
        )

    def add_handlers(self, logger: logging.Logger | None = None) -> None:
        """Add handlers to logger."""

        target_logger = logger or self._root_logger
        for handler in self.handlers:
            handler_instance = handler.get_handler()
            # Convert log level string to numeric level
            log_level_numeric = getattr(logging, self.log_level.upper(), logging.DEBUG)
            handler_instance.setLevel(log_level_numeric)  # Set handler level
            target_logger.addHandler(handler_instance)

    def _clear_existing_handlers(self) -> None:
        """Clear all existing handlers from root logger."""

        for handler in self._root_logger.handlers[:]:
            self._root_logger.removeHandler(handler)

    def disable(self) -> None:
        """Disable logging."""

        self._root_logger.setLevel(logging.CRITICAL)

    def _configure_logger(self, logger_name: str) -> None:
        """Configure a specific logger with root handlers and level."""

        logger = logging.getLogger(logger_name)
        logger.handlers = self._root_logger.handlers
        logger.setLevel(self.log_level.upper())

    @staticmethod
    def validate_log_level(level: str) -> None:
        """Validate that the log level is valid."""

        valid_levels = logger_constants.LOG_LEVEL_UPPERCASE
        if level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level: {level}. Must be one of {valid_levels}",
            )
