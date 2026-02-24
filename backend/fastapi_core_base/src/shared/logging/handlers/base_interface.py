import logging
from abc import ABC, abstractmethod


class LogHandlerInterface(ABC):
    """Base class for all logging handlers."""

    @abstractmethod
    def get_handler(self) -> logging.Handler:
        """Return configured logging handler."""

    def set_formatter(
        self,
        handler: logging.Handler,
        formatter: logging.Formatter,
    ) -> None:
        """Set formatter for the handler."""

        handler.setFormatter(formatter)
