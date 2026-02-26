"""
Health Check & App Status API Tests
=====================================
Tests for the /health and /maintenance-status endpoints.
Routes are registered inline via AppStatusEndpoints in src/app/routes.py.

The health/maintenance routes are added inline to the app (not via a router),
so we build a minimal test app here rather than relying on async_api_client.

Run: PYTHONPATH=. uv run pytest -m unit tests/app/test_health_api.py -v
"""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

pytestmark = pytest.mark.unit


@pytest.fixture
def health_app():
    """Minimal FastAPI app with only health & maintenance routes registered."""
    from src.app.routes import AppStatusEndpoints
    app = FastAPI()
    AppStatusEndpoints.app_health_status_check(app)
    AppStatusEndpoints.app_maintenance_status_check(app)
    return app


@pytest.fixture
async def health_client(health_app):
    """Async httpx client pointed at the minimal health app."""
    async with AsyncClient(
        transport=ASGITransport(app=health_app), base_url="http://test"
    ) as client:
        yield client


class TestHealthCheck:
    """Tests for GET /health"""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, health_client):
        """GET /health must return HTTP 200."""
        response = await health_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_returns_healthy_status(self, health_client):
        """GET /health must return JSON body with status=healthy."""
        response = await health_client.get("/health")
        data = response.json()
        assert data.get("status") == "healthy"

    @pytest.mark.asyncio
    async def test_health_response_is_json(self, health_client):
        """GET /health must return Content-Type: application/json."""
        response = await health_client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")


class TestMaintenanceStatus:
    """Tests for GET /maintenance-status"""

    @pytest.mark.asyncio
    async def test_maintenance_status_returns_200(self, health_client):
        """GET /maintenance-status returns 200 even if status service is unavailable."""
        response = await health_client.get("/maintenance-status")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_maintenance_status_has_maintenance_mode_key(self, health_client):
        """GET /maintenance-status response must include a maintenance_mode key."""
        response = await health_client.get("/maintenance-status")
        data = response.json()
        assert "maintenance_mode" in data


class TestHealthIntegration:
    """Integration tests for health endpoints against real app."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_returns_200_real(self, real_api_client):
        """GET /health against real running app returns 200."""
        response = await real_api_client.get("/health")
        assert response.status_code == 200
        assert response.json().get("status") == "healthy"
