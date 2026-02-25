"""Models for User Management module.

This module provides data access functions for user access control.
"""

from src.shared.services.database_service import database_service
from src.shared.services.logging_service import LoggingService
from src.shared.user_management import queries as user_management_queries

logger = LoggingService.get_logger(__name__)


async def get_hierarchical_access_data_models(user_id: int) -> list[dict]:
    """Fetch hierarchical screen/module access data for a user.

    Args:
        user_id: User ID

    Returns:
        List of hierarchical access dictionaries
    """
    logger.info(f"🔍 Fetching hierarchical access data for user_id: {user_id}")

    try:
        result = await database_service.execute_async_query(
            user_management_queries.HIERARCHICAL_ACCESS_QUERY.format(user_code=user_id),
        )

        # Extract the result from the JSON aggregate
        hierarchical_data = result[0].get("result", []) if result and len(result) > 0 else []

        logger.info(
            f"✅ Fetched hierarchical access data: {len(hierarchical_data) if hierarchical_data else 0} items",
        )
        return hierarchical_data or []

    except Exception as e:
        logger.error(f"❌ Error fetching hierarchical access data: {e}")
        return []


async def get_module_actions_data_models(user_id: int) -> list[dict]:
    """Fetch module-level actions with access control for a user.

    Args:
        user_id: User ID

    Returns:
        List of module action dictionaries
    """
    logger.info(f"🔍 Fetching module actions data for user_id: {user_id}")

    try:
        result = await database_service.execute_async_query(
            user_management_queries.MODULE_ACTIONS_QUERY.format(user_code=user_id),
        )

        logger.info(f"✅ Fetched {len(result) if result else 0} module actions")
        return result or []

    except Exception as e:
        logger.error(f"❌ Error fetching module actions data: {e}")
        return []


async def sync_user_access_hierarchy_models(user_id: int) -> bool:
    """Sync user access hierarchy.

    Args:
        user_id: User ID

    Returns:
        True if sync successful, False otherwise
    """
    logger.info(f"🔄 Syncing user access hierarchy for user_id: {user_id}")

    try:
        query = user_management_queries.SYNC_USER_ACCESS_HIERARCHY_QUERY.format(
            user_code=user_id,
        )

        await database_service.execute_async_query(query, session_user_id=None)
        logger.info(f"✅ User access hierarchy synced for user_id: {user_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Error syncing user access hierarchy: {e}")
        return False
