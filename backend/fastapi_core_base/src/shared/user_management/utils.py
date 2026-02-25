import os
from dataclasses import dataclass
from typing import Any

from fastapi import Request

from src.shared.services.logging_service import LoggingService
from src.shared.user_management import constants as user_management_constants
from src.shared.user_management.constants import Environment, UserIDSource

# Create logger instance at module level
logger = LoggingService.get_logger(__name__)


@dataclass
class UserContext:
    """Data class to hold user context information."""

    user_id: int
    request_id: str
    source: UserIDSource


def get_current_environment() -> Environment:
    """Determine the current environment."""

    env = os.getenv("env", user_management_constants.DEFAULT_ENV).lower()
    return Environment.LOCAL if env in user_management_constants.LOCAL_ENVIRONMENTS else Environment.PRODUCTION


def get_request_context(request: Request | None = None) -> dict[str, Any]:
    """Extract context information from the request."""

    return {
        "request_id": (
            getattr(
                request.state,
                "request_id",
                user_management_constants.DEFAULT_REQUEST_ID,
            )
            if request
            else user_management_constants.DEFAULT_REQUEST_ID
        ),
    }


def get_user_id_from_environment(context: dict[str, Any]) -> UserContext:
    """Retrieve user ID from environment variables."""

    user_id = int(os.getenv("USER_ID", str(user_management_constants.FALLBACK_USER_ID)))
    return UserContext(
        user_id=user_id,
        request_id=context["request_id"],
        source=UserIDSource.ENVIRONMENT,
    )


def get_user_id_from_request(request: Request, context: dict[str, Any]) -> UserContext:
    """Retrieve user ID from request state."""

    return UserContext(
        user_id=request.state.user_id,
        request_id=context["request_id"],
        source=UserIDSource.REQUEST,
    )


def get_fallback_user_id(context: dict[str, Any]) -> UserContext:
    """Get fallback user ID when other methods fail."""

    return UserContext(
        user_id=user_management_constants.FALLBACK_USER_ID,
        request_id=context["request_id"],
        source=UserIDSource.FALLBACK,
    )


def get_user_id(request: Request | None = None) -> int:
    """Retrieve the user ID from the request, or use fallback if not available."""

    context = get_request_context(request)
    current_env = get_current_environment()

    try:
        if current_env == Environment.LOCAL:
            user_context = get_user_id_from_environment(context)
        elif request is not None and hasattr(request.state, "user_id"):
            user_context = get_user_id_from_request(request, context)
        else:
            user_context = get_fallback_user_id(context)

        logger.debug(
            "User ID retrieved from %s",
            user_context.source.value,
            extra={
                "request_id": user_context.request_id,
                "user_id": user_context.user_id,
                "source": user_context.source.value,
            },
        )

        return user_context.user_id

    except (ValueError, AttributeError) as exc:
        logger.error(
            "Error retrieving user ID: %s",
            str(exc),
            extra={
                "request_id": context["request_id"],
            },
        )
        return user_management_constants.FALLBACK_USER_ID


def is_local_environment() -> bool:
    """Check if current environment is local."""

    return get_current_environment() == Environment.LOCAL
