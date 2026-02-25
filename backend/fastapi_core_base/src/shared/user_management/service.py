"""Service layer for User Management module.

This module provides business logic for user access control operations.
"""

from src.shared.services.logging_service import LoggingService
from src.shared.user_management import models as user_management_models

logger = LoggingService.get_logger(__name__)


async def get_user_access_details_service(user_id: int) -> dict:
    """Get user access details with module actions.

    This service function fetches module-level actions with access control.

    Args:
        user_id: User ID

    Returns:
        Dictionary with module_actions data
    """
    logger.info(f"📋 Getting user access details for user_id: {user_id}")

    try:
        # Fetch module actions data
        module_actions_data = await user_management_models.get_module_actions_data_models(user_id)

        result = {
            "module_actions": module_actions_data,
        }

        logger.info(
            f"✅ Retrieved user access details: " f"{len(module_actions_data)} module actions",
        )

        return result

    except Exception as e:
        logger.error(f"❌ Error getting user access details: {e}")
        raise


async def sync_user_access_hierarchy_service(user_id: int) -> dict:
    """Sync user access hierarchy.

    Args:
        user_id: User ID

    Returns:
        Dictionary with sync results
    """
    logger.info(f"🔄 Syncing user access hierarchy for user_id: {user_id}")

    try:
        success = await user_management_models.sync_user_access_hierarchy_models(
            user_id,
        )

        if success:
            logger.info(f"✅ User access hierarchy synced for user_id: {user_id}")
            return {
                "user_code": user_id,
                "sync_status": "success",
            }
        else:
            logger.error(
                f"❌ Failed to sync user access hierarchy for user_id: {user_id}",
            )
            return {
                "user_code": user_id,
                "sync_status": "failed",
            }

    except Exception as e:
        logger.error(f"❌ Error syncing user access hierarchy: {e}")
        raise
