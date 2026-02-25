import os

from src.shared.configuration.config import env_config_manager
from src.shared.services.database_service import database_service
from src.shared.services.logging_service import LoggingService

logger = LoggingService.get_logger(__name__)

NOTIFIER_TABLE = "base_pricing.bp_notifier_config"
TRUTHY_VALUES = {"1", "true", "yes", "y", "on"}


def _normalize_key(value: str) -> str:
    return value.strip().upper()


def _build_env_key(process_key: str, channel_key: str, setting_key: str) -> str:
    return f"NOTIFIER_{_normalize_key(process_key)}_" f"{_normalize_key(channel_key)}_" f"{_normalize_key(setting_key)}"


def _parse_bool(value: object | None) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in TRUTHY_VALUES


def _parse_recipients(value: str) -> list[str]:
    recipients = [email.strip() for email in value.replace(";", ",").split(",") if email.strip()]
    valid_emails = []
    for email in recipients:
        if "@" in email and "." in email.split("@")[1]:
            valid_emails.append(email)
        else:
            logger.warning(f"Invalid email format in recipients list: {email}")
    return valid_emails


async def get_notifier_setting_value(
    process_key: str,
    channel_key: str,
    setting_key: str,
) -> str | None:
    env_key = _build_env_key(process_key, channel_key, setting_key)
    # Explicit env check first so .env / export always wins over DB and config files
    env_value = os.getenv(env_key) or os.getenv(env_key.upper())
    if env_value is not None and str(env_value).strip():
        return str(env_value).strip()
    env_value = env_config_manager.get_dynamic_setting(env_key)
    if env_value is not None and str(env_value).strip():
        return str(env_value).strip()

    query = f"""
        SELECT setting_value
        FROM {NOTIFIER_TABLE}
        WHERE process_key = '{process_key}'
          AND channel_key = '{channel_key}'
          AND setting_key = '{setting_key}'
        LIMIT 1
    """

    try:
        result = await database_service.execute_async_query(
            query,
            db_type="postgres",
        )
    except Exception as exc:
        logger.warning(
            f"Failed to read notifier config {process_key}/{channel_key}/{setting_key}: {exc}",
        )
        return None

    if not result or not isinstance(result, list):
        return None

    row = result[0]
    if isinstance(row, dict):
        return row.get("setting_value")
    if isinstance(row, (list, tuple)):
        return row[0] if row else None
    return None


async def get_notifier_bool_setting(
    process_key: str,
    channel_key: str,
    setting_key: str,
) -> bool | None:
    value = await get_notifier_setting_value(process_key, channel_key, setting_key)
    return _parse_bool(value)


async def get_notifier_recipients_setting(
    process_key: str,
    channel_key: str,
    setting_key: str = "RECIPIENTS",
) -> list[str]:
    value = await get_notifier_setting_value(process_key, channel_key, setting_key)
    if not value:
        return []
    return _parse_recipients(value)


async def get_notifier_category(process_key: str) -> str | None:
    """Fetch the category for a given process key from the database."""
    # Check environment override first (convention: NOTIFIER_{PROCESS}_CATEGORY)
    env_key = f"NOTIFIER_{_normalize_key(process_key)}_CATEGORY"
    env_value = env_config_manager.get_dynamic_setting(env_key)
    if env_value is not None and str(env_value).strip():
        return str(env_value).strip()

    query = f"""
        SELECT category
        FROM {NOTIFIER_TABLE}
        WHERE process_key = '{process_key}'
        LIMIT 1
    """

    try:
        result = await database_service.execute_async_query(
            query,
            db_type="postgres",
        )
        if result and isinstance(result, list):
            row = result[0]
            if isinstance(row, dict):
                return row.get("category")
            if isinstance(row, (list, tuple)):
                return row[0] if row else None
    except Exception as exc:
        logger.warning(
            f"Failed to read notifier category for {process_key}: {exc}",
        )
    return None
