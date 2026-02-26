import pytest

pytestmark = pytest.mark.integration

@pytest.mark.asyncio
async def test_transactional_real_select(real_db_service):
    """
    INTEGRATION: Connects to the real DB from .secrets.toml.
    Tests the full end-to-end flow of a simple SELECT.
    """
    result = await real_db_service.execute_transactional_query("SELECT 1 as test_val")
    assert len(result) == 1
    assert result[0]["test_val"] == 1


@pytest.mark.asyncio
async def test_transactional_real_batch_fetch(real_db_service):
    """
    INTEGRATION: Tests that batching works with real DB cursors.
    """
    # Generate 2500 rows and fetch in batches of 1000
    query = "SELECT generate_series(1, 2500) as id"
    batches = []
    
    async for batch in await real_db_service.execute_transactional_query(
        query, fetch_strategy="batch", batch_size=1000
    ):
        batches.append(batch)
        
    assert len(batches) == 3  # 1000 + 1000 + 500
    assert len(batches[0]) == 1000
    assert batches[0][0]["id"] == 1
