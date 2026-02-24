import logging

from src.shared.logging import LogConfigInterface, LogHandlerInterface
from src.shared.logging import constants as logger_constants


class UvicornLoggerConfig(LogConfigInterface):
    """Uvicorn-specific logger configuration."""

    def __init__(
        self,
        handlers: list[LogHandlerInterface],
        log_level: str | None = None,
        logging_enabled: bool | None = None,
    ):
        """Initialize Uvicorn logger configuration."""

        super().__init__(handlers, log_level, logging_enabled)
        self.uvicorn_loggers = [
            logger_constants.LOGGER_UVICORN,
            logger_constants.LOGGER_UVICORN_ACCESS,
            logger_constants.LOGGER_UVICORN_ERROR,
        ]

    def setup(self) -> None:
        """Setup the logger configuration."""

        # Configure the root logger first
        self._root_logger.setLevel(self.log_level.upper())

        # Clear any existing handlers
        self._root_logger.handlers.clear()

        if self.logging_enabled:
            # Add handlers to root logger for application logs
            # self.add_handlers()

            # Disable root logger (application logs)
            self._root_logger.handlers = []
            self._root_logger.propagate = False

            # Configure only Uvicorn loggers
            for logger_name in self.uvicorn_loggers:
                logger = logging.getLogger(logger_name)
                logger.handlers.clear()
                self.add_handlers(logger)
                logger.setLevel(self.log_level.upper())
                logger.propagate = False  # Prevent double-logging for Uvicorn
        else:
            self.disable()

    def _configure_logger(self, logger_name: str) -> None:
        """Configure a specific logger with root handlers and level."""

        logger = logging.getLogger(logger_name)
        logger.handlers = self._root_logger.handlers
        logger.setLevel(self.log_level.upper())
