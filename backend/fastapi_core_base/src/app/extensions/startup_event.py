import glob
import os
import platform
from datetime import datetime, timedelta

from src.shared.configuration.config import env_config_manager
from src.shared.configuration.constants import LogEmoji
from src.shared.db.core.connection_manager import PostgresConnection
from src.shared.db.core.driver_context import DatabaseDriverManager, DatabaseDrivers
from src.shared.logging import settings as logger_settings
from src.shared.services.logging_service import LoggingService
from src.shared.user_management import utils as um_utils

logger = LoggingService.get_logger(__name__)


def _prune_old_logs(log_file_path: str, days: int = 30):
    """Helper to prune log files older than X days."""
    log_dir = os.path.dirname(log_file_path)
    log_base_name = os.path.basename(log_file_path)

    if not os.path.exists(log_dir):
        return

    log_pattern = os.path.join(log_dir, f"{log_base_name}*")
    log_files = glob.glob(log_pattern)
    cutoff_time = datetime.now() - timedelta(days=days)

    deleted_count = 0
    for log_file in log_files:
        try:
            if log_file == log_file_path:
                continue
            file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
            if file_mtime < cutoff_time:
                os.remove(log_file)
                deleted_count += 1
        except Exception:
            pass

    if deleted_count > 0:
        logger.info(
            f"{LogEmoji.SUCCESS_STATUS} Pruned {deleted_count} old log files (>{days} days).",
        )


def clear_logs():
    """Clear log file and terminal at startup with Deep Clean and Session Banners."""
    try:
        # Get log file path from settings
        log_file_path = logger_settings.get_log_file_path()

        # 1. Clear the main log file (Safe Plain-Text for File)
        banner = ""  # Initialize to avoid UnboundLocalError
        if os.path.exists(log_file_path):
            initial_size = os.path.getsize(log_file_path)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            env_val = os.getenv("env", "unknown")

            with open(log_file_path, "w", encoding="utf-8") as f:
                banner = "=" * 80 + "\n" + f"🚀 SESSION START: {now} | Environment: {env_val}\n" + "=" * 80 + "\n"
                f.write(banner)

            reclaimed = (initial_size - len(banner)) / 1024
            if reclaimed > 0:
                logger.debug(
                    f"{LogEmoji.SUCCESS_STATUS} Log file cleared. Reclaimed: {reclaimed:.2f} KB",
                )
            else:
                logger.debug(
                    f"{LogEmoji.SUCCESS_STATUS} Log file initialized with session banner.",
                )

        # 2. Prune old logs (Older than 30 days)
        _prune_old_logs(log_file_path, days=30)

        # 3. Deep Terminal Clear (Wipes scrollback buffer)
        try:
            if platform.system() != "Windows":
                # Deep clear sequence: Clear screen + Clear scrollback
                os.system('printf "\\033c\\033[3J"')

                # Create a simple terminal version
                terminal_banner = (
                    "\n" + "=" * 80 + "\n" + f"🚀 SESSION START: {now} | Environment: {env_val}\n" + "=" * 80 + "\n"
                )
                print(terminal_banner)
            else:
                os.system("cls")
                print(banner)

            logger.debug(
                f"{LogEmoji.SUCCESS_STATUS} Terminal Deep Cleared and Banner Displayed (Unified Style)",
            )
        except Exception:
            pass

    except Exception as e:
        logger.warning(f"⚠️ Failed to clear logs: {e}")


async def startup_event():
    """Perform startup events."""

    # Clear logs and terminal at startup (only in local environment)
    if um_utils.is_local_environment():
        clear_logs()

    # Detect and load client configuration
    await detect_and_load_client_config()

    # Fetch secrets and update environment configuration
    await env_config_manager.fetch_secrets_and_update_env_settings()
    # logger.info(
    #     f"{LogEmoji.CONFIGURATION} Environment Configuration Status {LogEmoji.CONFIGURATION}",
    # )
    logger.info(
        f"{LogEmoji.SUCCESS_STATUS} Configuration and secrets loaded successfully",
    )

    # Initialize the database driver once during startup
    database_driver = DatabaseDrivers.ASYNC_PG
    DatabaseDriverManager.set_db_driver(database_driver)
    PostgresConnection.initialize(database_driver)
    # logger.info(
    #     f"{LogEmoji.DATABASE_OPERATION} Database Connection Status {LogEmoji.DATABASE_OPERATION}",
    # )
    logger.info(
        f"{LogEmoji.SUCCESS_STATUS} Database connection pool established ({database_driver})",
    )

    # Initialize Redis service for multi-worker support
    try:
        from src.shared.services.redis_service import redis_service

        await redis_service.initialize()
        if redis_service.is_available():
            logger.info(
                "✅ Redis service initialized successfully for multi-worker support",
            )
        else:
            logger.warning("⚠️ Redis not available - running in single-worker mode")
    except Exception as e:
        logger.warning(
            f"⚠️ Failed to initialize Redis: {e} - running in single-worker mode",
        )

    # Initialize WebSocket manager with Redis Pub/Sub
    try:
        from src.shared.notifier.websocket_manager import websocket_manager

        await websocket_manager.start()
        logger.info("🔄 WebSocket manager with Redis Pub/Sub started successfully")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start WebSocket manager: {e}")


async def detect_and_load_client_config():
    """Detect tenant and environment, then load client configuration."""

    # logger.info(
    #     f"{LogEmoji.CONFIGURATION} Client Configuration Detection {LogEmoji.CONFIGURATION}",
    # )

    # Get environment from configuration
    environment = env_config_manager.environment_settings.get("DEPLOYMENT_ENV")
    if not environment:
        environment = env_config_manager.environment_settings.get("ENVIRONMENT")
    if not environment:
        environment = env_config_manager.environment or "dev"

    logger.debug(f"{LogEmoji.ENVIRONMENT} Detected Environment: {environment}")

    # Try to detect tenant from various sources
    tenant_id = None

    # Method 1: Environment variables
    tenant_id = os.getenv("CLIENT_NAME") or os.getenv("TENANT_ID")
    if tenant_id:
        logger.debug(
            f"{LogEmoji.SUCCESS_STATUS} Tenant detected from environment variables: {tenant_id}",
        )

    # Method 2: Get tenant from TENANT_NAME environment variable
    if not tenant_id:
        tenant_id = os.getenv("TENANT_NAME")
        if tenant_id:
            logger.debug(
                f"{LogEmoji.SUCCESS_STATUS} Tenant detected from TENANT_NAME environment variable: {tenant_id}",
            )

    # Method 3: If not found in env vars, try to get from .secrets.toml
    if not tenant_id:
        try:
            # Debug: Let's see what's actually in the environment settings
            logger.debug(
                f"{LogEmoji.INFO_STATUS} Checking .secrets.toml for tenant...",
            )
            # logger.info(
            #     f"{LogEmoji.INFO_STATUS} Environment settings keys: {list(env_config_manager.environment_settings.keys())}",
            # )

            # Try TENANT_NAME first (since that's what you have in .secrets.toml)
            tenant_id = env_config_manager.environment_settings.get("TENANT_NAME")
            if tenant_id:
                logger.debug(
                    f"{LogEmoji.SUCCESS_STATUS} Tenant detected from .secrets.toml (TENANT_NAME): {tenant_id}",
                )
            else:
                # Try TENANT_ID as fallback
                tenant_id = env_config_manager.environment_settings.get("TENANT_ID")
                if tenant_id:
                    logger.debug(
                        f"{LogEmoji.SUCCESS_STATUS} Tenant detected from .secrets.toml (TENANT_ID): {tenant_id}",
                    )
                else:
                    logger.warning(
                        f"{LogEmoji.WARNING_STATUS} No TENANT_NAME or TENANT_ID found in .secrets.toml",
                    )
        except Exception as e:
            logger.warning(f"Could not read tenant from .secrets.toml: {e}")

    # Method 4: List available clients and use first one as default
    if not tenant_id:
        available_clients = env_config_manager.list_available_clients()
        if available_clients:
            tenant_id = available_clients[0]["tenant_id"]
            logger.debug(
                f"{LogEmoji.SUCCESS_STATUS} Using first available client as default: {tenant_id}",
            )
        else:
            logger.warning(f"{LogEmoji.WARNING_STATUS} No client configurations found")
            return

    # Load client configuration
    if tenant_id and environment:
        try:
            logger.info(
                f"{LogEmoji.LOADING_STATUS} Loading client configuration for tenant: {tenant_id}, environment: {environment}",
            )

            # Ensure client config is loaded
            env_config_manager.ensure_client_config_loaded(tenant_id, environment)

            # Load the configuration
            env_config_manager.load_dynamic_client_config(
                tenant_id,
                environment,
            )

            # Log client information
            client_info = env_config_manager.get_client_info()
            logger.info(
                f"{LogEmoji.SUCCESS_STATUS} {tenant_id.capitalize()} configuration loaded ({environment})",
            )
            logger.debug(f"{LogEmoji.CONFIGURATION} Client Info: {client_info}")

        except Exception as e:
            logger.error(
                f"{LogEmoji.ERROR_STATUS} Error loading client configuration: {e}",
            )
    else:
        logger.warning(
            f"{LogEmoji.WARNING_STATUS} No tenant_id ({tenant_id}) or "
            f"environment ({environment}) available for client config loading",
        )
