from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Internal Imports using the src-layout
from src.shared.config import settings
from src.shared.logging import setup_logging
from src.app.routes import api_router
from src.app.extensions.exception_handlers import add_exception_handlers


def create_app() -> FastAPI:
    """
    Application factory to initialize FastAPI with Dynaconf settings.
    """

    # Initialize logging facade
    setup_logging()
    app = FastAPI(
        title=settings.get("PROJECT_NAME", "FastAPI Core Base"),
        version=settings.get("VERSION", "1.0.0"),
        description="Modular Monolith with Multi-Client Support",
        # Ensures docs are only visible if enabled in the specific client.toml
        docs_url="/docs" if settings.get("SHOW_DOCS") else None,
        redoc_url="/redoc" if settings.get("SHOW_DOCS") else None,
    )

    # 1. Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get("CORS_ORIGINS", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Register Global Exception Handlers (Standardizing error responses)
    add_exception_handlers(app)

    # 3. Include Master Router (Contains Auth, Users, Ingestion, Cron, etc.)
    app.include_router(api_router)

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Basic health check for Cloud Run / Kubernetes."""
        return {
            "status": "healthy",
            "client": settings.current_env,  # Shows if client_a, client_b, etc. is active
            "version": settings.get("VERSION")
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    # This part allows running via 'python src/app/main.py'
    uvicorn.run(
        "src.app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )