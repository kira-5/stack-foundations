from fastapi import FastAPI, APIRouter
from src.shared.user_management.routes import user_management_router
from src.shared.notifier.routes import notifier_router
from src.shared.email_templates.routes import email_templates_router
from src.shared.slack_templates.routes import slack_templates_router

class RoutingAggregator:
    @staticmethod
    def include_routers(app: FastAPI):
        """Include all shared routers into the application."""
        app.include_router(user_management_router, prefix="/api/v1", tags=["User Management"])
        app.include_router(notifier_router, prefix="/api/v1", tags=["Notifier"])
        app.include_router(email_templates_router, prefix="/api/v1", tags=["Email Templates"])
        app.include_router(slack_templates_router, prefix="/api/v1", tags=["Slack Templates"])

class AppStatusEndpoints:
    @staticmethod
    def app_health_status_check(app: FastAPI):
        """Register the health check endpoint."""
        @app.get("/health", tags=["Monitoring"])
        async def health_check():
            return {"status": "healthy"}

    @staticmethod
    def app_maintenance_status_check(app: FastAPI):
        """Register the maintenance status endpoint."""
        @app.get("/maintenance-status", tags=["Monitoring"])
        async def maintenance_status():
            try:
                from src.shared.services.app_status_service import app_status_service
                status = await app_status_service.get_flag("app_maintenance")
                return {"maintenance_mode": status}
            except Exception:
                return {"maintenance_mode": False, "error": "Status service unavailable"}

api_routes = RoutingAggregator()
app_status_endpoints = AppStatusEndpoints()
api_router = APIRouter() # Keep for compatibility if needed
