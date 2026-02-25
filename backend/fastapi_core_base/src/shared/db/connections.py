import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from google.cloud import bigquery
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.shared.configuration.config import env_config_manager


class BigQueryConnection:
    """Manages BigQuery connections."""

    _big_query_client = None
    dataset: str = env_config_manager.environment_settings.BIQUERY_DATASET

    @classmethod
    def get_big_query_connection(cls):
        """Creates or retrieves a BigQuery client connection.

        :return: BigQuery client
        """
        if cls._big_query_client is None:
            project_id = env_config_manager.get_dynamic_setting(
                "PROJECT_ID",
                "default-project",
            )
            dataset = cls.dataset
            print(
                f"Creating BigQuery client with project id: {project_id} and dataset {dataset}",
            )
            cls._big_query_client = bigquery.Client(
                project=project_id,
            )
        return cls._big_query_client


class PostgresConnection:
    """Common database connection manager for asyncpg, aiopg, and SQLAlchemy."""

    # Internal clients and pools
    database_driver: Optional[str] = None
    _asyncpg_pool: Optional[asyncpg.Pool] = None
    _sqlalchemy_engine: Optional[any] = None
    AsyncSessionLocal: Optional[async_sessionmaker] = None

    @classmethod
    def init_connection_strings(cls, database_driver):
        """Initialize the connection strings based on environment settings."""
        cls.database_driver = database_driver
        cls.connection_url_asyncpg = (
            f"postgresql://{env_config_manager.environment_settings.DB_USER}:"
            f"{env_config_manager.environment_settings.DB_PASSWORD}@"
            f"{env_config_manager.environment_settings.DB_HOST}:"
            f"{env_config_manager.environment_settings.DB_PORT}/"
            f"{env_config_manager.environment_settings.DB_NAME}"
        )
        cls.connection_url_sqlalchemy = (
            f"postgresql+asyncpg://{env_config_manager.environment_settings.DB_USER}:"
            f"{env_config_manager.environment_settings.DB_PASSWORD}@"
            f"{env_config_manager.environment_settings.DB_HOST}:"
            f"{env_config_manager.environment_settings.DB_PORT}/"
            f"{env_config_manager.environment_settings.DB_NAME}"
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
                cls._asyncpg_pool = await asyncpg.create_pool(
                    cls.connection_url_asyncpg,
                    min_size=5,
                    max_size=20,
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
                cls._sqlalchemy_engine = create_async_engine(
                    cls.connection_url_sqlalchemy,
                    echo=True,
                    pool_size=10,
                    max_overflow=5,
                    pool_pre_ping=True,
                )
                print("Postgres SQLAlchemy engine created.")
            except Exception as e:
                print(f"Error creating SQLAlchemy engine: {str(e)}")
                raise
        return cls._sqlalchemy_engine

    @classmethod
    def get_adbc_connection_url(cls) -> str:
        """Returns the connection URL for ADBC (standard postgres scheme)."""
        return (
            f"postgresql://{env_config_manager.environment_settings.DB_USER}:"
            f"{env_config_manager.environment_settings.DB_PASSWORD}@"
            f"{env_config_manager.environment_settings.DB_HOST}:"
            f"{env_config_manager.environment_settings.DB_PORT}/"
            f"{env_config_manager.environment_settings.DB_NAME}"
        )

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
            raise ValueError("Unsupported database type specified.")

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
