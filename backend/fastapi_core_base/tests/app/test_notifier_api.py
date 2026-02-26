import pytest
from unittest.mock import patch

pytestmark = pytest.mark.unit

@pytest.mark.asyncio
async def test_get_notifier_settings_returns_200(async_api_client):
    """
    69: GET /notifier test endpoint returns 200.
    """
    response = await async_api_client.get("/api/v1/notifier")
    # This route exists in src/shared/notifier/routes.py
    assert response.status_code == 200

@pytest.mark.integration
@pytest.mark.asyncio
async def test_notifier_real_config_dry_run(real_api_client):
    """
    70: GET /notifier with dry_run=True against real config.
    """
    response = await real_api_client.get("/api/v1/notifier?dry_run=true")
    assert response.status_code == 200
    data = response.json()
    assert data["dry_run"] is True
    assert "config_used" in data
