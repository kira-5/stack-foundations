from src.shared.logging import ApplicationLoggerConfig, UvicornLoggerConfig
from src.shared.logging import constants as logger_constants
from src.shared.logging import settings as logger_settings
from src.shared.logging.configs.base_interface import LogConfigInterface
from src.shared.logging.configs.service_separated_config import ServiceSeparatedLoggerConfig
from src.shared.logging.handler_factory import LogHandlerFactory


class LoggerConfigFactory:
    """Factory for creating logger configurations."""

    _config_map: dict[str, type[LogConfigInterface]] = {
        logger_constants.LOGGER_APPLICATION: ApplicationLoggerConfig,
        logger_constants.LOGGER_UVICORN: UvicornLoggerConfig,
        logger_constants.LOGGER_SERVICE_SEPARATED: ServiceSeparatedLoggerConfig,
    }

    @classmethod
    def create_logger(
        cls,
        logger_type: str = logger_settings.get_logger_type(),
        log_level: str | None = None,
        logging_enabled: bool | None = None,
        handler_types: list[str] | None = None,
    ) -> LogConfigInterface:
        """Create and return a logger configuration."""

        if handler_types is None:
            handler_types = [
                logger_constants.HANDLER_FILE,
            ]

            # Always include Terminal handler for human-readable logs (stdout)
            # Useful for local development and SSH sessions
            handler_types.append(logger_constants.HANDLER_TERMINAL)

            # Add Datadog handler if enabled (writes JSON to stderr)
            # This allows both: readable logs in terminal + JSON for Datadog
            # Terminal -> stdout (colored, human-readable)
            # Datadog -> stderr (JSON format for Datadog agent)
            import os

            # Debug: Print before check
            dd_service_before = os.getenv("DD_SERVICE")
            dd_logs_injection_before = os.getenv("DD_LOGS_INJECTION")
            print(
                f"🔍 [LoggerConfigFactory] Before check - DD_SERVICE={dd_service_before}, DD_LOGS_INJECTION={dd_logs_injection_before}",
            )

            datadog_logging_enabled = logger_settings.is_datadog_logging_enabled()
            print(
                f"🔍 [LoggerConfigFactory] is_datadog_logging_enabled() returned: {datadog_logging_enabled}",
            )

            if datadog_logging_enabled:
                handler_types.append(logger_constants.HANDLER_DATADOG)
                print(
                    "✅ Datadog log handler ENABLED - JSON logs will be written to stderr",
                )
            else:
                dd_service = os.getenv("DD_SERVICE")
                dd_logs_injection = os.getenv("DD_LOGS_INJECTION")
                print(
                    f"⚠️ Datadog log handler DISABLED - DD_SERVICE={dd_service}, DD_LOGS_INJECTION={dd_logs_injection}",
                )

        handlers = LogHandlerFactory.create_handlers(handler_types)

        config_class = cls._config_map.get(logger_type)
        if not config_class:
            raise ValueError(f"Unsupported logger type: {logger_type}")

        config = config_class(
            handlers=handlers,
            log_level=log_level,
            logging_enabled=logging_enabled,
        )
        config.setup()
        return config
