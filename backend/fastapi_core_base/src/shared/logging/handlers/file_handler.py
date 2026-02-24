import logging
import os
from enum import Enum
from logging.handlers import RotatingFileHandler

from src.shared.logging import ColorFormatter, LogHandlerInterface
from src.shared.logging import constants as logger_constants
from src.shared.logging import settings as logger_settings

# Conditionally import DatadogJSONFormatter for Cloud Run JSON logging
try:
    from src.shared.logging.handlers.datadog_handler import DatadogJSONFormatter
except ImportError:
    DatadogJSONFormatter = None


class FlushingFileHandler(logging.FileHandler):
    """File handler that flushes after every emit to ensure logs are written
    immediately.

    This is critical for Cloud Run where the Datadog sidecar tails log
    files and needs to see logs in real-time.
    """

    def emit(self, record):
        """Emit a record and flush immediately."""
        super().emit(record)
        self.flush()


class FlushingRotatingFileHandler(RotatingFileHandler):
    """Rotating file handler that flushes after every emit to ensure logs are written
    immediately.

    This is critical for Cloud Run where the Datadog sidecar tails log
    files and needs to see logs in real-time.
    """

    def emit(self, record):
        """Emit a record and flush immediately."""
        super().emit(record)
        self.flush()


class FileHandlerType(Enum):
    """Type of file handler to use."""

    SINGLE = "single"
    ROTATING = "rotating"


class FileLogHandler(LogHandlerInterface):
    """Handler for file logging with configurable rotation support."""

    def __init__(
        self,
        log_file: str | None = None,
        handler_type: FileHandlerType | None = None,
        enabled: bool | None = None,
        max_bytes: int | None = None,
        backup_count: int | None = None,
    ):
        """Initialize file handler using settings.toml configuration."""

        # Get settings from config, with optional override
        self.enabled = enabled if enabled is not None else logger_settings.is_file_logging_enabled()

        handler_type_str = handler_type.value if handler_type else logger_settings.get_file_handler_type()
        self.handler_type = FileHandlerType(handler_type_str.lower())

        self.log_file = log_file if log_file else logger_settings.get_log_file_path()

        self.max_bytes = max_bytes if max_bytes else logger_settings.get_log_file_max_bytes()

        self.backup_count = backup_count if backup_count else logger_settings.get_log_file_backup_count()

    def get_handler(self) -> logging.Handler | None:
        """Configure and return appropriate file handler based on configuration."""
        if not self.enabled:
            return logging.NullHandler()

        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(self.log_file)
        os.makedirs(log_dir, exist_ok=True)

        # Debug: Verify directory exists and is writable
        if os.path.exists(log_dir):
            print(f"✅ Log directory exists: {log_dir}")
            # Check if writable
            test_file = os.path.join(log_dir, ".test_write")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                print(f"✅ Log directory is writable: {log_dir}")
            except Exception as e:
                print(f"⚠️ Log directory NOT writable: {log_dir}, error: {e}")
        else:
            print(f"❌ Log directory does NOT exist: {log_dir}")

        print(f"📝 File handler will write logs to: {self.log_file}")

        # Use flushing handlers for Cloud Run to ensure logs are written immediately
        # This is critical for Datadog sidecar file-based log collection
        if self.handler_type == FileHandlerType.ROTATING:
            handler = FlushingRotatingFileHandler(
                self.log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
            )
        else:  # SINGLE
            handler = FlushingFileHandler(self.log_file)

        # Use JSON format for Cloud Run/Datadog (so Datadog can parse and correlate logs)
        # Otherwise use plain text format for local development
        should_use_json = logger_settings.should_use_json_file_format()
        if should_use_json and DatadogJSONFormatter is not None:
            # Use JSON format for Datadog compatibility
            # This ensures logs written to /shared-volume/logs/app.log can be parsed by Datadog
            formatter = DatadogJSONFormatter()
            print(
                f"✅ File handler using DatadogJSONFormatter - JSON logs will be written to {self.log_file}",
            )

            # Debug: Write a test log entry immediately to verify file is writable
            try:
                import json
                from datetime import datetime

                test_log_entry = {
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "level": "INFO",
                    "logger": "file_handler_init",
                    "message": f"File handler initialized - JSON logs will be written to {self.log_file}",
                    "dd.service": os.getenv("DD_SERVICE", "unknown"),
                    "dd.env": os.getenv("DD_ENV", "unknown"),
                }
                # Write directly to file to test (append mode)
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(test_log_entry) + "\n")
                print(f"✅ Test log entry written to {self.log_file}")
            except Exception as e:
                print(f"⚠️ Failed to write test log entry to {self.log_file}: {e}")
        else:
            print(
                f"⚠️ File handler using plain text format - should_use_json={should_use_json}, DatadogJSONFormatter={DatadogJSONFormatter is not None}",
            )
            # Use plain text format for local development
            # Get the base format from settings
            base_format = logger_settings.get_file_format()

            # Add timestamp to file format if it doesn't already include it
            # Check if format already has %(asctime)s
            if "%(asctime)s" not in base_format:
                # Prepend timestamp to the format for file logging only
                file_format = f"%(asctime)s - {base_format}"
            else:
                file_format = base_format

            formatter = ColorFormatter(
                fmt=file_format,
                datefmt=logger_constants.DATE_FORMAT,
                strip_colors=True,  # Strip colors for clean file logs, but keep [UVICORN-ERROR] prefix for errors
            )
        self.set_formatter(handler, formatter)

        # Filter out Datadog internal logs from file logs
        # Uvicorn access logs are controlled by LOG_SERVICE_UVICORN_ENABLED setting
        # (handled by ServiceFilter in service_separated_config)
        def filter_logs(record: logging.LogRecord) -> bool:
            # Exclude ddtrace internal logs from file output
            # They'll still be captured by Datadog handler in JSON format for Datadog
            if record.name.startswith("ddtrace"):
                return False
            # Note: uvicorn.access logs are now controlled by LOG_SERVICE_UVICORN_ENABLED
            # The ServiceFilter will handle filtering based on that setting
            return True

        handler.addFilter(filter_logs)
        return handler

    def enable(self) -> None:
        """Enable the file handler."""
        self.enabled = True

    def disable(self) -> None:
        """Disable the file handler."""
        self.enabled = False
