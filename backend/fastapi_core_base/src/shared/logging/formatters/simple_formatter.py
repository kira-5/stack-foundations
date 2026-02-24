import logging

from src.shared.logging import LogFormatterInterface


class SimpleFormatter(LogFormatterInterface):
    """Custom formatter that handles both structured and MTP-style formats."""

    def get_formatter(self) -> logging.Formatter:
        fmt = self._fmt if self._fmt else "%(levelname)s: %(message)s"
        return logging.Formatter(fmt, self.datefmt)
