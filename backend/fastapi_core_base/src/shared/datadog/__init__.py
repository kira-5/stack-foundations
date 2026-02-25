"""Datadog configuration module - MUST BE IMPORTED BEFORE OTHER IMPORTS.

WHY DATADOG MUST BE BEFORE OTHER IMPORTS:
1. Monkey-patching: patch_all() must be called BEFORE libraries (redis, sqlalchemy,
   psycopg, requests, aiohttp) are imported. Once imported, they're already loaded
   into memory and can't be properly instrumented.
2. Environment variables: DD_* env vars must be set BEFORE importing ddtrace.auto
   because ddtrace reads them at import time.
3. Auto-instrumentation: ddtrace.auto enables automatic tracing, but only works
   if called before target libraries are imported.
"""

import os
from src.shared.configuration.config import EnvConfigManager  # noqa: E402

# Check DATADOG_ENABLED from config BEFORE importing ddtrace
# This prevents "Connection refused" errors when Datadog is disabled
# We need to set DD_* env vars before ddtrace imports to prevent telemetry from starting
try:
    # Create a temporary config manager to check DATADOG_ENABLED early
    temp_config = EnvConfigManager()
    dd_enabled = temp_config.get_dynamic_setting(
        "DATADOG_ENABLED",
        True,
    )  # Default: enabled
    if isinstance(dd_enabled, str):
        dd_enabled = dd_enabled.lower() in ("true", "1", "yes")
    else:
        dd_enabled = bool(dd_enabled)

    if not dd_enabled:
        # Disable all Datadog features BEFORE importing ddtrace
        os.environ["DD_INSTRUMENTATION_TELEMETRY_ENABLED"] = "false"
        os.environ["DD_TRACE_ENABLED"] = "false"
        os.environ["DD_LOGS_INJECTION"] = "false"
        os.environ["DD_RUNTIME_METRICS_ENABLED"] = "false"
        os.environ["DD_PROFILING_ENABLED"] = "false"
    else:
        # Read DD_INSTRUMENTATION_TELEMETRY_ENABLED from config (datadog.toml)
        # Priority: Env Var > Client TOML > Environment Settings > datadog.toml > Default (true)
        dd_telemetry_enabled = temp_config.get_dynamic_setting(
            "DD_INSTRUMENTATION_TELEMETRY_ENABLED",
            True,  # Default: enabled
        )
        if isinstance(dd_telemetry_enabled, str):
            dd_telemetry_enabled = dd_telemetry_enabled.lower() in ("true", "1", "yes")
        else:
            dd_telemetry_enabled = bool(dd_telemetry_enabled)
        os.environ["DD_INSTRUMENTATION_TELEMETRY_ENABLED"] = str(
            bool(dd_telemetry_enabled),
        )

        # Check if we should disable FastAPI auto-instrumentation (when using custom spans)
        # This prevents duplicate "fastapi" service spans
        # Read from datadog.toml config
        use_custom_span_setting = temp_config.get_dynamic_setting(
            "DD_USE_CUSTOM_SPAN",
            True,
        )
        if isinstance(use_custom_span_setting, str):
            use_custom_span = use_custom_span_setting.lower() in ("true", "1", "yes")
        else:
            use_custom_span = bool(use_custom_span_setting)

        if use_custom_span:
            # Override to false when using custom spans (to avoid duplicates)
            os.environ["DD_TRACE_FASTAPI_ENABLED"] = "false"
        else:
            # When not using custom spans, read from datadog.toml config
            dd_fastapi_enabled = temp_config.get_dynamic_setting(
                "DD_TRACE_FASTAPI_ENABLED",
                True,
            )
            if isinstance(dd_fastapi_enabled, str):
                dd_fastapi_enabled = dd_fastapi_enabled.lower() in ("true", "1", "yes")
            else:
                dd_fastapi_enabled = bool(dd_fastapi_enabled)
            os.environ["DD_TRACE_FASTAPI_ENABLED"] = str(dd_fastapi_enabled)
except Exception:
    # If config check fails, default to disabled (safe fallback)
    os.environ["DD_INSTRUMENTATION_TELEMETRY_ENABLED"] = "false"
    os.environ["DD_TRACE_ENABLED"] = "false"
    os.environ["DD_LOGS_INJECTION"] = "false"
    os.environ["DD_RUNTIME_METRICS_ENABLED"] = "false"
    os.environ["DD_PROFILING_ENABLED"] = "false"
    use_custom_span = True  # Default to True for FastAPI config
    os.environ["DD_TRACE_FASTAPI_ENABLED"] = "false"

# Only import datadog submodules if Datadog is enabled (prevents ddtrace from being imported)
# These modules will be imported inside initialize_datadog() if needed
# This prevents ddtrace from initializing when DATADOG_ENABLED=false

# Import ddtrace.auto early (for side effects - enables automatic log injection)
# FastAPI auto-instrumentation will be disabled if DD_TRACE_FASTAPI_ENABLED=false


def initialize_datadog(env_config_manager: EnvConfigManager) -> bool:
    """Initialize Datadog configuration - MUST BE CALLED BEFORE OTHER IMPORTS.

    This function configures:
    - Service name and environment
    - Global tags
    - Version tracking
    - Deployment metadata tags
    - Per-service sampling rates
    - Library auto-instrumentation
    - Runtime metrics
    - Profiler

    :param env_config_manager: Configuration manager instance
    :return: True if initialization succeeded, False otherwise
    """
    # Check if Datadog is enabled for this client/environment
    # Default: ENABLED (True) - Datadog is enabled by default, disable per client/environment if needed
    # Can be set in datadog.toml, client TOML file, or environment variable
    # Priority order: Env Var > Client TOML > Environment Settings > datadog.toml > Default
    # See DATADOG_LOGGER_PRIORITY_ORDER.md for detailed priority order documentation
    dd_enabled = env_config_manager.get_dynamic_setting("DATADOG_ENABLED", True)
    if isinstance(dd_enabled, str):
        dd_enabled = dd_enabled.lower() in ("true", "1", "yes")
    else:
        dd_enabled = bool(dd_enabled)

    if not dd_enabled:
        print(
            "ℹ️  Datadog disabled for this client/environment (DATADOG_ENABLED=false or not set)",
        )
        return False

    # Import datadog submodules only when Datadog is enabled
    # This prevents ddtrace from being imported when DATADOG_ENABLED=false
    try:
        from . import config, instrumentation, sampling, tags, version  # noqa: E402
    except ImportError as import_error:
        print(f"⚠️ Failed to import Datadog submodules: {import_error}")
        return False

    try:
        # Step 1: Configure service name and basic settings
        dd_service, client, application, env, server = config.configure_service_name(
            env_config_manager,
        )
        config.configure_basic_settings(env_config_manager)

        # Step 2: Configure global tags
        tags.configure_global_tags(client, env, application, server)

        # Step 3: Generate dynamic version and get deployment metadata
        _dd_version, build_id, job_id, launched_by = version.generate_dynamic_version(
            env_config_manager,
        )

        # Step 4: Add deployment tags
        tags.add_deployment_tags(build_id, job_id, launched_by)

        # Step 5: Configure instrumentation and get service names + trace enabled flags
        service_names, trace_enabled = instrumentation.configure_instrumentation(
            application,
            client,
            env,
            env_config_manager,
        )

        # Step 6: Configure per-service sampling rates
        sampling.configure_sampling_rules(
            dd_service,
            service_names,
            trace_enabled,
            env_config_manager,
        )

        # Step 7: Enable runtime metrics
        instrumentation.enable_runtime_metrics(env_config_manager)

        # Step 8: Enable profiler
        instrumentation.enable_profiler(env_config_manager)

        print("✅ Datadog initialization completed successfully")
        return True

    except Exception as e:
        print(f"⚠️ Datadog initialization failed: {str(e)}")
        print("⚠️ Continuing without Datadog tracing")
        return False
