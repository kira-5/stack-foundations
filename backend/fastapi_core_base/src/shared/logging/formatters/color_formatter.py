import logging
import os
import re

from src.shared.logging import LogFormatterInterface
from src.shared.logging import constants as logger_constants

# Conditionally import ddtrace only if Datadog is enabled
try:
    from ddtrace.trace import tracer
except ImportError:
    tracer = None


class ColorFormatter(LogFormatterInterface):
    """Formatter that handles colored output with Datadog correlation."""

    COLORS = logger_constants.LOG_COLORS

    def __init__(self, fmt=None, datefmt=None, strip_colors=False):
        """Initialize the formatter.

        :param fmt: Format string
        :param datefmt: Date format string
        :param strip_colors: Whether to strip ANSI color codes
        """
        super().__init__(fmt, datefmt)
        self.strip_colors = strip_colors
        self._fmt = fmt  # Store fmt for get_formatter()

    def get_formatter(self) -> logging.Formatter:
        """Return configured formatter (returns self since ColorFormatter is already a
        Formatter)."""
        return self

    def format(self, record):
        """Format the log record with Datadog trace correlation and colors."""
        # 1. Inject Datadog Trace context into the record safely
        if tracer is not None:
            try:
                span = tracer.current_span()
                if span:
                    # Datadog standard trace context attributes
                    record.dd_trace_id = str(span.trace_id)
                    record.dd_span_id = str(span.span_id)
                else:
                    record.dd_trace_id = "0"
                    record.dd_span_id = "0"
            except Exception:
                # If tracer is not available or fails, set defaults
                record.dd_trace_id = "0"
                record.dd_span_id = "0"
        else:
            # Datadog not available - set defaults
            record.dd_trace_id = "0"
            record.dd_span_id = "0"

        # Add service and environment context
        record.dd_service = os.getenv("DD_SERVICE", "basesmart-app")
        record.dd_env = os.getenv("DD_ENV", "development")

        # 2. Handle service prefix and coloring logic
        orig_msg = record.msg
        orig_levelname = record.levelname
        service_color = getattr(record, "service_color", None)
        service_name = getattr(record, "service_name", None)

        if service_name:
            # Check if this is a UVICORN access log with an error status code FIRST
            # (before setting prefix color, so we can make prefix red too)
            # This check runs for BOTH terminal and file logs
            is_uvicorn_error = False
            is_uvicorn = (service_name and service_name.lower() == logger_constants.SERVICE_UVICORN.lower()) or (
                hasattr(record, "name") and "uvicorn" in record.name.lower()
            )

            if is_uvicorn:
                # Get HTTP status code from record.args (not from msg, which is just a format string)
                # UVICORN access log format: args = (client_ip:port, method, path, http_version, status_code)
                # Status code is at args[4] (last element)
                if hasattr(record, "args") and record.args and len(record.args) >= 5:
                    try:
                        status_code = record.args[4]  # Status code is the 5th element (index 4)
                        if isinstance(status_code, int):
                            # Mark as error if status code is 4xx or 5xx
                            if 400 <= status_code < 600:
                                is_uvicorn_error = True
                    except (IndexError, TypeError, ValueError):
                        pass

            # Add service prefix BEFORE levelname (so it appears before level in format string)
            if self.strip_colors:
                # For file logs: add ERROR indicator for UVICORN errors
                if is_uvicorn_error:
                    prefix = f"[{service_name.upper()}-ERROR]"
                else:
                    prefix = f"[{service_name.upper()}]"
                record.levelname = f"{prefix} - {orig_levelname}"
            else:
                # For terminal logs: colored prefix
                # Use ERROR color (red) for UVICORN errors, otherwise use service color
                if is_uvicorn_error:
                    prefix_color = self.COLORS.get("ERROR", self.COLORS["RESET"])
                else:
                    prefix_color = service_color if service_color else ""
                prefix = f"{prefix_color}[{service_name.upper()}]{self.COLORS['RESET']}"
                record.levelname = f"{prefix} - {orig_levelname}"

            # Add message color (only if not stripping colors)
            # Use service color for message when service is present (matches prefix color)
            # Exception: For UVICORN access logs with error status codes (4xx, 5xx), use ERROR color (red)
            if not self.strip_colors:
                # For UVICORN errors, use ERROR color (red) instead of service color or log level color
                if is_uvicorn_error:
                    message_color = self.COLORS.get("ERROR", self.COLORS["RESET"])
                else:
                    # Use service color for normal messages
                    message_color = (
                        service_color if service_color else self.COLORS.get(orig_levelname, self.COLORS["RESET"])
                    )

                record.msg = f"{message_color}{orig_msg}{self.COLORS['RESET']}"
            # For file logs, msg stays as-is (prefix is in levelname)
        elif not self.strip_colors:
            # No service prefix, but add level color for terminal
            color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
            record.msg = f"{color}{orig_msg}{self.COLORS['RESET']}"

        try:
            # 3. Use the standard formatter logic
            # This will now look for %(dd_trace_id)s in your format string if needed
            formatted_message = super().format(record)
        except (KeyError, ValueError):
            # Fallback formatting if there's an error
            formatted_message = f"{record.levelname}: {record.msg}"
        finally:
            # Reset message and levelname so future handlers don't get nested colors/prefixes
            record.msg = orig_msg
            record.levelname = orig_levelname

        # 4. Strip colors if needed (for file output)
        # This removes ANSI color codes but preserves the [SERVICE] prefix
        if self.strip_colors:
            ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
            formatted_message = ansi_escape.sub("", formatted_message)

        return formatted_message
