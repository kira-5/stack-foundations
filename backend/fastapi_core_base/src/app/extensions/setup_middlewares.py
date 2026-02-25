import os

from fastapi import FastAPI

# Using src-layout imports
from src.shared.configuration.config import env_config_manager
from src.shared.middleware.log_clear_middleware import LogClearMiddleware
from src.shared.middleware.cors import setup_cors_middleware
from src.shared.middleware.app_version import AppversionMiddleware
from src.shared.middleware.database import DatabaseSessionMiddleware
from src.shared.middleware.maintenance import MaintenanceMiddleware
from src.shared.user_management.utils import is_local_environment

# TODO: Locate or implement TenantContextMiddleware
# from src.shared.middleware.tenant import TenantContextMiddleware

def setup_middlewares(app: FastAPI):
    """Set up application middlewares."""

    # Middleware to clear log file before each API request
    # This should be added first so it runs before other middlewares
    if is_local_environment():
        app.add_middleware(LogClearMiddleware)

    # Middleware for CORS setup (Dynamic from configuration)
    setup_cors_middleware(app)

    # Middleware for app versioning
    app.add_middleware(AppversionMiddleware)

    # Middleware for database session management
    app.add_middleware(DatabaseSessionMiddleware)

    # NOTE: UserContextMiddleware removed - user context is now set directly in
    # CustomRouteHandler._get_user_details() for better performance and clarity
    # Datadog Tracing Middleware (if Datadog is enabled)
    # Skip in local development (Datadog is disabled locally)
    if not is_local_environment():
        # Check if Datadog is configured by checking DD_SERVICE environment variable
        dd_service = os.getenv("DD_SERVICE")
        if dd_service:
            try:
                from src.shared.middleware.datadog import DatadogTracingMiddleware

                # Get sample rate from settings.toml or environment variable (default: 1.0 = 100%)
                sample_rate = getattr(
                    env_config_manager.environment_settings,
                    "DD_TRACE_SAMPLE_RATE",
                    1.0,
                )
                # Convert to float if it's a string
                if isinstance(sample_rate, str):
                    try:
                        sample_rate = float(sample_rate)
                    except ValueError:
                        sample_rate = 1.0

                app.add_middleware(
                    DatadogTracingMiddleware,
                    service_name=dd_service,
                    sample_body_content=False,  # Disable body capture in production
                    sample_rate=sample_rate,  # Sample rate from settings (e.g., 0.1 = 10%)
                )

                # Log the span creation strategy being used
                if DatadogTracingMiddleware.USE_CUSTOM_SPAN:
                    strategy = "custom span (better hierarchy)"
                else:
                    strategy = "FastAPI auto-instrumentation span"
                print(f"✅ Datadog Tracing Middleware: Using {strategy}")
            except ImportError:
                # Datadog middleware not available, skip silently
                pass
            except Exception as e:
                # Log error but don't fail startup
                print(f"⚠️ Failed to add Datadog tracing middleware: {str(e)}")

    # Class-based Middleware for checking maintenance mode (returns 503 when ON)
    app.add_middleware(MaintenanceMiddleware)
