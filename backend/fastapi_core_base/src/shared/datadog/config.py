"""Core Datadog configuration: service name, environment, and basic settings."""

import os

from src.shared.configuration.config import EnvConfigManager


def configure_service_name(
    env_config_manager: EnvConfigManager,
) -> tuple[str, str, str, str, str]:
    """Configure DD_SERVICE name from application, client, server, and environment.

    Read DD_SERVICE from environment (set by supervisor) or construct it
    for local development. DD_SERVICE is auto-constructed from
    CLIENT_NAME + env (no need to set).

    :param env_config_manager: Configuration manager instance
    :return: Tuple of (dd_service, client, application, env, server)
    """
    # Use get_dynamic_setting() - handles both single-tenant and multi-tenant cases
    # Priority: 1. current_client_config (runtime switching) → 2. environment_settings (startup/default)
    # Read from datadog.toml (DEFAULT_CLIENT_NAME, DEFAULT_APPLICATION, SERVER_IDENTIFIER)
    # All defaults come from datadog.toml
    client = env_config_manager.get_dynamic_setting(
        "CLIENT_NAME",
        env_config_manager.get_dynamic_setting("DEFAULT_CLIENT_NAME", "basesmart"),
    )
    application = env_config_manager.get_dynamic_setting(
        "APPLICATION",
        env_config_manager.get_dynamic_setting(
            "DEFAULT_APPLICATION",
            "core-base-pricing",
        ),
    )
    # env = env_config_manager.environment_settings.DEPLOYMENT_ENVIRONMENT  # Use environment directly (from 'env' variable)
    env = env_config_manager.environment_settings.DEPLOYMENT_ENV

    # Auto-detect Cloud Run: Check K_SERVICE (set automatically by Cloud Run)
    # Also check IS_CLOUD_RUN flag if explicitly set (for backward compatibility)
    k_service = os.getenv("K_SERVICE")
    is_cloud_run_setting = env_config_manager.get_dynamic_setting("IS_CLOUD_RUN", False)
    if isinstance(is_cloud_run_setting, str):
        is_cloud_run_flag = is_cloud_run_setting.lower() in ("true", "1", "yes")
    else:
        is_cloud_run_flag = bool(is_cloud_run_setting)

    # Cloud Run is detected if K_SERVICE exists OR IS_CLOUD_RUN flag is set
    is_cloud_run = bool(k_service) or is_cloud_run_flag

    # Get server identifier (needed for return value and fallback)
    server = env_config_manager.get_dynamic_setting("SERVER_IDENTIFIER", "be")

    if is_cloud_run:
        # Cloud Run: Use NEW_RELIC_APP_NAME if set, otherwise use K_SERVICE, otherwise construct
        dd_service = env_config_manager.get_dynamic_setting("NEW_RELIC_APP_NAME", "")
        if not dd_service and k_service:
            # Use K_SERVICE (Cloud Run service name) as service name
            dd_service = k_service
        if not dd_service:
            # Fallback: Construct service name if neither NEW_RELIC_APP_NAME nor K_SERVICE is set
            dd_service = f"{application}-{client}-{server}-{env}"
    else:
        # Backend server: Construct service name from components
        dd_service = f"{application}-{client}-{server}-{env}"

    os.environ["DD_SERVICE"] = dd_service
    print(f"✅ DD_SERVICE set to: {dd_service}")

    # DD_ENV is automatically derived from 'env' variable (set by supervisor)
    dd_env = env
    os.environ["DD_ENV"] = dd_env

    # Note: DD_SERVICE is set as environment variable, which ddtrace uses as default
    # Any spans without explicit service names will inherit DD_SERVICE
    # Additional configuration for specific libraries is done in instrumentation.py

    return dd_service, client, application, env, server


def configure_basic_settings(env_config_manager: EnvConfigManager) -> None:
    """Configure basic Datadog settings from environment or config.

    :param env_config_manager: Configuration manager instance
    """
    # DD_TRACE_AGENT_URL: Read from datadog.toml (can be overridden by environment variable)
    # First check env var, then datadog.toml, then use default from datadog.toml
    dd_trace_agent_url = os.getenv(
        "DD_TRACE_AGENT_URL",
    ) or env_config_manager.get_dynamic_setting(
        "DD_TRACE_AGENT_URL",
        "http://localhost:8126",  # Final fallback if not in config
    )
    os.environ["DD_TRACE_AGENT_URL"] = str(dd_trace_agent_url)

    # DD_TRACE_ENABLED: Read from datadog.toml (only if DATADOG_ENABLED=true)
    # Note: When DATADOG_ENABLED=false, this is set to false in app/datadog/__init__.py
    dd_trace_enabled = env_config_manager.get_dynamic_setting("DD_TRACE_ENABLED", True)
    if isinstance(dd_trace_enabled, str):
        dd_trace_enabled = dd_trace_enabled.lower() in ("true", "1", "yes")
    os.environ["DD_TRACE_ENABLED"] = str(bool(dd_trace_enabled))

    # DD_LOGS_INJECTION: Read from datadog.toml
    # First check env var (Cloud Run override), then config, then default True
    dd_logs_injection = os.getenv("DD_LOGS_INJECTION")
    if dd_logs_injection is None:
        dd_logs_injection = env_config_manager.get_dynamic_setting(
            "DD_LOGS_INJECTION",
            True,
        )
    if isinstance(dd_logs_injection, str):
        dd_logs_injection = dd_logs_injection.lower() in ("true", "1", "yes")
    else:
        dd_logs_injection = bool(dd_logs_injection)
    os.environ["DD_LOGS_INJECTION"] = str(dd_logs_injection)
    print(f"✅ DD_LOGS_INJECTION set to: {dd_logs_injection}")

    # DD_REMOTE_CONFIGURATION_ENABLED: Read from datadog.toml
    dd_remote_config = env_config_manager.get_dynamic_setting(
        "DD_REMOTE_CONFIGURATION_ENABLED",
        False,
    )
    if isinstance(dd_remote_config, str):
        dd_remote_config = dd_remote_config.lower() in ("true", "1", "yes")
    os.environ["DD_REMOTE_CONFIGURATION_ENABLED"] = str(bool(dd_remote_config))

    # DD_RUNTIME_METRICS_ENABLED: Read from datadog.toml
    dd_runtime_metrics = env_config_manager.get_dynamic_setting(
        "DD_RUNTIME_METRICS_ENABLED",
        True,
    )
    if isinstance(dd_runtime_metrics, str):
        dd_runtime_metrics = dd_runtime_metrics.lower() in ("true", "1", "yes")
    os.environ["DD_RUNTIME_METRICS_ENABLED"] = str(bool(dd_runtime_metrics))

    # DD_RUNTIME_METRICS_RUNTIME_ID_ENABLED: Read from datadog.toml
    dd_runtime_id = env_config_manager.get_dynamic_setting(
        "DD_RUNTIME_METRICS_RUNTIME_ID_ENABLED",
        True,
    )
    if isinstance(dd_runtime_id, str):
        dd_runtime_id = dd_runtime_id.lower() in ("true", "1", "yes")
    os.environ["DD_RUNTIME_METRICS_RUNTIME_ID_ENABLED"] = str(bool(dd_runtime_id))

    # DD_PROFILING_ENABLED: Read from datadog.toml
    dd_profiling = env_config_manager.get_dynamic_setting("DD_PROFILING_ENABLED", True)
    if isinstance(dd_profiling, str):
        dd_profiling = dd_profiling.lower() in ("true", "1", "yes")
    os.environ["DD_PROFILING_ENABLED"] = str(bool(dd_profiling))

    # DD_INSTRUMENTATION_TELEMETRY_ENABLED: Read from datadog.toml
    # Note: This is also set early in app/datadog/__init__.py before ddtrace imports
    # Setting it here ensures it's properly configured during initialization
    dd_telemetry = env_config_manager.get_dynamic_setting(
        "DD_INSTRUMENTATION_TELEMETRY_ENABLED",
        True,
    )
    if isinstance(dd_telemetry, str):
        dd_telemetry = dd_telemetry.lower() in ("true", "1", "yes")
    os.environ["DD_INSTRUMENTATION_TELEMETRY_ENABLED"] = str(bool(dd_telemetry))
