import asyncio
from contextlib import asynccontextmanager

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
    _asyncpg_client = None
    _sqlalchemy_engine = None
    AsyncSessionLocal = None

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
    async def get_asyncpg_connection(cls):
        """Retrieve or create an asyncpg connection."""
        if cls._asyncpg_client is None or cls._asyncpg_client.is_closed():
            try:
                cls._asyncpg_client = await asyncpg.connect(cls.connection_url_asyncpg)
            except asyncpg.PostgresError as e:
                print(f"Error connecting to PostgreSQL with asyncpg: {str(e)}")
                raise
            except Exception as e:
                print(f"Error connecting to PostgreSQL with asyncpg: {str(e)}")
                raise
        return cls._asyncpg_client

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
            except Exception as e:
                print(f"Error creating SQLAlchemy engine: {str(e)}")
                raise
        return cls._sqlalchemy_engine

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """Get a connection based on the selected database type."""
        if cls.database_driver == "asyncpg":
            conn = await cls.get_asyncpg_connection()
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
    async def close(cls):
        """Close all database connections."""
        tasks = []
        if cls._asyncpg_client is not None:
            tasks.append(cls._asyncpg_client.close())
            cls._asyncpg_client = None
            print("Postgres asyncpg connection closed.")

        if cls._sqlalchemy_engine is not None:
            tasks.append(cls._sqlalchemy_engine.dispose())
            cls._sqlalchemy_engine = None
            print("Postgres SQLAlchemy engine closed.")

        await asyncio.gather(*tasks)  # Wait for all closing tasks
        print("All database connections closed.")
