from fastapi.responses import JSONResponse
from typing import Any, Optional

class BaseJSONResponse(JSONResponse):
    """
    Standardized JSON response for all API endpoints.
    """
    def __init__(
        self,
        status: int,
        success: str,
        message: str,
        data: Any = None,
        user_id: Optional[str] = None,
        error: Optional[dict] = None,
        **kwargs
    ) -> None:
        content = {
            "status": status,
            "success": success,
            "message": message,
            "user_id": user_id,
            "data": data if data is not None else [],
            "error": error if error is not None else {}
        }
        super().__init__(content=content, status_code=status, **kwargs)
