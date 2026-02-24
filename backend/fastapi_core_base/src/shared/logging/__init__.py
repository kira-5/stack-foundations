# Import formatters first
from src.shared.logging.formatters.base_interface import LogFormatterInterface
from src.shared.logging.formatters.color_formatter import ColorFormatter

# Import handlers
from src.shared.logging.handlers.base_interface import LogHandlerInterface
from src.shared.logging.handlers.file_handler import FileLogHandler
from src.shared.logging.handlers.terminal_handler import TerminalLogHandler

# Import Datadog handler conditionally
try:
    from src.shared.logging.handlers.datadog_handler import DatadogLogHandler
except ImportError:
    DatadogLogHandler = None

# Import configs last since they depend on handlers
from src.shared.logging.configs.base_interface import LogConfigInterface
from src.shared.logging.configs.application_config import ApplicationLoggerConfig
from src.shared.logging.configs.uvicorn_config import UvicornLoggerConfig

try:
    from src.shared.logging.configs.service_separated_config import (
        ServiceSeparatedLoggerConfig,
    )
except ImportError:
    ServiceSeparatedLoggerConfig = None

from src.shared.logging.config_factory import LoggerConfigFactory
from src.shared.logging.logger_factory import LoggerFactory

# Facade imports
import logging
from src.shared.services.logging_service import LoggingService


def setup_logging():
    """Initializer called once in main.py or at startup."""
    LoggingService.configure()


def get_logger(name: str) -> logging.Logger:
    """The standard entry point for all modules to get a logger."""
    return LoggingService.get_logger(name)


__all__ = [
    # Facade
    "LoggingService",
    "setup_logging",
    "get_logger",
    # Interfaces
    "LogConfigInterface",
    "LogFormatterInterface",
    "LogHandlerInterface",
    # Configs
    "ApplicationLoggerConfig",
    "UvicornLoggerConfig",
    "ServiceSeparatedLoggerConfig",
    # Handlers
    "FileLogHandler",
    "TerminalLogHandler",
    "DatadogLogHandler",
    # Formatters
    "ColorFormatter",
    # Config factory
    "LoggerConfigFactory",
    # Logger factory
    "LoggerFactory",
]
