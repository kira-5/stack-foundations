import logging
import sys

from src.shared.logging import ColorFormatter, LogHandlerInterface
from src.shared.logging import constants as logger_constants
from src.shared.logging import settings as logger_settings


class TerminalLogHandler(LogHandlerInterface):
    """Handler for terminal/stdout logging."""

    def __init__(self, use_stderr: bool = False):
        """Initialize terminal handler."""

        self.stream = sys.stderr if use_stderr else sys.stdout

    def get_handler(self) -> logging.Handler:
        """Configure and return a terminal handler with custom formatting."""
        terminal_handler = logging.StreamHandler(self.stream)
        formatter = ColorFormatter(
            fmt=logger_settings.get_terminal_format(),
            datefmt=logger_constants.DATE_FORMAT,
            strip_colors=False,  # Keep colors for terminal output
        )
        self.set_formatter(terminal_handler, formatter)

        # Filter out Datadog internal logs from terminal
        # Uvicorn access logs are controlled by LOG_SERVICE_UVICORN_ENABLED setting
        # (handled by ServiceFilter in service_separated_config)
        def filter_logs(record: logging.LogRecord) -> bool:
            # Exclude ddtrace internal logs from terminal output
            # They'll still be captured by Datadog handler in JSON format
            if record.name.startswith("ddtrace"):
                return False
            # Note: uvicorn.access logs are now controlled by LOG_SERVICE_UVICORN_ENABLED
            # The ServiceFilter will handle filtering based on that setting
            return True

        terminal_handler.addFilter(filter_logs)
        return terminal_handler
