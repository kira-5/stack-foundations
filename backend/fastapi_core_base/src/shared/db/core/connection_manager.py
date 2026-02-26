import asyncio
import typing
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.shared.configuration.config import env_config_manager


class PostgresConnection:
    """Common database connection manager for asyncpg, aiopg, and SQLAlchemy."""

    # Internal clients and pools
    database_driver: str | None = None
    _asyncpg_pool: asyncpg.Pool | None = None
    _sqlalchemy_engine: typing.Any | None = None
    AsyncSessionLocal: async_sessionmaker | None = None

    @classmethod
    def init_connection_strings(cls, database_driver):
        """Initialize the connection strings based on environment settings."""
        cls.database_driver = database_driver
        
        # Support both legacy direct fields and new centralized configuration
        db_user = env_config_manager.get_dynamic_setting("DB_USER", "postgres")
        db_pass = env_config_manager.get_dynamic_setting("DB_PASSWORD", "postgres")
        db_host = env_config_manager.get_dynamic_setting("DB_HOST", "localhost")
        db_port = env_config_manager.get_dynamic_setting("DB_PORT", "5432")
        db_name = env_config_manager.get_dynamic_setting("DB_NAME", "postgres")

        cls.connection_url_asyncpg = (
            f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        )
        cls.connection_url_sqlalchemy = (
            f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        )

    @classmethod
    def initialize(cls, database_driver):
        """Call this method during app startup to set up the connection strings."""
        cls.init_connection_strings(database_driver)

    @classmethod
    async def get_asyncpg_pool(cls):
        """Retrieve or create an asyncpg connection pool."""
        if cls._asyncpg_pool is None:
            try:
                pool_min = int(env_config_manager.get_dynamic_setting("DB_POOL_MIN_SIZE", 1))
                pool_max = int(env_config_manager.get_dynamic_setting("DB_POOL_MAX_SIZE", 5))
                cls._asyncpg_pool = await asyncpg.create_pool(
                    cls.connection_url_asyncpg,
                    min_size=pool_min,
                    max_size=pool_max,
                    max_inactive_connection_lifetime=300,
                )
                print("Postgres asyncpg pool created.")
            except Exception as e:
                print(f"Error creating asyncpg pool: {str(e)}")
                raise
        return cls._asyncpg_pool

    @classmethod
    async def get_sqlalchemy_engine(cls):
        """Retrieve or create a SQLAlchemy engine."""
        if cls._sqlalchemy_engine is None:
            try:
                sa_pool_size = int(env_config_manager.get_dynamic_setting("DB_SA_POOL_SIZE", 2))
                sa_max_overflow = int(env_config_manager.get_dynamic_setting("DB_SA_MAX_OVERFLOW", 3))
                cls._sqlalchemy_engine = create_async_engine(
                    cls.connection_url_sqlalchemy,
                    echo=False,  # default to False for prod hygiene
                    pool_size=sa_pool_size,
                    max_overflow=sa_max_overflow,
                    pool_pre_ping=True,
                )
                print("Postgres SQLAlchemy engine created.")
            except Exception as e:
                print(f"Error creating SQLAlchemy engine: {str(e)}")
                raise
        return cls._sqlalchemy_engine

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """Get a connection based on the selected database type."""
        if cls.database_driver == "asyncpg":
            pool = await cls.get_asyncpg_pool()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    try:
                        yield conn
                    except Exception as e:
                        print(f"Error during database operation with asyncpg: {str(e)}")
                        raise
        elif cls.database_driver == "sqlalchemy":
            engine = await cls.get_sqlalchemy_engine()
            if cls.AsyncSessionLocal is None:
                cls.AsyncSessionLocal = async_sessionmaker(
                    bind=engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                )
            async with cls.AsyncSessionLocal() as session:
                try:
                    yield session
                    await session.commit()  # Commit transaction on success
                except Exception as e:
                    await session.rollback()
                    print(
                        f"Error during database operation with SQLAlchemy: {str(e)}",
                    )
                    raise
        else:
            raise ValueError(f"Unsupported database type specified: {cls.database_driver}")



    @classmethod
    async def get_pool_status(cls) -> dict:
        """Returns the current status of the database connection pools."""
        status = {
            "asyncpg": {"active": False, "size": 0, "free": 0},
            "sqlalchemy": {"active": False},
        }

        if cls._asyncpg_pool:
            status["asyncpg"] = {
                "active": True,
                "size": cls._asyncpg_pool.get_size(),
                "free": cls._asyncpg_pool.get_idle_size(),
                "min_size": cls._asyncpg_pool.get_min_size(),
                "max_size": cls._asyncpg_pool.get_max_size(),
            }

        if cls._sqlalchemy_engine:
            status["sqlalchemy"] = {
                "active": True,
                "pool_size": cls._sqlalchemy_engine.pool.size(),
                "checked_out": cls._sqlalchemy_engine.pool.checkedout(),
                "overflow": cls._sqlalchemy_engine.pool.overflow(),
            }

        return status

    @classmethod
    async def close(cls):
        """Close all database connections."""
        tasks = []
        if cls._asyncpg_pool is not None:
            tasks.append(cls._asyncpg_pool.close())
            cls._asyncpg_pool = None
            print("Postgres asyncpg pool closed.")

        if cls._sqlalchemy_engine is not None:
            tasks.append(cls._sqlalchemy_engine.dispose())
            cls._sqlalchemy_engine = None
            print("Postgres SQLAlchemy engine closed.")

        if tasks:
            await asyncio.gather(*tasks)  # Wait for all closing tasks
            print("All database connections closed.")
