import json
import os
from pathlib import Path
from typing import Any

import toml
from dotenv import load_dotenv
from dynaconf import Dynaconf

from src.shared.configuration import constants as config_constants
from src.shared.configuration import (
    email_notification_secret_manager,
    gcp_secret_manager,
    mtp_secret_manager,
)
from src.shared.services.logging_service import LoggingService

logger = LoggingService.get_logger(__name__)


class EnvConfigManager:
    """Class to manage application configuration and secrets loading."""

    MTP_SECRET_KEYS = config_constants.MTP_SECRET_KEYS
    GCP_SECRET_KEYS = config_constants.GCP_SECRET_KEYS
    EMAIL_NOTIFICATION_SECRET_KEYS = config_constants.EMAIL_NOTIFICATION_SECRET_KEYS

    def __init__(self):
        load_dotenv()
        self.environment = os.getenv("env", "local")
        self.dynaconf_env = f"base-pricing-{self.environment}"
        # DD_TRACE_AGENT_URL and DD_VERSION are now read from datadog.toml via get_dynamic_setting()
        # Keep dd_trace_agent_url for backward compatibility (fallback to env var)
        self.dd_trace_agent_url = os.getenv("DD_TRACE_AGENT_URL", None)

        # matches: backend/src/shared/configuration/config.py -> ../../../../toml_config
        self.configfilebasepath = Path(__file__).resolve().parent.parent.parent.parent / "toml_config"

        # Initialize dynamic client configuration support
        self.current_tenant = None
        self.current_environment = None
        self.current_client_config = None
        self.clients_dir = self.configfilebasepath / "clients"
        self.clients_dir.mkdir(parents=True, exist_ok=True)

        self.environment_settings = self.initialize_dynaconf()

        # Initialize secret loaders as None - they will be created when needed
        self.gcp_secret_loader = None
        self.mtp_secret_loader = None
        self.email_notification_secret_loader = None

        logger.debug(
            f"EnvConfigManager initialized with clients_dir: {self.clients_dir}",
        )

    def initialize_dynaconf(self):
        """Initialize Dynaconf with settings, secrets, and client files."""

        # Step 1: Load settings.toml and .secrets.toml first to get TENANT_NAME
        initial_settings = Dynaconf(
            settings_files=["settings.toml", ".secrets.toml"],
            root_path=str(self.configfilebasepath),
            env_file=".env",
            environments=True,
            load_dotenv=True,
            default_env="DEFAULT",
            env=self.dynaconf_env,
            env_switcher="ENV_FOR_DYNACONF",
            lowercase_read=True,
            redis_enabled=True,
        )
        initial_settings.setenv(self.dynaconf_env)

        # Step 2: Get TENANT_NAME to determine which client file to load
        tenant_name = (
            os.getenv("CLIENT_NAME")
            or os.getenv("TENANT_ID")
            or os.getenv("TENANT_NAME")
            or initial_settings.get("TENANT_NAME")
        )

        # Step 3: Load only the matching client file (not all files)
        # clients_dir is already set correctly in __init__
        client_files = []
        if tenant_name and self.clients_dir.exists():
            # Try to find the matching client file
            client_file = self.clients_dir / f"{tenant_name}.toml"
            if client_file.exists():
                client_files = [str(client_file)]
                logger.debug(
                    f"Loading client file for tenant '{tenant_name}': {client_file}",
                )
            else:
                # Fallback: search for file with matching TENANT_ID in content
                for config_file in self.clients_dir.glob("*.toml"):
                    try:
                        config = self._load_toml_file(config_file)
                        if config.get("DEFAULT", {}).get("TENANT_ID") == tenant_name:
                            client_files = [str(config_file)]
                            logger.debug(
                                f"Found client file with matching TENANT_ID: {config_file}",
                            )
                            break
                    except Exception:
                        continue

        # Step 4: Combine all settings files (only the matching client file).
        # Load .secrets.toml LAST so it overrides client config (e.g. NOTIFIER_*_SLACK_WEBHOOK_URL).
        settings_files = (
            [
                "settings.toml",
                "logging.toml",
                "datadog.toml",
            ]
            + client_files
            + [".secrets.toml"]
        )

        logger.debug(
            f"Loading Dynaconf with files: {settings_files} from {self.configfilebasepath}",
        )

        settings = Dynaconf(
            settings_files=settings_files,
            root_path=str(self.configfilebasepath),
            env_file=".env",
            environments=True,
            load_dotenv=True,
            default_env="DEFAULT",
            env=self.environment,
            env_switcher="ENV_FOR_DYNACONF",
            lowercase_read=True,
            redis_enabled=True,
        )
        settings.setenv(self.environment)
        settings.ENVIRONMENT = self.environment
        return settings

    def initialize_gcp_secret_loader(self):
        """Initialize the Google Secret Loader for fetching secrets."""
        # Use dynamic configuration to get the secret name
        secret_name = self.get_dynamic_setting("GOOGLE_SECRET_NAME", "default_secret")
        return self._initialize_secret_loader(
            gcp_secret_manager.GoogleSecretManagerLoader,
            secret_name,
        )

    def initialize_mtp_secret_loader(self):
        """Initialize the MTP Secret Loader for fetching secrets."""
        return self._initialize_secret_loader(
            mtp_secret_manager.MtpSecretsManagerLoader,
            self.environment_settings.MTP_SECRET_NAME,
        )

    def initialize_email_notification_secret_loader(self):
        """Initialize the Notification Email Secret Loader for fetching secrets."""
        return self._initialize_secret_loader(
            email_notification_secret_manager.EmailNotificationSecretManagerLoader,
            self.environment_settings.EMAIL_NOTIFICATION_SECRET_NAME,
        )

    def get_gcp_secret_loader(self):
        """Get GCP secret loader with lazy initialization."""
        if self.gcp_secret_loader is None:
            self.gcp_secret_loader = self.initialize_gcp_secret_loader()
        return self.gcp_secret_loader

    def get_mtp_secret_loader(self):
        """Get MTP secret loader with lazy initialization."""
        if self.mtp_secret_loader is None:
            self.mtp_secret_loader = self.initialize_mtp_secret_loader()
        return self.mtp_secret_loader

    def get_email_notification_secret_loader(self):
        """Get email notification secret loader with lazy initialization."""
        if self.email_notification_secret_loader is None:
            self.email_notification_secret_loader = self.initialize_email_notification_secret_loader()
        return self.email_notification_secret_loader

    def _initialize_secret_loader(self, loader_class, secret_name):
        """Helper method to initialize a secret loader."""
        # Use dynamic configuration for client-specific settings
        project_id = self.get_dynamic_setting("PROJECT_ID", "default-project")
        project_number = self.get_dynamic_setting("PROJECT_NUMBER", "123456789012")
        secret_version = self.environment_settings.get("SECRET_VERSION", "latest")
        env = self.environment_settings.get("DEPLOYMENT_ENV", "dev")

        if not project_id:
            raise ValueError("PROJECT_ID must be set in the environment.")

        return loader_class(
            project_id,
            project_number,
            secret_name,
            secret_version,
            env,
        )

    async def fetch_secrets_and_update_env_settings(self):
        """Fetch secrets from secret managers and update Dynaconf settings."""
        gcp_secret_config = await self.get_gcp_secret_loader().fetch_secrets_from_gcp()
        mtp_secret_config = await self.get_mtp_secret_loader().fetch_secrets_from_mtp()
        email_notification_secret_config = await (
            self.get_email_notification_secret_loader().fetch_secrets_from_email_notification()
        )

        env_conf = self._load_dynaconf_settings()
        env_conf.update(
            self._process_secret_config(gcp_secret_config, self.GCP_SECRET_KEYS),
        )
        env_conf.update(
            self._process_secret_config(mtp_secret_config, self.MTP_SECRET_KEYS),
        )
        env_conf.update(
            self._process_secret_config(
                email_notification_secret_config,
                self.EMAIL_NOTIFICATION_SECRET_KEYS,
            ),
        )

        os.environ.update(env_conf)
        return env_conf

    def _load_dynaconf_settings(self):
        """Load settings from Dynaconf into a dictionary."""
        env_conf = {}
        for key in self.environment_settings.keys():
            value = self.environment_settings[key]
            if isinstance(value, (str, bool)):
                env_conf[key.upper()] = str(value)
        return env_conf

    def _process_secret_config(self, db_config, secret_keys):
        """Process secret configuration JSON and update environment settings."""
        env_conf = {}
        if db_config:
            try:
                db_config_dict = json.loads(db_config)
                for key in secret_keys:
                    self._update_env_conf(env_conf, db_config_dict, key)
            except json.JSONDecodeError:
                logger.error("Failed to decode configuration JSON.")
        else:
            logger.warning("Configuration JSON not found in Secret Manager.")
        return env_conf

    def _update_env_conf(self, env_conf, db_config_dict, key):
        """Update environment configuration with secret values."""
        key_upper = key.upper()

        # Check if the key exists in Secret Manager response
        value = db_config_dict.get(key) or db_config_dict.get(key_upper)

        if value is not None:
            # IMPORTANT: In local environment, do NOT overwrite if already set (e.g., in .secrets.toml)
            if self.environment == "local" or "-local" in self.environment:
                existing_value = getattr(self.environment_settings, key_upper, None)
                if existing_value is not None:
                    logger.debug(
                        f"Skipping cloud secret overwrite for `{key_upper}` "
                        f"as it is already set locally to: {existing_value}",
                    )
                    return

            self.environment_settings[key_upper] = value
            env_conf[key_upper] = str(value)
        else:
            # Optional keys may not be present in all environments - log as debug instead of print
            logger.debug(
                f"Optional key `{key}` not found in JSON configuration " "(this is normal if not needed).",
            )

        # Normalization: Map DEPLOY_ENV -> DEPLOYMENT_ENV
        # Cloud Run / Secrets provide DEPLOY_ENV, but app uses DEPLOYMENT_ENV
        if key == "DEPLOY_ENV" and "DEPLOYMENT_ENV" not in env_conf:
            value = db_config_dict.get(key)
            if value:
                self.environment_settings["DEPLOYMENT_ENV"] = value
                env_conf["DEPLOYMENT_ENV"] = str(value)
                logger.debug(
                    f"Mapped DEPLOY_ENV ({value}) to DEPLOYMENT_ENV for consistency.",
                )

    # def _process_email_notification_config(self, email_config):
    #     """Store email notification credentials in global config."""
    #     env_conf = {}
    #     if email_config:
    #         try:
    #             email_config_dict = json.loads(email_config)
    #             self.notification_email_credentials = email_config_dict
    #             self.environment_settings.NOTIFICATION_EMAIL_CREDENTIALS = (
    #                 email_config_dict
    #             )
    #             env_conf["NOTIFICATION_EMAIL_CREDENTIALS"] = json.dumps(
    #                 email_config_dict,
    #             )
    #             for key in self.EMAIL_NOTIFICATION_SECRET_KEYS:
    #                 self._update_env_conf(env_conf, email_config_dict, key)
    #         except json.JSONDecodeError:
    #             print("Failed to decode notification email configuration JSON.")
    #     else:
    #         print("Notification email configuration JSON not found in Secret Manager.")
    #     return env_conf

    def load_dynamic_client_config(
        self,
        tenant_id: str,
        environment: str,
    ) -> dict[str, Any]:
        """Load client configuration based on tenant ID and environment.

        Args:
            tenant_id: The tenant identifier
            environment: The deployment environment

        Returns:
            Dict containing the client configuration
        """
        logger.debug(
            f"Loading dynamic client config for tenant: {tenant_id}, environment: {environment}",
        )

        # Try to find client configuration file
        client_file = self._find_client_file(tenant_id)

        if not client_file:
            logger.warning(f"No client configuration found for tenant: {tenant_id}")
            return self._get_default_client_config(tenant_id, environment)

        try:
            # Load client configuration
            client_config = self._load_toml_file(client_file)
            logger.debug(f"Loaded client config from: {client_file}")

            # Process template variables
            processed_config = self._process_template_variables(
                client_config,
                tenant_id,
                environment,
            )

            # Store current configuration
            self.current_client_config = processed_config
            self.current_tenant = tenant_id
            self.current_environment = environment

            logger.info(f"Client configuration loaded successfully for {tenant_id}")
            return processed_config

        except Exception as e:
            logger.error(f"Error loading client config for {tenant_id}: {e}")
            return self._get_default_client_config(tenant_id, environment)

    def _find_client_file(self, tenant_id: str) -> Path | None:
        """Find the appropriate client configuration file for the tenant."""

        # Method 1: Direct tenant ID match
        client_file = self.clients_dir / f"{tenant_id}.toml"
        if client_file.exists():
            logger.debug(f"Found direct client file: {client_file}")
            return client_file

        # Method 2: Look for files with matching tenant ID in content
        for config_file in self.clients_dir.glob("*.toml"):
            try:
                config = self._load_toml_file(config_file)
                if config.get("DEFAULT", {}).get("TENANT_ID") == tenant_id:
                    logger.debug(
                        f"Found client file with matching tenant ID: {config_file}",
                    )
                    return config_file
            except Exception as e:
                logger.warning(f"Error reading {config_file}: {e}")
                continue

        # Method 3: Use environment variable as fallback
        env_client = os.getenv("CLIENT_NAME")
        if env_client:
            client_file = self.clients_dir / f"{env_client}.toml"
            if client_file.exists():
                logger.debug(
                    f"Using fallback client file from environment: {client_file}",
                )
                return client_file

        logger.warning(f"No client configuration file found for tenant: {tenant_id}")
        return None

    def _load_toml_file(self, file_path: Path) -> dict[str, Any]:
        """Load and parse a TOML file."""
        try:
            with open(file_path) as f:
                return toml.load(f)
        except Exception as e:
            logger.error(f"Error loading TOML file {file_path}: {e}")
            raise

    def _process_template_variables(
        self,
        config: dict[str, Any],
        tenant_id: str,
        environment: str,
    ) -> dict[str, Any]:
        """Process template variables in the configuration."""

        processed_config = {}

        # Process DEFAULT section
        default_config = config.get("DEFAULT", {})
        for key, value in default_config.items():
            if isinstance(value, str) and value.startswith("@format {"):
                # Extract variable name from @format {VARIABLE_NAME}
                var_name = value[8:-1]  # Remove "@format {" and "}"
                processed_value = self._resolve_template_variable(
                    var_name,
                    tenant_id,
                    environment,
                )
                processed_config[key] = processed_value
            else:
                processed_config[key] = value

        # Process environment-specific section
        env_config = config.get(environment, {})
        for key, value in env_config.items():
            if isinstance(value, str) and value.startswith("@format {"):
                var_name = value[8:-1]
                processed_value = self._resolve_template_variable(
                    var_name,
                    tenant_id,
                    environment,
                )
                processed_config[key] = processed_value
            else:
                processed_config[key] = value

        # Add metadata
        processed_config["_metadata"] = {
            "tenant_id": tenant_id,
            "environment": environment,
            "config_source": "dynamic_client_config",
        }

        return processed_config

    def _resolve_template_variable(
        self,
        var_name: str,
        tenant_id: str,
        environment: str,
    ) -> str:
        """Resolve a template variable to its actual value."""

        # First, check if we have a current client config loaded
        if self.current_client_config:
            client_value = self.current_client_config.get(var_name)
            if client_value:
                logger.debug(
                    f"Resolved template variable {var_name} from client config = {client_value}",
                )
                return str(client_value)

        # Common variable mappings (fallback)
        variable_mappings = {
            "CLIENT_NAME": tenant_id,
            "TENANT_ID": tenant_id,
            "PROJECT_ID": f"{tenant_id}-project",
            "PROJECT_NUMBER": f"{tenant_id}-project-number",
            "PROJECT_NAME": f"{tenant_id}-project",
            "GOOGLE_SECRET_NAME": f"{tenant_id}_secret",
            "GCS_BUCKET": f"{tenant_id}_basesmart",
            "GUROBI_API_URL": f"http://gurobi-internal.iaproducts.ai:6673/solve_BaseSmart_{tenant_id}_{environment}/",
        }

        # Check if variable exists in mappings
        if var_name in variable_mappings:
            value = variable_mappings[var_name]
            logger.debug(
                f"Resolved template variable {var_name} from mappings = {value}",
            )
            return value

        # Check environment variables
        env_value = os.getenv(var_name)
        if env_value:
            logger.debug(
                f"Resolved template variable {var_name} from environment = {env_value}",
            )
            return env_value

        # Check existing config manager
        try:
            config_value = getattr(self.environment_settings, var_name, None)
            if config_value:
                logger.debug(
                    f"Resolved template variable {var_name} from config = {config_value}",
                )
                return str(config_value)
        except (AttributeError, Exception):
            pass

        # Return default value
        default_value = f"default_{var_name.lower()}"
        logger.warning(
            f"Template variable {var_name} not found, using default: {default_value}",
        )
        return default_value

    def _get_default_client_config(
        self,
        tenant_id: str,
        environment: str,
    ) -> dict[str, Any]:
        """Get default configuration when no client file is found."""

        logger.debug(f"Using default configuration for tenant: {tenant_id}")

        default_config = {
            "CLIENT_NAME": tenant_id,
            "TENANT_ID": tenant_id,
            "PROJECT_ID": f"{tenant_id}-project",
            "PROJECT_NUMBER": "123456789012",
            "PROJECT_NAME": f"{tenant_id}-project",
            "GOOGLE_SECRET_NAME": f"{tenant_id}_secret",
            "GCS_BUCKET": f"{tenant_id}_basesmart",
            "GUROBI_API_URL": f"http://gurobi-internal.iaproducts.ai:6673/solve_BaseSmart_{tenant_id}_{environment}/",
            "_metadata": {
                "tenant_id": tenant_id,
                "environment": environment,
                "config_source": "default_config",
            },
        }
        logger.debug(f"Default config: {default_config}")

        return default_config

    def get_dynamic_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting with the following priority:
        1. Environment Variables (os.getenv)
        2. Client Configuration (clients/*.toml)
        3. Environment Settings (settings.toml / .secrets.toml / Secrets)
        """

        # 1. First, check environment variables (Absolute Highest Priority)
        env_var_value = os.getenv(key) or os.getenv(key.upper())
        if env_var_value is not None:
            logger.debug(
                f"Getting setting {key} from environment variables = {env_var_value}",
            )
            return env_var_value

        # Ensure client config is loaded
        if self.current_client_config is None:
            self.ensure_client_config_loaded()

        # 2. Try to get from current client config
        if self.current_client_config:
            value = self.current_client_config.get(
                key,
            ) or self.current_client_config.get(key.upper())
            if value is not None:
                logger.debug(
                    f"Getting dynamic setting {key} from client config = {value}",
                )
                return value

        # 3. Try to get from environment settings (settings.toml / .secrets.toml / Secrets)
        try:
            env_value = getattr(self.environment_settings, key, None) or getattr(
                self.environment_settings,
                key.upper(),
                None,
            )
            if env_value is not None:
                # Check if it's a template variable that needs processing
                if isinstance(env_value, str) and env_value.startswith("@format {"):
                    # Extract variable name and resolve it
                    var_name = env_value[8:-1]  # Remove "@format {" and "}"
                    resolved_value = self._resolve_template_variable(
                        var_name,
                        self.current_tenant or "default",
                        self.current_environment or "dev",
                    )
                    logger.debug(f"Resolved template variable {key} = {resolved_value}")
                    return resolved_value
                else:
                    logger.debug(
                        f"Getting setting {key} from environment settings = {env_value}",
                    )
                    return env_value
        except (AttributeError, Exception):
            pass

        logger.warning(f"Setting {key} not found, using default: {default}")
        return default

    def get_client_info(self) -> dict[str, Any]:
        """Get information about the current client configuration."""

        # Ensure client config is loaded
        if self.current_client_config is None:
            self.ensure_client_config_loaded()

        if self.current_client_config is None:
            return {
                "tenant_id": None,
                "environment": None,
                "config_source": "none",
                "client_name": None,
            }

        return {
            "tenant_id": self.current_tenant,
            "environment": self.current_environment,
            "config_source": self.current_client_config.get("_metadata", {}).get(
                "config_source",
                "unknown",
            ),
            "client_name": self.current_client_config.get("CLIENT_NAME"),
            "project_id": self.current_client_config.get("PROJECT_ID"),
            "gurobi_api_url": self.current_client_config.get("GUROBI_API_URL"),
        }

    def list_available_clients(self) -> list:
        """List all available client configurations."""

        if not self.clients_dir.exists():
            return []

        clients = []
        for config_file in self.clients_dir.glob("*.toml"):
            try:
                config = self._load_toml_file(config_file)
                client_name = config.get("DEFAULT", {}).get(
                    "CLIENT_NAME",
                    config_file.stem,
                )
                tenant_id = config.get("DEFAULT", {}).get("TENANT_ID", client_name)
                clients.append(
                    {
                        "file": config_file.name,
                        "client_name": client_name,
                        "tenant_id": tenant_id,
                    },
                )
            except Exception as e:
                logger.warning(f"Error reading client file {config_file}: {e}")

        return clients

    def validate_client_config(self, tenant_id: str) -> bool:
        """Validate that a client configuration exists and is valid."""

        client_file = self._find_client_file(tenant_id)
        if not client_file:
            logger.warning(f"No client configuration found for tenant: {tenant_id}")
            return False

        try:
            config = self._load_toml_file(client_file)
            required_keys = ["CLIENT_NAME", "TENANT_ID", "PROJECT_ID"]

            default_config = config.get("DEFAULT", {})
            missing_keys = [key for key in required_keys if key not in default_config]

            if missing_keys:
                logger.error(f"Missing required keys in {client_file}: {missing_keys}")
                return False

            logger.info(
                f"Client configuration validation passed for tenant: {tenant_id}",
            )
            return True

        except Exception as e:
            logger.error(
                f"Client configuration validation failed for tenant {tenant_id}: {e}",
            )
            return False

    def ensure_client_config_loaded(
        self,
        tenant_id: str = None,
        environment: str = None,
    ):
        """Ensure that a client configuration is loaded."""

        # If no tenant_id provided, try to get from environment or use default
        if tenant_id is None:
            # First try to get from environment variables
            tenant_id = os.getenv("CLIENT_NAME") or os.getenv("TENANT_ID")

            # If not found in env vars, try to get from .secrets.toml
            if not tenant_id:
                try:
                    tenant_id = self.environment_settings.get("TENANT_NAME")
                    logger.info(f"Found TENANT_NAME in .secrets.toml: {tenant_id}")
                except Exception as e:
                    logger.warning(
                        f"Could not read TENANT_NAME from .secrets.toml: {e}",
                    )

            # Final fallback
            if not tenant_id:
                tenant_id = "default-client"
                logger.warning("No TENANT_NAME found, using default-client")

        # If no environment provided, try to get from environment or use default
        if environment is None:
            environment = os.getenv("env") or os.getenv("DEPLOYMENT_ENV") or "dev"

        # Only load if not already loaded or if different tenant/environment
        if (
            self.current_tenant != tenant_id
            or self.current_environment != environment
            or self.current_client_config is None
        ):

            logger.debug(
                f"Ensuring client config is loaded for tenant: {tenant_id}, environment: {environment}",
            )
            self.load_dynamic_client_config(tenant_id, environment)


# Usage
env_config_manager = EnvConfigManager()
