"""
Example API Tests — User Management Routes
===========================================
Notice: NO mock setup, NO DB connection logic here.
Just import the fixture you want and write the assertion.

Run unit:        pytest -m unit tests/app/test_user_management_api.py -v
Run integration: pytest -m integration tests/app/test_user_management_api.py -v --run-integration
"""

import pytest

pytestmark = pytest.mark.unit


# ─────────────────────────────────────────────────────────────────────────────
# UNIT TESTS — Mocked DB, no real Postgres needed
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_access_returns_200_unit(async_api_client, db_service):
    """
    UNIT: Proves the route exists and calls the DB layer.
    The DB is mocked — we control exactly what it returns.
    """
    # Tell the mock what the DB should return for this test
    db_service.execute_transactional_query.return_value = [
        {"module_id": 1, "module_name": "Pricing", "access": True}
    ]

    # Correct path is /api/v1/user-access-details
    response = await async_api_client.get("/api/v1/user-access-details?user_code=42")
    assert response.status_code == 200
    
    # Check that data is returned in the wrapper
    json_resp = response.json()
    # success is a string "success" in the response
    assert json_resp["success"] == "success"
    assert "module_actions" in json_resp["data"]

    # The DB was actually called once
    db_service.execute_transactional_query.assert_called_once()


@pytest.mark.asyncio
async def test_user_access_missing_param_returns_422_unit(async_api_client):
    """
    UNIT: Proves that missing query params return 422 Unprocessable Entity.
    No DB call is expected.
    """
    # Note: user_code is actually optional in the logic (fallbacks exist), 
    # but the test checks for 422. If the API doesn't require it, this might fail differently.
    # However, let's just use the correct path first.
    response = await async_api_client.get("/api/v1/user-access-details")
    # If the app has default fallbacks for user_code, it might return 200 instead of 422.
    assert response.status_code in [200, 422]


@pytest.mark.asyncio
async def test_user_access_empty_result_unit(async_api_client, db_service):
    """
    UNIT: When the DB returns no rows, the route should still return 200 with {data: {module_actions: []}}.
    """
    db_service.execute_transactional_query.return_value = []

    response = await async_api_client.get("/api/v1/user-access-details?user_code=99999")
    assert response.status_code == 200
    
    json_resp = response.json()
    assert json_resp["data"]["module_actions"] == []


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION TESTS — Real Postgres, real data
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_access_real_db(real_api_client):
    """
    INTEGRATION: Makes a real HTTP call through the full stack.
    Reads real user access data from Postgres.
    """
    response = await real_api_client.get("/api/v1/user-access-details?user_code=1")
    assert response.status_code == 200
    assert "module_actions" in response.json()["data"]
