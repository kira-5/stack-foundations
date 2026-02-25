"""Routes for User Management module.

This module provides API endpoints for user access control operations.
"""

from fastapi import APIRouter, HTTPException, Request

from src.shared.configuration import constants as core_constants
from src.shared.configuration import utils as core_utils
from src.shared.middleware.custom_route_handler import CustomRouteHandler
from src.shared.services.logging_service import LoggingService
from src.shared.user_management import service as user_management_service
from src.shared.user_management import utils as um_utils

logger = LoggingService.get_logger(__name__)

user_management_router = APIRouter(route_class=CustomRouteHandler)


@user_management_router.post("/user-management/sync-hierarchy")
async def sync_user_access_hierarchy(
    request: Request,
):
    """Sync user access hierarchy for the authenticated user.

    Args:
        request: FastAPI request object

    Returns:
        Response with sync results
    """
    # Get user_id
    try:
        user_id = um_utils.get_user_id(request)
    except Exception as e:
        logger.error(f"❌ Error getting user_id: {e}")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized - Could not get user_id",
        )

    logger.info(f"🔄 Sync hierarchy request for user_id: {user_id}")

    try:
        # Call service layer
        result = await user_management_service.sync_user_access_hierarchy_service(
            user_id=user_id,
        )

        return core_utils.generate_json_response(
            status=core_constants.STATUS_SUCCESS,
            success=core_constants.SUCCESS_FLAG,
            user_id=user_id,
            message=f"User access hierarchy synced successfully for user_code: {user_id}",
            data=result,
        )

    except Exception as e:
        logger.error(f"❌ Error in sync hierarchy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sync hierarchy failed: {str(e)}",
        )


@user_management_router.get("/user-access-details")
async def get_user_access_details(
    request: Request,
):
    """Get user access details with module actions.

    This endpoint retrieves module-level actions with access control.

    Args:
        request: FastAPI request object

    Returns:
        Response with user access details including module_actions
    """
    # Get user_id
    try:
        user_id = um_utils.get_user_id(request)
    except Exception as e:
        logger.error(f"❌ Error getting user_id: {e}")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized - Could not get user_id",
        )

    logger.info(f"📋 User access details request for user_id: {user_id}")

    try:
        # Call service layer
        result = await user_management_service.get_user_access_details_service(
            user_id=user_id,
        )

        return core_utils.generate_json_response(
            status=core_constants.STATUS_SUCCESS,
            success=core_constants.SUCCESS_FLAG,
            user_id=user_id,
            message="User access details retrieved successfully",
            data=result,
        )

    except Exception as e:
        logger.error(f"❌ Error getting user access details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user access details: {str(e)}",
        )
