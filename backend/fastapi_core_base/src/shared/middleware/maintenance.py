# app/extensions/maintenance.py

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.shared.services.database_service import database_service
from src.shared.services.redis_service import redis_service


class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if await self.is_maintenance():
            return Response("Service is under maintenance", status_code=503)
        return await call_next(request)

    @staticmethod
    async def is_maintenance():
        # 1. Check Redis first (fast path)
        redis_status = await redis_service.get_cache(
            key="app:maintenance:status",
            namespace="app_status",
        )
        # if redis_status is not None:
        #     return bool(redis_status)

        # 2. Fallback to DB if Redis missing or down
        query = """
            SELECT status FROM base_pricing.bp_app_status_master
            WHERE flag_name = 'app_maintenance'
            AND is_active = TRUE
        """
        res = await database_service.execute_transactional_query(query=query)

        if res and isinstance(res, list) and len(res) > 0:
            status = res[0].get("status")
            # Sync back to Redis as a lazy-load
            await redis_service.set_cache(
                key="app:maintenance:status",
                value=status,
                expire_seconds=86400,
                namespace="app_status",
            )
            return status

        return False
