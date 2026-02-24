import json
import logging
import os
import sys

from src.shared.logging import LogHandlerInterface

# Conditionally import ddtrace only if Datadog is enabled
try:
    from ddtrace.trace import tracer
except ImportError:
    tracer = None


class DatadogLogHandler(LogHandlerInterface):
    """Handler for sending logs to Datadog with trace correlation.

    This handler formats logs as JSON and sends them to stdout/stderr,
    which the Datadog agent will pick up when DD_LOGS_INJECTION is
    enabled.
    """

    def __init__(self, level: int | None = None, use_stderr: bool = True):
        """Initialize Datadog handler.

        :param level: Logging level (defaults to logger settings)
        :param use_stderr: Whether to use stderr instead of stdout
            (default: True) Uses stderr so it doesn't conflict with
            Terminal handler (stdout)
        """
        self.level = level
        self.use_stderr = use_stderr
        self._handler: logging.Handler | None = None

    def get_handler(self) -> logging.Handler:
        """Configure and return a Datadog log handler with trace correlation."""
        if self._handler is None:
            # Use stderr by default so Terminal handler can use stdout
            # This prevents duplicate logs: Terminal (stdout) + Datadog (stderr)
            # Datadog agent picks up logs from both stdout and stderr
            stream = sys.stderr if self.use_stderr else sys.stdout

            # Debug: Print which stream we're using
            stream_name = "stderr" if self.use_stderr else "stdout"
            print(f"📤 Datadog handler writing JSON logs to {stream_name}")

            self._handler = logging.StreamHandler(stream)

            # Set formatter that includes trace context as JSON
            formatter = DatadogJSONFormatter()
            self.set_formatter(self._handler, formatter)

            # Debug: Write a test log to verify it's working
            import json

            test_log = {
                "timestamp": "2026-01-18T02:40:58.000Z",
                "level": "INFO",
                "logger": "datadog_handler_init",
                "message": "Datadog handler initialized - JSON logs will be written to stderr",
                "dd.service": os.getenv("DD_SERVICE", "unknown"),
                "dd.env": os.getenv("DD_ENV", "unknown"),
            }
            stream.write(json.dumps(test_log) + "\n")
            stream.flush()

            # Always send JSON logs to stderr for Datadog collection
            # Datadog agent collects from both stdout and stderr streams
            # On backend servers, logs go to stdout (terminal handler) and stderr (Datadog handler)
            # Datadog agent should be configured to collect from both streams

        return self._handler


class DatadogJSONFormatter(logging.Formatter):
    """Custom JSON formatter for Datadog logs with trace correlation."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with Datadog trace context.

        Uses tracer.get_log_correlation_context() to automatically inject:
        - dd.trace_id
        - dd.span_id
        - dd.service
        - dd.env
        - dd.version
        """
        # Build log data structure
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Get correlation context from tracer (automatically includes trace_id, span_id, service, env, version)
        # This is the recommended way per Datadog documentation
        if tracer is not None:
            try:
                correlation_context = tracer.get_log_correlation_context()
                # Ensure all required fields are present
                log_data.update(correlation_context)
                # CRITICAL: Always override dd.service with DD_SERVICE env var to ensure consistency
                # This ensures logs use the same service name as traces (basesmart-lesliespool-be-test)
                # The tracer correlation context might return a different service name, so we override it
                dd_service_env = os.getenv("DD_SERVICE")
                if dd_service_env:
                    log_data["dd.service"] = dd_service_env
                elif "dd.service" not in log_data or not log_data.get("dd.service"):
                    log_data["dd.service"] = "basesmart-app"
                if "dd.env" not in log_data or not log_data.get("dd.env"):
                    log_data["dd.env"] = os.getenv("DD_ENV", "development")
                if "dd.version" not in log_data:
                    log_data["dd.version"] = os.getenv("DD_VERSION", "")
            except Exception:
                # Fallback to manual extraction if correlation context fails
                try:
                    span = tracer.current_span()
                    if span:
                        log_data["dd.trace_id"] = str(span.trace_id)
                        log_data["dd.span_id"] = str(span.span_id)
                except Exception:
                    pass
                # CRITICAL: Always use DD_SERVICE env var for service name consistency
                dd_service_env = os.getenv("DD_SERVICE")
                log_data["dd.service"] = dd_service_env if dd_service_env else "basesmart-app"
                log_data["dd.env"] = os.getenv("DD_ENV", "development")
                log_data["dd.version"] = os.getenv("DD_VERSION", "")
        else:
            # Datadog not available - set defaults from environment
            log_data["dd.trace_id"] = "0"
            log_data["dd.span_id"] = "0"
            # CRITICAL: Always use DD_SERVICE env var for service name consistency
            dd_service_env = os.getenv("DD_SERVICE")
            log_data["dd.service"] = dd_service_env if dd_service_env else "basesmart-app"
            log_data["dd.env"] = os.getenv("DD_ENV", "development")
            log_data["dd.version"] = os.getenv("DD_VERSION", "")

        # Add exception info if present
        if record.exc_info:
            log_data["error.kind"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            log_data["error.message"] = str(record.exc_info[1]) if record.exc_info[1] else None
            log_data["error.stack"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra") and record.extra:
            log_data.update(record.extra)

        # Add common extra fields
        extra_fields = [
            "user_id",
            "tenant_id",
            "strategy_id",
            "plan_id",
            "product_id",
            "store_id",
            "request_id",
            "session_id",
            "model_type",
            "view_type",
            "error_type",
            "error_message",
        ]

        for field in extra_fields:
            if hasattr(record, field):
                value = getattr(record, field)
                if value is not None:
                    log_data[field] = str(value)

        # Add file location info
        log_data["file.name"] = record.filename
        log_data["file.line"] = record.lineno
        log_data["file.function"] = record.funcName

        # Add service component tag if available (from ServiceFilter)
        service_name = getattr(record, "service_name", None)
        if service_name:
            log_data["component"] = service_name
            # Also add as tag for filtering
            log_data["service.component"] = service_name

        # Convert to JSON string
        try:
            return json.dumps(log_data, default=str, ensure_ascii=False)
        except Exception:
            # Fallback to simple format if JSON serialization fails
            return f"{record.levelname}: {record.getMessage()}"
