from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.shared.configuration.config import env_config_manager


def get_asyncpg_pool_kwargs(dsn: str) -> dict:
    """Asyncpg connection builder arguments."""
    pool_min = int(env_config_manager.get_dynamic_setting("DB_POOL_MIN_SIZE", 1))
    pool_max = int(env_config_manager.get_dynamic_setting("DB_POOL_MAX_SIZE", 5))
    return {
        "dsn": dsn,
        "min_size": pool_min,
        "max_size": pool_max,
        "max_inactive_connection_lifetime": 300,
    }

def get_sqlalchemy_engine_factory(url: str):
    """SQLAlchemy engine builder factory."""
    sa_pool_size = int(env_config_manager.get_dynamic_setting("DB_SA_POOL_SIZE", 2))
    sa_max_overflow = int(env_config_manager.get_dynamic_setting("DB_SA_MAX_OVERFLOW", 3))
    return create_async_engine(
        url,
        echo=False,  # default to False for prod hygiene
        pool_size=sa_pool_size,
        max_overflow=sa_max_overflow,
        pool_pre_ping=True,
    )

def get_sqlalchemy_sessionmaker(engine):
    """SQLAlchemy sessionmaker factory."""
    from sqlalchemy.ext.asyncio import AsyncSession
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
