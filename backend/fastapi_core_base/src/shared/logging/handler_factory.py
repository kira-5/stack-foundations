from src.shared.logging import FileLogHandler, LogHandlerInterface, TerminalLogHandler
from src.shared.logging import constants as logger_constants
from src.shared.logging import settings as logger_settings

# Import Datadog handler conditionally
try:
    from src.shared.logging.handlers.datadog_handler import DatadogLogHandler

    DATADOG_AVAILABLE = True
except ImportError:
    DATADOG_AVAILABLE = False
    DatadogLogHandler = None


class LogHandlerFactory:
    """Factory for creating logger handlers."""

    _handler_map: dict[str, type[LogHandlerInterface]] = {
        logger_constants.HANDLER_FILE: FileLogHandler,
        logger_constants.HANDLER_TERMINAL: TerminalLogHandler,
    }

    # Add Datadog handler if available
    if DATADOG_AVAILABLE:
        _handler_map[logger_constants.HANDLER_DATADOG] = DatadogLogHandler

    @classmethod
    def create_handlers(cls, handler_types: list[str]) -> list[LogHandlerInterface]:
        """Create and return a list of handler instances based on enabled settings."""

        handlers = []
        for handler_type in handler_types:
            # Check if handler is enabled in settings
            if handler_type == logger_constants.HANDLER_FILE:
                if not logger_settings.is_file_logging_enabled():
                    continue
            elif handler_type == logger_constants.HANDLER_TERMINAL:
                if not logger_settings.is_terminal_logging_enabled():
                    continue
            elif handler_type == logger_constants.HANDLER_DATADOG:
                if not logger_settings.is_datadog_logging_enabled():
                    continue
                if not DATADOG_AVAILABLE:
                    continue  # Skip if Datadog handler not available

            handler_class = cls._handler_map.get(handler_type)
            if not handler_class:
                raise ValueError(f"Unsupported handler type: {handler_type}")
            handlers.append(handler_class())
        return handlers
