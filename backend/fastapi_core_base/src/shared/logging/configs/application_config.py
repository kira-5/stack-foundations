import logging

from src.shared.logging import LogConfigInterface


class ApplicationLoggerConfig(LogConfigInterface):
    """Configuration for application logger."""

    def add_handlers(self, logger: logging.Logger | None = None) -> None:
        """Add handlers to the logger."""

        target_logger = logger or self._root_logger
        for handler in self.handlers:
            target_logger.addHandler(handler.get_handler())

    def setup(self) -> None:
        """Setup the logger configuration."""

        # Configure the root logger first
        self._root_logger.setLevel(self.log_level.upper())

        # Suppress DEBUG logs from third-party libraries ONLY if LOG_LEVEL is INFO or higher
        # If LOG_LEVEL is DEBUG, allow third-party DEBUG logs (user wants to see everything)
        log_level_upper = self.log_level.upper()
        if log_level_upper != "DEBUG":
            # These libraries set their own loggers to DEBUG, bypassing root logger level
            # Only suppress them when LOG_LEVEL is INFO/WARNING/ERROR/CRITICAL
            third_party_loggers = [
                "grpc",
                "_cygrpc",
                "urllib3",
                "urllib3.connectionpool",
                "urllib3.util",
                "google.auth",
                "google.auth.transport",
                "google.auth.transport.requests",
                "oauth2client",
                "httpx",
                "httpcore",
            ]

            for logger_name in third_party_loggers:
                third_party_logger = logging.getLogger(logger_name)
                # Set to WARNING to suppress DEBUG/INFO from third-party libs
                # Only show WARNING, ERROR, CRITICAL from these libraries
                third_party_logger.setLevel(logging.WARNING)
        # If LOG_LEVEL is DEBUG, don't suppress - let user see all DEBUG logs including third-party

        # Clear any existing handlers to prevent duplicates
        self._root_logger.handlers.clear()

        # Add handlers if logging is enabled
        if self.logging_enabled:
            self.add_handlers()

    def _configure_logger(self, logger_name: str) -> None:
        """Configure a specific logger with root handlers and level."""

        logger = logging.getLogger(logger_name)
        logger.handlers = self._root_logger.handlers
        logger.setLevel(self.log_level.upper())
