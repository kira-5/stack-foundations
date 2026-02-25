from src.shared.configuration.response import BaseJSONResponse
from typing import Any, Optional

def generate_json_response(
    status: int,
    success: str,
    user_id: Optional[str],
    message: str,
    data: Any = None,
    error: Optional[dict] = None,
) -> BaseJSONResponse:
    """
    Generate a standardized JSON response.
    """
    return BaseJSONResponse(
        status=status,
        success=success,
        user_id=user_id,
        message=message,
        data=data,
        error=error,
    )
