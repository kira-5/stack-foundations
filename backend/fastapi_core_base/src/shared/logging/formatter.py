import logging

from src.shared.logging import constants as logger_constants


class CustomFormatter(logging.Formatter):
    """Custom formatter that handles both structured and MTP-style formats."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record based on the specified format type."""

        self._add_color_to_levelname(record)

        # If the message is already formatted (MTP style), return as is
        if logger_constants.PIPE_SEPARATOR in str(record.msg):
            return super().format(record)

        # Otherwise, format as structured log
        self._format_structured_log(record)
        return super().format(record)

    def _add_color_to_levelname(self, record: logging.LogRecord) -> None:
        """Add color to the log level name if running in a terminal."""

        if hasattr(record, "levelname"):
            color = logger_constants.LOG_COLORS.get(
                record.levelname,
                logger_constants.LOG_COLORS[logger_constants.LOG_LEVEL_RESET_UPPERCASE],
            )
            reset_color = logger_constants.LOG_COLORS[logger_constants.LOG_LEVEL_RESET_UPPERCASE]
            record.levelname = f"{color}{record.levelname}{reset_color}"

    def _format_structured_log(self, record: logging.LogRecord) -> None:
        """Format the log record as a structured log."""

        extra = getattr(record, "extra", None)
        if extra and isinstance(extra, dict):
            extra_str = logger_constants.PIPE_SEPARATOR.join(
                f"{k}{logger_constants.EQUALS_SEPARATOR}{v}" for k, v in extra.items()
            )
            record.msg = f"{record.msg}{logger_constants.PIPE_SEPARATOR}{extra_str}"
