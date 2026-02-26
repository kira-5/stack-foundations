from src.shared.configuration.config import env_config_manager


def get_adbc_connection_url() -> str:
    """Returns the connection URL for ADBC (standard postgres scheme)."""
    return (
        f"postgresql://{env_config_manager.environment_settings.DB_USER}:"
        f"{env_config_manager.environment_settings.DB_PASSWORD}@"
        f"{env_config_manager.environment_settings.DB_HOST}:"
        f"{env_config_manager.environment_settings.DB_PORT}/"
        f"{env_config_manager.environment_settings.DB_NAME}"
    )
