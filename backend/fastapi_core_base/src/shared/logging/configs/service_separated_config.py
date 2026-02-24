"""Service-separated logger configuration with per-service enable/disable and colors."""

import logging

from src.shared.config import settings
from src.shared.logging import LogConfigInterface
from src.shared.logging import constants as logger_constants


def get_service_from_logger_name(logger_name: str) -> str | None:
    """Get service name from logger name.

    Maps logger names to services:
    - redis.* → redis
    - psycopg.*, sqlalchemy.* → postgres
    - urllib3.*, requests.* → requests
    - aiohttp.* → aiohttp
    - grpc.* → grpc
    - jinja2.* → misc
    - uvicorn.*, fastapi → uvicorn
    - src.* → application

    :param logger_name: Logger name (e.g., "redis.client", "src.shared.services.mailer")
    :return: Service name or None if not mapped
    """
    # Check exact matches first
    if logger_name in logger_constants.SERVICE_LOGGER_PATTERNS:
        return logger_constants.SERVICE_LOGGER_PATTERNS[logger_name]

    # Check prefix matches
    for pattern, service in logger_constants.SERVICE_LOGGER_PATTERNS.items():
        if logger_name.startswith(pattern):
            return service

    # Check if it's application code (starts with "src.")
    if logger_name.startswith("src."):
        return logger_constants.SERVICE_APPLICATION

    # Default: misc for unknown loggers
    return logger_constants.SERVICE_MISC


def get_service_enabled_setting(service: str, default: bool = True) -> bool:
    """Get enable/disable setting for a service.

    :param service: Service name (redis, postgres, etc.)
    :param default: Default value if not found
    :return: True if service logging is enabled, False otherwise
    """
    # Map service to config key
    config_key_map = {
        logger_constants.SERVICE_REDIS: logger_constants.LOG_SERVICE_REDIS_ENABLED,
        logger_constants.SERVICE_POSTGRES: logger_constants.LOG_SERVICE_POSTGRES_ENABLED,
        logger_constants.SERVICE_REQUESTS: logger_constants.LOG_SERVICE_REQUESTS_ENABLED,
        logger_constants.SERVICE_AIOHTTP: logger_constants.LOG_SERVICE_AIOHTTP_ENABLED,
        logger_constants.SERVICE_GRPC: logger_constants.LOG_SERVICE_GRPC_ENABLED,
        logger_constants.SERVICE_MISC: logger_constants.LOG_SERVICE_MISC_ENABLED,
        logger_constants.SERVICE_APPLICATION: logger_constants.LOG_SERVICE_APPLICATION_ENABLED,
        logger_constants.SERVICE_UVICORN: logger_constants.LOG_SERVICE_UVICORN_ENABLED,
    }

    config_key = config_key_map.get(service)
    if not config_key:
        return default

    # Get from Dynaconf settings
    try:
        setting_value = settings.get(config_key, default)
        if isinstance(setting_value, bool):
            return setting_value
        if isinstance(setting_value, str):
            return setting_value.lower() in ("true", "1", "yes")
    except Exception:
        return default

    return default


class ServiceFilter(logging.Filter):
    """Filter logs by service enable/disable setting."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter logs - return False if service is disabled."""
        service = get_service_from_logger_name(record.name)

        if service:
            # Add service name and color to record for formatter
            record.service_name = service
            record.service_color = logger_constants.SERVICE_COLORS.get(service, "")
            # Check if service is enabled
            is_enabled = get_service_enabled_setting(service)
            return is_enabled

        # Unknown loggers: allow by default, assign to misc
        record.service_name = logger_constants.SERVICE_MISC
        record.service_color = logger_constants.SERVICE_COLORS.get(
            logger_constants.SERVICE_MISC,
            "",
        )
        is_enabled = get_service_enabled_setting(logger_constants.SERVICE_MISC)
        return is_enabled


class ServiceSeparatedLoggerConfig(LogConfigInterface):
    """Service-separated logger configuration.

    Logs everything but keeps each service separate with:
    - Individual enable/disable per service
    - Different colors per service
    - Service tags in logs
    """

    def setup(self) -> None:
        """Setup service-separated logging configuration."""
        if not self.logging_enabled:
            self.disable()
            return

        # Configure root logger
        # Convert log level string to numeric level
        log_level_numeric = getattr(logging, self.log_level.upper(), logging.DEBUG)

        # Create service filter FIRST (before any logging operations)
        service_filter = ServiceFilter()

        # Use self._root_logger consistently (it's the same as logging.getLogger())
        self._root_logger.handlers.clear()
        self._root_logger.propagate = True
        self._root_logger.setLevel(log_level_numeric)

        # Add filter to root logger BEFORE adding handlers
        self._root_logger.addFilter(service_filter)

        # Add handlers to root logger
        if self.logging_enabled:
            self.add_handlers()  # This adds handlers to self._root_logger

        # Store handlers BEFORE basicConfig (basicConfig might modify the list)
        handlers_list = list(self._root_logger.handlers)

        # Add filter to each handler BEFORE basicConfig
        for handler in handlers_list:
            handler.addFilter(service_filter)

        # Configure Python's logging defaults
        # CRITICAL: Pass handlers as a list, not self._root_logger.handlers (which might be cleared)
        logging.basicConfig(
            level=log_level_numeric,
            handlers=handlers_list,  # Use stored list
            force=True,
        )

        # Re-get root logger after basicConfig (it's the same object, but verify)
        root_logger = logging.getLogger()
        assert root_logger is self._root_logger, "Root logger should be the same object"
        root_logger.propagate = True
        root_logger.setLevel(log_level_numeric)

        # CRITICAL: Re-add filter to root logger after basicConfig
        if service_filter not in root_logger.filters:
            root_logger.addFilter(service_filter)

        # CRITICAL: Ensure filters are on handlers after basicConfig
        # Remove any existing ServiceFilter instances and add fresh one
        for handler in root_logger.handlers:
            # Remove any existing ServiceFilter instances
            handler.filters = [f for f in handler.filters if not isinstance(f, ServiceFilter)]
            # Add our filter
            handler.addFilter(service_filter)

        # Ensure ALL application loggers propagate and don't have their own handlers
        # This is critical for app.* loggers to work
        app_logger = logging.getLogger("src")
        app_logger.propagate = True
        app_logger.handlers = []  # Remove any existing handlers, use root handlers
        app_logger.setLevel(log_level_numeric)

        # Ensure app.main logger propagates (this is the one used in main.py)
        app_main_logger = logging.getLogger("src.app.main")
        app_main_logger.propagate = True
        app_main_logger.handlers = []
        app_main_logger.setLevel(log_level_numeric)

        # Also ensure all src.* child loggers propagate
        for logger_name in [
            "src.configuration",
            "src.app.routes",
            "src.shared.services",
            "src.app.extensions",
        ]:
            child_logger = logging.getLogger(logger_name)
            child_logger.propagate = True
            child_logger.handlers = []
            child_logger.setLevel(log_level_numeric)

        # Ensure uvicorn loggers propagate to root logger so they go through ServiceFilter
        # This ensures uvicorn access logs get service prefixes and can be filtered
        uvicorn_loggers = [
            logger_constants.LOGGER_UVICORN,
            logger_constants.LOGGER_UVICORN_ACCESS,
            logger_constants.LOGGER_UVICORN_ERROR,
        ]
        for logger_name in uvicorn_loggers:
            uvicorn_logger = logging.getLogger(logger_name)
            uvicorn_logger.propagate = True
            uvicorn_logger.handlers = []  # Remove any existing handlers, use root handlers
            uvicorn_logger.setLevel(log_level_numeric)

        # Note: Datadog is disabled in local development (see app/datadog/__init__.py),
        # so ddtrace logs won't appear in local dev. The terminal/file handler filters
        # will still catch any ddtrace logs that might appear (e.g., if manually enabled).

        # Suppress third-party DEBUG logs if LOG_LEVEL is not DEBUG
        log_level_upper = self.log_level.upper()
        if log_level_upper != "DEBUG":
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
                third_party_logger.setLevel(logging.WARNING)
