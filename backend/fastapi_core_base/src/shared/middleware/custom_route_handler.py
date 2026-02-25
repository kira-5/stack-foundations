import time
from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute

from src.shared.services.logging_service import LoggingService

logger = LoggingService.get_logger(__name__)


class CustomRouteHandler(APIRoute):
    """Custom route handler for consistent logging and performance tracking."""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()
            response: Response = await original_route_handler(request)
            process_time = (time.time() - start_time) * 1000
            
            # Log performance metadata if needed
            logger.debug(
                f"Route {request.url.path} processed in {process_time:.2f}ms"
            )
            
            response.headers["X-Process-Time"] = str(process_time)
            return response

        return custom_route_handler
