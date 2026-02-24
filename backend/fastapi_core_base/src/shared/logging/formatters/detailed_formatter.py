import logging

from src.shared.logging import LogFormatterInterface


class DetailedFormatter(LogFormatterInterface):
    """Detailed formatter with full context information."""

    def get_formatter(self) -> logging.Formatter:
        fmt = (
            self._fmt
            if self._fmt
            else ("%(asctime)s [%(process)d] %(levelname)-8s " "%(name)s:%(funcName)s:%(lineno)d - %(message)s")
        )
        return logging.Formatter(fmt, self.datefmt)
