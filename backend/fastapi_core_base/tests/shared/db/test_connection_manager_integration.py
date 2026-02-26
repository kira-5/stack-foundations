import pytest
from src.shared.db.core.connection_manager import PostgresConnection
from src.shared.configuration.config import env_config_manager

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_connection_returns_valid_asyncpg(real_db_service):
    """
    61: get_connection() returns a valid asyncpg connection.
    """
    async with await PostgresConnection.get_connection() as conn:
        assert conn is not None
        # Verify it's a real asyncpg connection by running a simple query
        res = await conn.fetchval("SELECT 1")
        assert res == 1

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pool_initialization_matches_centralized_config():
    """
    62 & 63: Pool initializes correctly using databases.toml and matches pool sizes.
    """
    # Force re-initialization to ensure it picks up config
    await PostgresConnection.close()
    PostgresConnection.initialize(database_driver="asyncpg")
    
    # Trigger pool creation
    pool = await PostgresConnection.get_asyncpg_pool()
    assert pool is not None
    
    # Check pool sizes from databases.toml
    expected_min = int(env_config_manager.get_dynamic_setting("DB_POOL_MIN_SIZE", 1))
    expected_max = int(env_config_manager.get_dynamic_setting("DB_POOL_MAX_SIZE", 5))
    
    # Access private pool attributes for verification
    assert pool._minsize == expected_min
    assert pool._maxsize == expected_max

@pytest.mark.integration
@pytest.mark.asyncio
async def test_connection_manager_close_cleans_up():
    """
    64: close() (formerly close_all) closes pool without errors.
    """
    PostgresConnection.initialize(database_driver="asyncpg")
    await PostgresConnection.get_asyncpg_pool()
    
    # Close it
    await PostgresConnection.close()
    
    # Verify pool is None
    assert PostgresConnection._asyncpg_pool is None
    assert PostgresConnection._sqlalchemy_engine is None
