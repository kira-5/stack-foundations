import logging
from abc import ABC, abstractmethod


class LogFormatterInterface(logging.Formatter, ABC):
    """Base class for all formatters."""

    @abstractmethod
    def get_formatter(self) -> logging.Formatter:
        """Return configured formatter."""


# import logging
# from abc import ABC, abstractmethod


# class LogFormatterInterface(ABC):
#     """Base interface for all log formatters."""

#     def __init__(self, fmt=None, datefmt=None):
#         self._fmt = fmt
#         self.datefmt = datefmt

#     @abstractmethod
#     def get_formatter(self) -> logging.Formatter:
#         """Return configured formatter instance."""
#         pass
