import logging

from src.shared.logging.base import LogFormatterInterface


class MTPFormatter(LogFormatterInterface):
    """MTP-style formatter with message|timestamp|process format."""

    def get_formatter(self) -> logging.Formatter:
        fmt = self._fmt if self._fmt else "%(message)s|%(asctime)s|%(process)d"
        return logging.Formatter(fmt, self.datefmt)
