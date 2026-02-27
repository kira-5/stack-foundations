"""Logger settings to avoid circular imports."""

from typing import Any
from src.shared.logging import constants as logger_constants


def _get_settings() -> Any:
    """Lazy-load settings to avoid circular imports during bootstrap."""
    from src.shared.configuration.config import settings

    return settings


def is_logging_enabled() -> bool:
    """Is logging enabled from environment."""
    return _get_settings().get("LOGGING_ENABLED", True)


def get_logger_type() -> str:
    """Get logger type from environment."""
    return _get_settings().get("LOGGER_TYPE", "application")


def get_log_title() -> str:
    """Get log title from environment."""
    return _get_settings().get("LOG_TITLE", "FastAPI Core Base")


def get_log_level() -> str:
    """Get log level from environment."""
    level = _get_settings().get("LOG_LEVEL", "INFO")
    if level not in logger_constants.LOG_LEVEL_UPPERCASE:
        return logger_constants.DEFAULT_LOG_LEVEL
    return level


def is_terminal_logging_enabled() -> bool:
    """Is terminal logging enabled from environment."""
    return _get_settings().get("TERMINAL_LOGGING_ENABLED", True)


def is_file_logging_enabled() -> bool:
    """Is file logging enabled from environment."""
    return _get_settings().get("FILE_LOGGING_ENABLED", False)


def get_terminal_format() -> str:
    """Get terminal format from environment."""
    format_value = _get_settings().get("LOG_TERMINAL_FORMAT")
    if format_value not in logger_constants.LOG_FORMAT_TYPES:
        return logger_constants.LOG_FORMATS[logger_constants.LOG_FORMAT_SIMPLE_TYPE]
    return logger_constants.LOG_FORMATS[format_value]


def get_file_format() -> str:
    """Get file format from environment."""
    format_value = _get_settings().get("LOG_FILE_FORMAT")
    if format_value not in logger_constants.LOG_FORMAT_TYPES:
        return logger_constants.LOG_FORMATS[logger_constants.LOG_FORMAT_SIMPLE_TYPE]
    return logger_constants.LOG_FORMATS[format_value]


def get_file_handler_type() -> str:
    """Get file handler type from config."""
    return _get_settings().get("FILE_HANDLER_TYPE", "standard")


def _is_cloud_run() -> bool:
    """Check if running on Cloud Run via K_SERVICE or IS_CLOUD_RUN flag."""
    import os

    if os.getenv("K_SERVICE"):
        return True
    return bool(_get_settings().get("IS_CLOUD_RUN", False))


def get_log_file_path() -> str:
    """Get log file path from config."""
    if _is_cloud_run():
        return _get_settings().get("LOG_FILE_PATH", "/shared-volume/logs/app.log")
    return _get_settings().get("LOG_FILE_PATH", "logs/app.log")


def get_log_file_max_bytes() -> int:
    """Get maximum file size in bytes."""
    return _get_settings().get("LOG_FILE_MAX_BYTES", 10485760)  # 10MB


def get_log_file_backup_count() -> int:
    """Get number of backup files to keep."""
    return _get_settings().get("LOG_FILE_BACKUP_COUNT", 5)


def _parse_bool_setting(value: Any) -> bool:
    """Parse a boolean setting value."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


def is_datadog_logging_enabled() -> bool:
    """Check if Datadog logging handler should be enabled."""
    import os

    dd_enabled = _get_settings().get("DATADOG_ENABLED", None)
    if dd_enabled is not None:
        if not _parse_bool_setting(dd_enabled):
            return False

        logs_injection = os.getenv("DD_LOGS_INJECTION") or _get_settings().get(
            "DD_LOGS_INJECTION",
        )
        if logs_injection is not None:
            return _parse_bool_setting(logs_injection)
        return True

    logs_injection = os.getenv("DD_LOGS_INJECTION")
    if logs_injection is not None:
        return _parse_bool_setting(logs_injection)

    return False


def should_use_json_file_format() -> bool:
    """Check if file handler should use JSON format."""
    return _is_cloud_run() or is_datadog_logging_enabled()
