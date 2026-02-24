from dynaconf import Dynaconf
import os

# Define the project root (backend/fastapi_core_base)
# The current file is at src/shared/config.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))

CONFIG_DIR = os.path.join(PROJECT_ROOT, "toml_config")

settings = Dynaconf(
    envvar_prefix="APP",  # Allows overriding via APP_VARNAME
    settings_files=[
        os.path.join(CONFIG_DIR, "settings.toml"),
        os.path.join(CONFIG_DIR, "logging.toml"),
        os.path.join(CONFIG_DIR, "datadog.toml"),
        os.path.join(CONFIG_DIR, ".secrets.toml"),
    ],
    # Add support for client-specific configuration in the toml_config/clients folder
    includes=[os.path.join(CONFIG_DIR, "clients/*.toml")],
    environments=True,
    load_dotenv=True,
)

# Export the settings object
__all__ = ["settings"]
