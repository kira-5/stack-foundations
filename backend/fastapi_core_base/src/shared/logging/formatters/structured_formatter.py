import logging

from src.shared.logging import LogFormatterInterface
from src.shared.logging import constants as logger_constants


class StructuredFormatter(LogFormatterInterface):
    """Structured formatter with key=value pairs."""

    def get_formatter(self) -> logging.Formatter:
        return StructuredLoggingFormatter(self._fmt, self.datefmt)


class StructuredLoggingFormatter(logging.Formatter):
    def format(self, record):
        """Format log record with structured key=value pairs."""
        # Format the basic message
        message = super().format(record)

        # Add structured data if available
        extra = getattr(record, "extra", {})
        if extra and isinstance(extra, dict):
            extra_str = logger_constants.STRUCTURED_SEPARATOR.join(f"{k}={v}" for k, v in extra.items())
            message = f"{message}{logger_constants.STRUCTURED_SEPARATOR}{extra_str}"

        return message
