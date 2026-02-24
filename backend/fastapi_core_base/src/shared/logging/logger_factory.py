import logging
from logging import Logger


from src.shared.logging import settings as logger_settings
from src.shared.logging.config_factory import LoggerConfigFactory


class LoggerFactory:
    @staticmethod
    def create_logger() -> Logger:
        """Initialize and configure the logging system using environment settings."""
        if not logger_settings.is_logging_enabled():
            return logging.getLogger()

        # Setting up the configuration
        LoggerConfigFactory.create_logger(
            logger_type=logger_settings.get_logger_type(),
            log_level=logger_settings.get_log_level(),
            logging_enabled=logger_settings.is_logging_enabled(),
        )

        # The root logger is now configured with handlers from the factory
        return logging.getLogger()
