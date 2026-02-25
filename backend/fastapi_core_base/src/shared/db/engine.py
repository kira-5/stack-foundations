# app/database/engine.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.configuration.config import env_config_manager

# Connection details
DATABASE_URL = (
    f"postgresql://{env_config_manager.environment_settings.DB_USER}:"
    f"{env_config_manager.environment_settings.DB_PASSWORD}@"
    f"{env_config_manager.environment_settings.DB_HOST}:"
    f"{env_config_manager.environment_settings.DB_PORT}/"
    f"{env_config_manager.environment_settings.DB_NAME}"
)

# Create the SQLAlchemy async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a configured "Session" class
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
