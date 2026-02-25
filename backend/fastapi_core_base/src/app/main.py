from contextlib import asynccontextmanager

import firebase_admin
from dotenv import load_dotenv

# =============================================================================
# 1. INITIALIZATION - MUST BE AT THE ABSOLUTE TOP
# =============================================================================
# Load environment variables FIRST so they are available for all components
load_dotenv()

from src.shared.configuration.config import env_config_manager

# Note: Datadog is controlled via DATADOG_ENABLED in config files (.secrets.toml, settings.toml, client TOML)
# The check happens in src/shared/datadog/__init__.py before importing ddtrace
# WHY DATADOG MUST BE BEFORE OTHER IMPORTS:
# 1. Monkey-patching: patch_all() must be called BEFORE libraries (redis, sqlalchemy,
#    psycopg, requests, aiohttp) are imported. Once imported, they're already loaded
#    into memory and can't be properly instrumented.
# 2. Environment variables: DD_* env vars must be set BEFORE importing ddtrace.auto
#    because ddtrace reads them at import time.
# 3. Auto-instrumentation: ddtrace.auto enables automatic tracing, but only works
#    if called before target libraries are imported.
try:
    from src.shared.datadog import initialize_datadog

    # Initialize Datadog configuration (must be before other third-party imports)
    DATADOG_ENABLED = initialize_datadog(env_config_manager)
except Exception as e:
    DATADOG_ENABLED = False
    print(f"⚠️ Datadog initialization failed: {str(e)}")
    print("⚠️ Continuing without Datadog tracing")

# =============================================================================
# 2. CORE IMPORTS
# =============================================================================
from fastapi import FastAPI

from src.shared.configuration import constants as core_constants
from src.shared.configuration.constants import LogEmoji
from src.shared.exceptions import exceptions_handler
from src.app.extensions import setup_middlewares
from src.app.extensions.openapi import custom_openapi
from src.app.extensions.startup_event import startup_event
from src.app.routes import api_routes, app_status_endpoints

from src.shared import logging as shared_logging
# =============================================================================
# 3. LOGGER INITIALIZATION
# =============================================================================
# Initialize and configure the logging system
shared_logging.setup_logging()

# Global logger instance
logger = shared_logging.get_logger(__name__)

# Test: Write a log immediately after initialization to verify handlers are working
logger.info("🔍 Logger initialized - testing log handlers")


def log_environment_settings():
    """Log current environment settings after startup."""
    environment_current = f"{LogEmoji.ENVIRONMENT} Current Environment: {env_config_manager.environment}"
    logger.info(environment_current)


async def perform_cleanup():
    """Perform application cleanup during shutdown."""
    shutdown_info = f"{LogEmoji.START_STATUS} System Shutdown Information {LogEmoji.START_STATUS}"
    shutdown_services = f"{LogEmoji.SERVER_SHUTDOWN} Backend Shutting down services..."

    logger.info(shutdown_info)
    logger.info(shutdown_services)

    # Flush Datadog traces before shutdown (critical for Cloud Run)
    if DATADOG_ENABLED:
        try:
            from ddtrace.trace import tracer

            tracer.flush()
            logger.info("✅ Datadog traces flushed")
        except Exception as e:
            logger.error(f"❌ Error flushing Datadog traces: {e}")

    # Shutdown WebSocket manager and Redis Pub/Sub
    try:
        # TODO: Locate or implement websocket_manager in src.shared
        # from src.shared.notifications.websocket_manager import websocket_manager
        # await websocket_manager.stop()
        logger.info("⏳ WebSocket manager shutdown (skipped - missing implementation)")
    except Exception as e:
        logger.error(f"❌ Error shutting down WebSocket manager: {e}")

    # Close Redis connections
    try:
        from src.shared.services.redis_service import redis_service

        await redis_service.close()
        logger.info("✅ Redis service shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error shutting down Redis service: {e}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage application startup and shutdown events."""
    try:
        startup_info = f"{LogEmoji.START_STATUS} System Startup Information {LogEmoji.START_STATUS}"
        startup_services = f"{LogEmoji.SERVER_STARTUP} Backend Starting up services..."

        logger.info(startup_info)
        logger.info(startup_services)

        # 1. Perform core system startup events
        await startup_event()

        # 2. Log environment state
        log_environment_settings()

        # 3. Initialize Firebase
        try:
            firebase_admin.initialize_app()
        except ValueError:
            # Already initialized or invalid config
            pass

        yield
    except Exception as e:
        logger.error(
            "Startup failed",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise
    finally:
        await lifespan.perform_cleanup()


# Add perform_cleanup to lifespan for cleaner access if needed, 
# but main.py has it as a standalone function. 
# Let's just call it directly as defined above.
lifespan.perform_cleanup = perform_cleanup

# =============================================================================
# 4. APP FACTORY
# =============================================================================
app = FastAPI(
    title=core_constants.API_TITLE,
    description="Base Pricing Platform API",
    summary="Core API for managing base pricing logic and optimizations.",
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    docs_url=f"{core_constants.API_PREFIX}/docz",
    redoc_url=f"{core_constants.API_PREFIX}/redocz",
    openapi_url=f"{core_constants.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)


@app.get("/docs", include_in_schema=False)
async def root():
    """Redirect or provide status for /docs."""
    return {"Success": True}


# Register OpenAPI customization
app.openapi = lambda: custom_openapi(app)

# Register middleware
setup_middlewares.setup_middlewares(app)

# Add exception handlers
exceptions_handler.add_exception_handlers(app)

# Include all routers
api_routes.include_routers(app)

# Health and Monitoring routes
app_status_endpoints.app_health_status_check(app)
app_status_endpoints.app_maintenance_status_check(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)
