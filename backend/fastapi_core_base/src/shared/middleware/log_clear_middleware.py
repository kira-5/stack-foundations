import glob
import os
import platform
from datetime import datetime, timedelta

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.shared.logging import settings as logger_settings


class LogClearMiddleware(BaseHTTPMiddleware):
    """Middleware to clear log file before each API request."""

    async def dispatch(self, request: Request, call_next):
        """Clear log file before processing the request."""

        # Skip clearing for health check endpoints to avoid unnecessary file operations
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            response = await call_next(request)
            return response

        # Get log file path from settings
        log_file_path = logger_settings.get_log_file_path()

        try:
            # Clear the main log file if it exists
            if os.path.exists(log_file_path):
                # Open file in write mode to truncate it (clears all content)
                with open(log_file_path, "w") as f:
                    f.write("")  # Write empty string to clear file

            # Also delete old log files (app.log.1, app.log.2, etc.) older than 30 days
            # This mimics the behavior of: find logs/ -name "app.log*" -mtime +30 -delete
            log_dir = os.path.dirname(log_file_path)
            log_base_name = os.path.basename(log_file_path)

            if os.path.exists(log_dir):
                # Find all log files matching pattern (app.log, app.log.1, app.log.2, etc.)
                log_pattern = os.path.join(log_dir, f"{log_base_name}*")
                log_files = glob.glob(log_pattern)

                # Calculate cutoff time (30 days ago)
                cutoff_time = datetime.now() - timedelta(days=30)

                for log_file in log_files:
                    try:
                        # Skip the main log file (we already cleared it)
                        if log_file == log_file_path:
                            continue

                        # Check if file is older than 30 days
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                        if file_mtime < cutoff_time:
                            os.remove(log_file)
                    except Exception:
                        # If deletion fails, continue with other files
                        pass

        except Exception:
            # If clearing fails, don't break the request
            # We can't use logger here as it might cause circular dependency
            # Just continue with the request
            pass

        # Clear terminal screen using system command
        # This will clear the terminal where the server is running
        try:
            # Use 'clear' for Unix/Linux/macOS, 'cls' for Windows
            clear_command = "cls" if platform.system() == "Windows" else "clear"
            os.system(clear_command)  # nosec B605
        except Exception:
            # If clearing terminal fails, continue with the request
            pass

        # Process the request
        response = await call_next(request)
        return response
