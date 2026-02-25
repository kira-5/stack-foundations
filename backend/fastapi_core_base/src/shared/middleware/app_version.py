from async_lru import alru_cache
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.shared.configuration.config import env_config_manager
from src.shared.configuration import constants as core_constants
from src.shared.configuration import response


@alru_cache(ttl=60)
async def get_app_version():
    # query = um_queries.APP_VERSION_QUERY
    # data = await database_service.execute_transactional_query(query)
    # return data[0]["remarks"]
    return "1.0.0"


class AppversionMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        client_name = env_config_manager.get_dynamic_setting(
            "CLIENT_NAME",
            "default-client",
        )
        # Skip version check for WebSocket connections and local development
        if (
            request.headers.get("upgrade") == "websocket"
            or not request.headers.get("origin")
            or not request.headers["origin"].startswith(
                f"https://{client_name}.devs.impactsmartsuite.com",
            )
        ):
            return await call_next(request)
            excluded_routes = [
                f"{core_constants.API_PREFIX}/login",
                f"{core_constants.API_PREFIX}/samlCustomLogin",
                f"{core_constants.API_PREFIX}/register",
                f"{core_constants.API_PREFIX}/logout",
                f"{core_constants.API_PREFIX}/sse-output",
                f"{core_constants.API_PREFIX}/notifications/ws",
                f"{core_constants.API_PREFIX}/notifications/system/websocket-test",
                f"{core_constants.API_PREFIX}/notifications/system/health",
                f"{core_constants.API_PREFIX}/notifications/system/stats",
            ]
            if request.url.path not in excluded_routes:
                app_version = request.headers.get(core_constants.APP_VERSION)
                if request.method != "OPTIONS":
                    latest_appversion = await get_app_version()
                    if str(app_version) != str(latest_appversion):
                        return response.BaseJSONResponse(
                            status=418,
                            success=core_constants.FAILURE_FLAG,
                            user_id=None,
                            message=core_constants.APP_VERSION_MISMATCH_MESSAGE,
                            data=[],
                            error=[],
                        )

        return await call_next(request)
