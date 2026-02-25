from src.shared.services.database_service import database_service
from src.shared.services.redis_service import redis_service

REDIS_KEY_MAINTENANCE = "app:maintenance:status"
REDIS_KEY_DATA_INGESTION = "app:data_ingestion:status"
NAMESPACE = "app_status"

# Redis stores non-dict/list as str(value), so bool False becomes "False"; bool("False") is True.
_TRUE_VALUES = {True, "true", "True", "1", 1}
_FALSE_VALUES = {False, "false", "False", "0", 0}


def _redis_value_to_bool(value) -> bool:
    """Convert value from Redis (str/bool/bytes) to bool.

    Handles str('False') correctly.
    """
    if value is None:
        return False
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace").strip()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    # Legacy: non-empty string treated as True
    return bool(value)


class AppStatusService:
    @staticmethod
    async def set_flag(flag_name: str, status: bool):
        """Update a flag in both DB and Redis."""
        query = f"""
            UPDATE base_pricing.bp_app_status_master
            SET status = {status},
                updated_at = CURRENT_TIMESTAMP
            WHERE flag_name = '{flag_name}'
            AND is_active = TRUE
        """
        await database_service.execute_transactional_query(
            query=query,
        )

        # Sync with Redis
        redis_key = REDIS_KEY_MAINTENANCE if flag_name == "app_maintenance" else REDIS_KEY_DATA_INGESTION
        await redis_service.set_cache(
            key=redis_key,
            value=status,
            expire_seconds=86400,
            namespace=NAMESPACE,
        )

    @staticmethod
    async def get_flag(flag_name: str) -> bool:
        """Get flag status, checking Redis first."""
        redis_key = REDIS_KEY_MAINTENANCE if flag_name == "app_maintenance" else REDIS_KEY_DATA_INGESTION
        redis_status = await redis_service.get_cache(key=redis_key, namespace=NAMESPACE)

        if redis_status is not None:
            return _redis_value_to_bool(redis_status)

        query = f"""
            SELECT status FROM base_pricing.bp_app_status_master
            WHERE flag_name = '{flag_name}'
            AND is_active = TRUE
        """
        res = await database_service.execute_transactional_query(
            query=query,
        )

        status = False
        if res and isinstance(res, list) and len(res) > 0:
            status = res[0].get("status")
            # Lazy load into Redis
            await redis_service.set_cache(
                key=redis_key,
                value=status,
                expire_seconds=86400,
                namespace=NAMESPACE,
            )

        return bool(status)


app_status_service = AppStatusService()
