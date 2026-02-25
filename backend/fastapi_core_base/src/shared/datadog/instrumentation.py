"""Library instrumentation: auto-instrumentation setup for Datadog.

Service List (Pattern: {application}-{client}-{component}-{env}):

core-base-pricing-lesliespool-be-dev - Main FastAPI app (clean, focused)
core-base-pricing-lesliespool-redis-dev - Redis
core-base-pricing-lesliespool-postgres-dev - PostgreSQL
core-base-pricing-lesliespool-requests-dev - HTTP requests
core-base-pricing-lesliespool-aiohttp-dev - Async HTTP
core-base-pricing-lesliespool-grpc-dev - gRPC (Secret Manager)
core-base-pricing-lesliespool-misc-dev - Templates, unknown operations

Datadog Service Architecture - Separate Services Mode

This module configures 7 separate services per client/environment for better observability,
filtering, and cost optimization. Each service has independent sampling rates and can be
monitored separately.

Service List (Pattern: {application}-{client}-{component}-{env}):

1. core-base-pricing-lesliespool-be-dev
   - Type: Main FastAPI Application
   - Purpose: FastAPI request/response handling, API endpoints, business logic
   - Sampling: 100% (DD_TRACE_SAMPLE_RATE=1.0) - Full visibility for debugging
   - Instrumentation: FastAPI auto-instrumentation (disabled when using custom spans)
   - Notes: Clean service focused only on application logic, no templates/unknown ops

2. core-base-pricing-lesliespool-redis-dev
   - Type: Redis/DragonflyDB Cache
   - Purpose: Caching operations, session storage, pub/sub messaging
   - Sampling: 10% (DD_TRACE_REDIS_SAMPLE_RATE=0.1) - High volume, reduce noise
   - Instrumentation: Redis library auto-instrumentation
   - Operations: GET, SET, PING, PUBLISH, SUBSCRIBE, etc.

3. core-base-pricing-lesliespool-postgres-dev
   - Type: PostgreSQL Database
   - Purpose: Database queries, data persistence, transactions
   - Sampling: 10% (DD_TRACE_POSTGRES_SAMPLE_RATE=0.1) - High volume, reduce noise
   - Instrumentation: psycopg2/psycopg3 and SQLAlchemy auto-instrumentation
   - Operations: SELECT, INSERT, UPDATE, DELETE, transactions

4. core-base-pricing-lesliespool-requests-dev
   - Type: Synchronous HTTP Client
   - Purpose: External HTTP API calls, GCP metadata server requests
   - Sampling: 50% (DD_TRACE_REQUESTS_SAMPLE_RATE=0.5) - Moderate volume
   - Instrumentation: requests library auto-instrumentation
   - Operations: GET, POST, PUT, DELETE to external APIs

5. core-base-pricing-lesliespool-aiohttp-dev
   - Type: Asynchronous HTTP Client
   - Purpose: Async HTTP calls, concurrent API requests
   - Sampling: 50% (DD_TRACE_AIOHTTP_SAMPLE_RATE=0.5) - Moderate volume
   - Instrumentation: aiohttp library auto-instrumentation
   - Operations: Async GET, POST, PUT, DELETE operations

6. core-base-pricing-lesliespool-grpc-dev
   - Type: gRPC Client (Async)
   - Purpose: Google Cloud Secret Manager calls, gRPC-based services
   - Sampling: 30% (DD_TRACE_GRPC_SAMPLE_RATE=0.3) - Infrastructure, lower volume
   - Instrumentation: gRPC auto-instrumentation (via google-cloud-secret-manager)
   - Operations: AccessSecretVersion, gRPC method calls

7. core-base-pricing-lesliespool-misc-dev
   - Type: Miscellaneous Operations
   - Purpose: Template rendering (Jinja2), unknown/unnamed operations, internal utilities
   - Sampling: 50% (DD_TRACE_MISC_SAMPLE_RATE=0.5) - Moderate volume
   - Instrumentation: Jinja2 auto-instrumentation, span processor for unnamed spans
   - Operations: HTML template rendering (.j2 files), unknown Python operations
   - Notes: Keeps main service clean by separating non-core operations

Configuration:
- Service naming mode: "separate" (DD_SERVICE_NAMING_MODE)
- Each service can be filtered independently in Datadog
- Per-service sampling rates optimize costs while maintaining visibility
- Consistent naming pattern enables multi-tenant dashboards and alerts
"""

import os

from src.shared.configuration.config import EnvConfigManager

from .constants import (
    CONFIG_KEY_AIOHTTP_ENABLED,
    CONFIG_KEY_GRPC_ENABLED,
    CONFIG_KEY_PSYCOPG_ENABLED,
    CONFIG_KEY_REDIS_ENABLED,
    CONFIG_KEY_REQUESTS_ENABLED,
    CONFIG_KEY_SERVICE_NAMING_MODE,
    CONFIG_KEY_SQLALCHEMY_ENABLED,
    DEFAULT_SERVICE_NAMING_MODE,
    DEFAULT_TRACE_AIOHTTP_ENABLED,
    DEFAULT_TRACE_GRPC_ENABLED,
    DEFAULT_TRACE_PSYCOPG_ENABLED,
    DEFAULT_TRACE_REDIS_ENABLED,
    DEFAULT_TRACE_REQUESTS_ENABLED,
    DEFAULT_TRACE_SQLALCHEMY_ENABLED,
    SERVICE_NAMING_MODE_COMPONENT_TAGS,
    SERVICE_NAMING_MODE_HYBRID,
    SERVICE_NAMING_MODE_SEPARATE,
    SERVICE_NAMING_MODE_SERVICE_CENTRIC,
)

# =============================================================================
# GLOBAL SERVICE NAMING MODE CONFIGURATION
# =============================================================================
# This variable stores the current service naming mode after initialization.
# It can be accessed from other modules to check which mode is active.
#
# Values:
#   - "separate": Explicit service naming (sets DD_*_SERVICE env vars)
#   - "inferred": Let Datadog infer service names automatically
#
# To change the mode, set DD_SERVICE_NAMING_MODE environment variable or
# configure it in settings.toml before calling configure_instrumentation().
#
# Example usage:
#   from src.shared.datadog.instrumentation import SERVICE_NAMING_MODE
#   if SERVICE_NAMING_MODE == "separate":
#       # Do something specific to separate services mode
# =============================================================================
SERVICE_NAMING_MODE: str | None = None


def get_bool_setting(
    key: str,
    default: bool,
    env_config_manager: EnvConfigManager,
) -> bool:
    """Get boolean setting from environment or settings.toml.

    :param key: Configuration key name
    :param default: Default value if not found
    :param env_config_manager: Configuration manager instance
    :return: Boolean value
    """
    env_value = os.getenv(key, "").lower()
    if env_value in ("true", "1", "yes"):
        return True
    if env_value in ("false", "0", "no"):
        return False

    # Fall back to settings.toml
    setting_value = getattr(
        env_config_manager.environment_settings,
        key,
        default,
    )
    # Handle None explicitly
    if setting_value is None:
        return default
    if isinstance(setting_value, bool):
        return setting_value
    if isinstance(setting_value, str):
        return setting_value.lower() in ("true", "1", "yes")
    return default


def get_service_naming_mode(env_config_manager: EnvConfigManager) -> str:
    """Get service naming mode from environment or settings.toml.

    Four modes are supported with comprehensive ratings:

    ═══════════════════════════════════════════════════════════════════════════
    MODE COMPARISON TABLE
    ═══════════════════════════════════════════════════════════════════════════

    Service Separation:
    ┌─────────────┬──────────┬───────────────┬────────┬─────────────────┐
    │   Service   │ Separate │ Component Tags│ Hybrid │ Service Centric │
    ├─────────────┼──────────┼───────────────┼────────┼─────────────────┤
    │ Redis       │ Separate │ Separate      │ Separate│ Grouped         │
    │ PostgreSQL  │ Separate │ Separate      │ Separate│ Grouped         │
    │ Requests    │ Separate │ Separate      │ Grouped │ Grouped         │
    │ aiohttp     │ Separate │ Separate      │ Grouped │ Grouped         │
    │ gRPC        │ Separate │ Separate      │ Grouped │ Grouped         │
    │ Misc        │ Separate │ Separate      │ Grouped │ Grouped         │
    └─────────────┴──────────┴───────────────┴────────┴─────────────────┘

    Rating Comparison (out of 5):
    ┌─────────────────────┬──────────┬───────────────┬────────┬─────────────────┐
    │     Criteria        │ Separate │ Component Tags│ Hybrid │ Service Centric │
    ├─────────────────────┼──────────┼───────────────┼────────┼─────────────────┤
    │ Multi-tenant        │   5/5    │     5/5       │  4/5   │      3/5        │
    │ Filtering            │   5/5    │     5/5       │  4/5   │      3/5        │
    │ Service Map          │   5/5    │     5/5       │  4/5   │      2/5        │
    │ Complexity           │   4/5    │     3/5       │  3/5   │      5/5        │
    │ Cost Optimization    │   4/5    │     5/5       │  4/5   │      3/5        │
    │ Debugging            │   5/5    │     5/5       │  4/5   │      3/5        │
    │ Dashboards           │   5/5    │     5/5       │  4/5   │      3/5        │
    ├─────────────────────┼──────────┼───────────────┼────────┼─────────────────┤
    │ OVERALL RATING       │  4.7/5   │    4.7/5      │ 3.9/5  │     2.9/5       │
    │                      │ ⭐⭐⭐⭐⭐ │   ⭐⭐⭐⭐⭐    │ ⭐⭐⭐⭐ │      ⭐⭐⭐       │
    └─────────────────────┴──────────┴───────────────┴────────┴─────────────────┘

    Total Services Created:
    - Separate:        7 services (1 main + 6 components)
    - Component Tags:  7 services (same as separate + tags)
    - Hybrid:          3 services (1 main + Redis + PostgreSQL)
    - Service Centric:  1 service (everything grouped)

    Best Use Cases:
    - Separate:        Multi-tenant production (BEST for your use case)
    - Component Tags:  Multi-tenant + advanced filtering needs
    - Hybrid:          Want fewer services but still monitor critical components
    - Service Centric:  Simple apps, single tenant, minimal setup

    :param env_config_manager: Configuration manager instance
    :return: Service naming mode
    """
    env_value = os.getenv(CONFIG_KEY_SERVICE_NAMING_MODE, "").lower()
    valid_modes = (
        SERVICE_NAMING_MODE_SEPARATE,
        SERVICE_NAMING_MODE_COMPONENT_TAGS,
        SERVICE_NAMING_MODE_HYBRID,
        SERVICE_NAMING_MODE_SERVICE_CENTRIC,
    )
    if env_value in valid_modes:
        return env_value

    # Fall back to settings.toml
    setting_value = getattr(
        env_config_manager.environment_settings,
        CONFIG_KEY_SERVICE_NAMING_MODE,
        DEFAULT_SERVICE_NAMING_MODE,
    )
    if setting_value is None:
        return DEFAULT_SERVICE_NAMING_MODE
    if isinstance(setting_value, str):
        mode = setting_value.lower()
        if mode in valid_modes:
            return mode
    return DEFAULT_SERVICE_NAMING_MODE


def get_service_name(
    library_key: str,
    component_name: str,
    application: str,
    client: str,
    env: str,
    env_config_manager: EnvConfigManager,
) -> str:
    """Get custom service name from environment or settings.toml, or use pattern.

    :param library_key: Library key (e.g., "REDIS", "POSTGRES")
    :param component_name: Component name (e.g., "redis", "postgres")
    :param application: Application name
    :param client: Client name
    :param env: Environment name
    :param env_config_manager: Configuration manager instance
    :return: Service name
    """
    env_key = f"DD_{library_key}_SERVICE"
    # Check environment variable first
    env_value = os.getenv(env_key)
    if env_value:
        return env_value

    # Check settings.toml
    setting_value = getattr(
        env_config_manager.environment_settings,
        env_key,
        None,
    )
    if setting_value:
        return str(setting_value)

    # Use same pattern as DD_SERVICE: {application}-{client}-{component}-{env}
    return f"{application}-{client}-{component_name}-{env}"


def configure_separate_services(
    application: str,
    client: str,
    env: str,
    trace_enabled: dict[str, bool],
    env_config_manager: EnvConfigManager,
) -> tuple[dict[str, str], dict[str, str]]:
    """Configure Separate Services approach (Explicit Naming) - Rating: 5.0/5 ⭐⭐⭐⭐⭐

    What it does: Each component gets its own explicit service name via DD_*_SERVICE env vars.

    Service structure:
      - core-base-pricing-lesliespool-be-dev (Main FastAPI app)
      - base-pricing-lesliespool-postgres-dev (PostgreSQL)
      - base-pricing-lesliespool-redis-dev (Redis)
      - base-pricing-lesliespool-requests-dev (HTTP requests)
      - base-pricing-lesliespool-aiohttp-dev (async HTTP calls)
      - base-pricing-lesliespool-grpc-dev (gRPC calls - Secret Manager)
      - base-pricing-lesliespool-misc-dev (Miscellaneous - templates, unknown operations)

    Ratings:
      Multi-tenant support: 5/5 - Perfect - consistent naming across all tenants
      Filtering:           5/5 - Excellent - filter by client/component/environment
      Service map:        5/5 - Clear dependency visualization
      Complexity:        4/5 - Medium - requires configuration but predictable
      Cost:              4/5 - Good - per-service sampling rates for optimization
      Debugging:         5/5 - Excellent - clear latency attribution
      Dashboards:        5/5 - Easy - consistent naming enables templates

    Verdict: ✅ BEST FOR YOUR MULTI-TENANT USE CASE

    :param application: Application name
    :param client: Client name
    :param env: Environment name
    :param trace_enabled: Dictionary of trace enabled flags
    :param env_config_manager: Configuration manager instance
    :return: Tuple of (service_names dict, component_names dict for tags)
    """
    print("🔍 separate configuration started")
    service_names: dict[str, str] = {}
    component_names: dict[str, str] = {}

    if trace_enabled.get("redis"):
        redis_service = get_service_name(
            "REDIS",
            "redis",
            application,
            client,
            env,
            env_config_manager,
        )
        service_names["redis"] = redis_service
        os.environ["DD_REDIS_SERVICE"] = redis_service
        component_names["redis"] = f"{application}-{client}-redis-{env} (Redis commands)"

    if trace_enabled.get("psycopg") or trace_enabled.get("sqlalchemy"):
        postgres_service = get_service_name(
            "POSTGRES",
            "postgres",
            application,
            client,
            env,
            env_config_manager,
        )
        service_names["postgres"] = postgres_service
        # Set multiple env vars to ensure ddtrace picks it up
        # ddtrace reads: DD_PSYCOPG_SERVICE, DD_DB_SERVICE, DD_SQLALCHEMY_SERVICE
        os.environ["DD_POSTGRES_SERVICE"] = postgres_service
        os.environ["DD_PSYCOPG_SERVICE"] = postgres_service  # ddtrace uses this for psycopg
        os.environ["DD_DB_SERVICE"] = postgres_service
        if trace_enabled.get("sqlalchemy"):
            os.environ["DD_SQLALCHEMY_SERVICE"] = postgres_service
        component_names["postgres"] = f"{application}-{client}-postgres-{env} (PostgreSQL queries)"

    if trace_enabled.get("requests"):
        requests_service = get_service_name(
            "REQUESTS",
            "requests",
            application,
            client,
            env,
            env_config_manager,
        )
        service_names["requests"] = requests_service
        os.environ["DD_REQUESTS_SERVICE"] = requests_service
        component_names["requests"] = f"{application}-{client}-requests-{env} (HTTP requests)"

    if trace_enabled.get("aiohttp"):
        aiohttp_service = get_service_name(
            "AIOHTTP",
            "aiohttp",
            application,
            client,
            env,
            env_config_manager,
        )
        service_names["aiohttp"] = aiohttp_service
        os.environ["DD_AIOHTTP_SERVICE"] = aiohttp_service
        component_names["aiohttp"] = f"{application}-{client}-aiohttp-{env} (async HTTP calls)"

    if trace_enabled.get("grpc"):
        grpc_service = get_service_name(
            "GRPC",
            "grpc",
            application,
            client,
            env,
            env_config_manager,
        )
        service_names["grpc"] = grpc_service
        os.environ["DD_GRPC_SERVICE"] = grpc_service
        component_names["grpc"] = f"{application}-{client}-grpc-{env} (gRPC calls - Secret Manager)"

    # Misc service for templates, unknown operations, and other internal operations
    # This keeps the main service clean and focused on FastAPI request/response logic
    misc_service = get_service_name(
        "MISC",
        "misc",
        application,
        client,
        env,
        env_config_manager,
    )
    service_names["misc"] = misc_service
    os.environ["DD_MISC_SERVICE"] = misc_service
    component_names["misc"] = f"{application}-{client}-misc-{env} (Miscellaneous - templates, unknown operations)"

    return service_names, component_names


def configure_component_based_with_tags(
    application: str,
    client: str,
    env: str,
    trace_enabled: dict[str, bool],
    env_config_manager: EnvConfigManager,
) -> tuple[dict[str, str], dict[str, str]]:
    """Configure Component-Based + Tags approach - Rating: 4.7/5 ⭐⭐⭐⭐⭐

    What it does: Separate services + custom tags (client, application, component) for
    additional filtering dimensions.

    Service structure:
      - base-pricing-lesliespool-postgres-dev
        Tags: client=lesliespool, application=base-pricing, component=postgres
      - base-pricing-lesliespool-redis-dev
        Tags: client=lesliespool, application=base-pricing, component=redis

    Ratings:
      Multi-tenant support: 5/5 - Excellent - tags + service names provide flexibility
      Filtering:           5/5 - Excellent - multiple filter dimensions (service + tags)
      Service map:        5/5 - Excellent - clear dependencies
      Complexity:        3/5 - Medium - requires tag configuration
      Cost:              5/5 - Excellent - filter by tags for sampling optimization
      Debugging:         5/5 - Excellent - multiple ways to identify issues
      Dashboards:        5/5 - Excellent - tag-based queries enable powerful dashboards

    Verdict: ✅ EXCELLENT ENHANCEMENT TO SEPARATE SERVICES

    :param application: Application name
    :param client: Client name
    :param env: Environment name
    :param trace_enabled: Dictionary of trace enabled flags
    :param env_config_manager: Configuration manager instance
    :return: Tuple of (service_names dict, component_names dict for tags)
    """
    # Use separate services as base
    service_names, component_names = configure_separate_services(
        application,
        client,
        env,
        trace_enabled,
        env_config_manager,
    )

    # Add custom tags to component_names for tag-based filtering
    # These tags will be added to spans via span processor
    for component in component_names:
        component_names[component] = (
            f"{component_names[component]} " f"[client={client}, application={application}, component={component}]"
        )

    return service_names, component_names


def configure_hybrid_services(
    application: str,
    client: str,
    env: str,
    trace_enabled: dict[str, bool],
    env_config_manager: EnvConfigManager,
) -> tuple[dict[str, str], dict[str, str]]:
    """Configure Hybrid Services approach (Selective Separation) - Rating: 4.0/5 ⭐⭐⭐⭐

    What it does: Separate services for critical components (DB, Redis), unified for
    others (HTTP requests grouped with main service).

    Service structure:
      - core-base-pricing-lesliespool-be-dev (includes requests, aiohttp, grpc, misc)
      - base-pricing-lesliespool-postgres-dev (PostgreSQL - separate)
      - base-pricing-lesliespool-redis-dev (Redis - separate)

    Ratings:
      Multi-tenant support: 4/5 - Good - critical components separated
      Filtering:           4/5 - Good - can filter critical components
      Service map:        4/5 - Good - shows critical dependencies clearly
      Complexity:        3/5 - Medium - selective configuration required
      Cost:              4/5 - Good - optimize critical high-volume components
      Debugging:         4/5 - Good - critical paths are clear
      Dashboards:        4/5 - Good - balance between simplicity and detail

    Verdict: ✅ GOOD COMPROMISE IF YOU WANT FEWER SERVICES

    :param application: Application name
    :param client: Client name
    :param env: Environment name
    :param trace_enabled: Dictionary of trace enabled flags
    :param env_config_manager: Configuration manager instance
    :return: Tuple of (service_names dict, component_names dict for tags)
    """
    print("🔍 hybrid configuration started")
    service_names: dict[str, str] = {}
    component_names: dict[str, str] = {}

    # Separate services for critical components (DB, Redis)
    if trace_enabled.get("redis"):
        redis_service = get_service_name(
            "REDIS",
            "redis",
            application,
            client,
            env,
            env_config_manager,
        )
        service_names["redis"] = redis_service
        os.environ["DD_REDIS_SERVICE"] = redis_service
        component_names["redis"] = f"{application}-{client}-redis-{env} (Redis commands)"

    if trace_enabled.get("psycopg") or trace_enabled.get("sqlalchemy"):
        postgres_service = get_service_name(
            "POSTGRES",
            "postgres",
            application,
            client,
            env,
            env_config_manager,
        )
        service_names["postgres"] = postgres_service
        # Set multiple env vars to ensure ddtrace picks it up
        # ddtrace reads: DD_PSYCOPG_SERVICE, DD_DB_SERVICE, DD_SQLALCHEMY_SERVICE
        os.environ["DD_POSTGRES_SERVICE"] = postgres_service
        os.environ["DD_PSYCOPG_SERVICE"] = postgres_service  # ddtrace uses this for psycopg
        os.environ["DD_DB_SERVICE"] = postgres_service
        if trace_enabled.get("sqlalchemy"):
            os.environ["DD_SQLALCHEMY_SERVICE"] = postgres_service
        component_names["postgres"] = f"{application}-{client}-postgres-{env} (PostgreSQL queries)"

    # Requests, aiohttp, grpc, and misc stay with main service (explicitly unset DD_*_SERVICE)
    # They will appear under core-base-pricing-lesliespool-be-dev
    # CRITICAL: Unset environment variables so they use main service (DD_SERVICE)
    if trace_enabled.get("requests"):
        # Remove DD_REQUESTS_SERVICE if it exists so requests use main service
        if "DD_REQUESTS_SERVICE" in os.environ:
            del os.environ["DD_REQUESTS_SERVICE"]
        component_names["requests"] = f"{application}-{client}-requests-{env} (HTTP requests - grouped with main)"

    if trace_enabled.get("aiohttp"):
        # Remove DD_AIOHTTP_SERVICE if it exists so aiohttp uses main service
        if "DD_AIOHTTP_SERVICE" in os.environ:
            del os.environ["DD_AIOHTTP_SERVICE"]
        component_names["aiohttp"] = f"{application}-{client}-aiohttp-{env} (async HTTP calls - grouped with main)"

    if trace_enabled.get("grpc"):
        # Remove DD_GRPC_SERVICE if it exists so grpc uses main service
        if "DD_GRPC_SERVICE" in os.environ:
            del os.environ["DD_GRPC_SERVICE"]
        component_names["grpc"] = f"{application}-{client}-grpc-{env} (gRPC calls - grouped with main)"

    # Misc service stays with main service (no separate service)
    # Remove DD_MISC_SERVICE if it exists so misc uses main service
    if "DD_MISC_SERVICE" in os.environ:
        del os.environ["DD_MISC_SERVICE"]
    component_names["misc"] = f"{application}-{client}-misc-{env} (Miscellaneous - grouped with main)"

    return service_names, component_names


def configure_service_centric(
    application: str,
    client: str,
    env: str,
    trace_enabled: dict[str, bool],
    env_config_manager: EnvConfigManager,
) -> tuple[dict[str, str], dict[str, str]]:
    """Configure Service-Centric Tracing approach (Unified View) - Rating: 3.0/5 ⭐⭐⭐

    What it does: All spans grouped under main service; components identified via
    resources/tags.

    Service structure:
      - core-base-pricing-lesliespool-be-dev (ALL spans)
        ├── POST /api/v1/strategies
        ├── postgres.query (Resource: leslies_dev)
        ├── redis.command (Resource: redis-host)
        └── requests.request (Resource: www.googleapis.com)

    Ratings:
      Multi-tenant support: 3/5 - Moderate - main service follows pattern, resources don't
      Filtering:           3/5 - Moderate - filter by resource/tag, not service
      Service map:        2/5 - Poor - everything looks like one service
      Complexity:        5/5 - Low - minimal configuration
      Cost:              3/5 - Moderate - can't optimize per component
      Debugging:         3/5 - Moderate - need to look at resources to identify components
      Dashboards:        3/5 - Moderate - need resource-based queries

    Verdict: ⚠️ NOT IDEAL FOR YOUR USE CASE

    :param application: Application name
    :param client: Client name
    :param env: Environment name
    :param trace_enabled: Dictionary of trace enabled flags
    :param env_config_manager: Configuration manager instance (kept for consistency)
    :return: Tuple of (service_names dict, component_names dict for tags)
    """
    # Ensure env_config_manager is available for future enhancements
    _ = env_config_manager

    service_names: dict[str, str] = {}
    component_names: dict[str, str] = {}

    # Don't set any DD_*_SERVICE variables - everything groups under main service
    # Components will be identified by resources (database names, hostnames, etc.)
    # CRITICAL: Explicitly unset all DD_*_SERVICE env vars to ensure everything uses main service

    print("🔍 service_centric configuration started")

    # Unset Redis service (if exists)
    if "DD_REDIS_SERVICE" in os.environ:
        del os.environ["DD_REDIS_SERVICE"]
    if trace_enabled.get("redis"):
        component_names["redis"] = f"{application}-{client}-redis-{env} (Redis - identified by resource)"

    # Unset PostgreSQL service (if exists)
    if "DD_POSTGRES_SERVICE" in os.environ:
        del os.environ["DD_POSTGRES_SERVICE"]
    if "DD_DB_SERVICE" in os.environ:
        del os.environ["DD_DB_SERVICE"]
    if "DD_SQLALCHEMY_SERVICE" in os.environ:
        del os.environ["DD_SQLALCHEMY_SERVICE"]
    if trace_enabled.get("psycopg") or trace_enabled.get("sqlalchemy"):
        component_names["postgres"] = (
            f"{application}-{client}-postgres-{env} " "(PostgreSQL - identified by database name resource)"
        )

    # Unset Requests service (if exists)
    if "DD_REQUESTS_SERVICE" in os.environ:
        del os.environ["DD_REQUESTS_SERVICE"]
    if trace_enabled.get("requests"):
        component_names["requests"] = (
            f"{application}-{client}-requests-{env} " "(HTTP requests - identified by domain resource)"
        )

    # Unset aiohttp service (if exists)
    if "DD_AIOHTTP_SERVICE" in os.environ:
        del os.environ["DD_AIOHTTP_SERVICE"]
    if trace_enabled.get("aiohttp"):
        component_names["aiohttp"] = (
            f"{application}-{client}-aiohttp-{env} " "(async HTTP calls - identified by domain resource)"
        )

    # Unset gRPC service (if exists)
    if "DD_GRPC_SERVICE" in os.environ:
        del os.environ["DD_GRPC_SERVICE"]
    if trace_enabled.get("grpc"):
        component_names["grpc"] = (
            f"{application}-{client}-grpc-{env} " "(gRPC calls - identified by service name resource)"
        )

    # Unset Misc service (if exists) - everything uses main service
    if "DD_MISC_SERVICE" in os.environ:
        del os.environ["DD_MISC_SERVICE"]
    component_names["misc"] = (
        f"{application}-{client}-misc-{env} " "(Miscellaneous - templates, unknown operations - identified by resource)"
    )

    return service_names, component_names


def configure_service_names(
    application: str,
    client: str,
    env: str,
    trace_enabled: dict[str, bool],
    env_config_manager: EnvConfigManager,
) -> tuple[dict[str, str], dict[str, str]]:
    """Configure service names - routes to appropriate approach based on DD_SERVICE_NAMING_MODE.

    Supported modes:
    - "separate" (default, 5.0/5): Explicit service naming
    - "component_tags" (4.7/5): Separate services + custom tags
    - "hybrid" (4.0/5): Selective separation
    - "service_centric" (3.0/5): Unified view

    :param application: Application name
    :param client: Client name
    :param env: Environment name
    :param trace_enabled: Dictionary of trace enabled flags
    :param env_config_manager: Configuration manager instance
    :return: Tuple of (service_names dict, component_names dict for tags)
    """
    # Get service naming mode
    service_naming_mode = get_service_naming_mode(env_config_manager)

    # Set global variable for access from other modules
    global SERVICE_NAMING_MODE
    SERVICE_NAMING_MODE = service_naming_mode

    # Route to appropriate configuration function based on mode
    mode_display_map = {
        SERVICE_NAMING_MODE_SEPARATE: "Separate Services (5.0/5)",
        SERVICE_NAMING_MODE_COMPONENT_TAGS: "Component-Based + Tags (4.7/5)",
        SERVICE_NAMING_MODE_HYBRID: "Hybrid Services (4.0/5)",
        SERVICE_NAMING_MODE_SERVICE_CENTRIC: "Service-Centric (3.0/5)",
    }
    mode_display = mode_display_map.get(service_naming_mode, service_naming_mode)
    print(f"📊 Datadog Service Naming Mode: {mode_display}")
    print(f"🔍 DEBUG: service_naming_mode = '{service_naming_mode}'")
    print(f"🔍 DEBUG: trace_enabled = {trace_enabled}")

    if service_naming_mode == SERVICE_NAMING_MODE_SEPARATE:
        return configure_separate_services(
            application,
            client,
            env,
            trace_enabled,
            env_config_manager,
        )
    elif service_naming_mode == SERVICE_NAMING_MODE_COMPONENT_TAGS:
        return configure_component_based_with_tags(
            application,
            client,
            env,
            trace_enabled,
            env_config_manager,
        )
    elif service_naming_mode == SERVICE_NAMING_MODE_HYBRID:
        return configure_hybrid_services(
            application,
            client,
            env,
            trace_enabled,
            env_config_manager,
        )
    elif service_naming_mode == SERVICE_NAMING_MODE_SERVICE_CENTRIC:
        return configure_service_centric(
            application,
            client,
            env,
            trace_enabled,
            env_config_manager,
        )
    else:
        # Fallback to separate services (default)
        print(
            f"⚠️ Unknown service naming mode: {service_naming_mode}, using 'separate'",
        )
        return configure_separate_services(
            application,
            client,
            env,
            trace_enabled,
            env_config_manager,
        )


def enable_runtime_metrics(env_config_manager: EnvConfigManager) -> None:
    """Enable Runtime Metrics if configured.

    :param env_config_manager: Configuration manager instance
    """
    # DD_RUNTIME_METRICS_ENABLED is already set in config.py from datadog.toml
    # Read it from environment variable (set by config.py) to check if enabled
    runtime_metrics_enabled = os.getenv(
        "DD_RUNTIME_METRICS_ENABLED",
        "true",
    ).lower() in ("true", "1", "yes")

    if runtime_metrics_enabled:
        # DD_RUNTIME_METRICS_RUNTIME_ID_ENABLED is already set in config.py from datadog.toml
        # Read it from environment variable (set by config.py) to check if enabled
        runtime_id_enabled = os.getenv(
            "DD_RUNTIME_METRICS_RUNTIME_ID_ENABLED",
            "true",
        ).lower() in ("true", "1", "yes")

        from ddtrace.runtime import RuntimeMetrics

        RuntimeMetrics.enable()
        print(
            "✅ Datadog Runtime Metrics enabled (GC pressure, thread count, CPU, memory)",
        )
        if runtime_id_enabled:
            print("✅ Runtime ID tagging enabled (for multi-instance deployments)")


def enable_profiler(env_config_manager: EnvConfigManager) -> None:
    """Enable Profiler if configured.

    Enable Profiler if specifically configured (for detailed performance
    analysis). Profiler shows slow functions, hotspots, memory
    allocations. Check both environment variable and settings.toml.

    :param env_config_manager: Configuration manager instance
    """
    # DD_PROFILING_ENABLED is already set in config.py from datadog.toml
    # Read it from environment variable (set by config.py) to check if enabled
    profiling_enabled = os.getenv("DD_PROFILING_ENABLED", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    if profiling_enabled:
        try:
            from ddtrace.profiling.profiler import Profiler

            Profiler().start()
            print(
                "✅ Datadog Profiler enabled (slow functions, hotspots, memory allocations)",
            )
        except ImportError:
            # Profiler might not be available in all ddtrace versions
            print(
                "⚠️ Datadog Profiler not available (ddtrace version may not support it)",
            )
        except Exception as e:
            print(f"⚠️ Datadog Profiler failed to start: {str(e)}")


def configure_instrumentation(
    application: str,
    client: str,
    env: str,
    env_config_manager: EnvConfigManager,
) -> tuple[dict[str, str], dict[str, bool]]:
    """Configure auto-instrumentation for libraries.

    Configure auto-instrumentation from settings.toml. Each setting
    controls whether that library creates a separate service in Datadog.

    :param application: Application name
    :param client: Client name
    :param env: Environment name
    :param env_config_manager: Configuration manager instance
    :return: Tuple of (service_names dict, trace_enabled dict)
    """
    import logging

    # Suppress ddtrace DEBUG logs - they're too verbose
    # Note: Datadog is disabled in local development (see initialize_datadog),
    # so these settings only apply in production/staging environments
    logging.getLogger("ddtrace").setLevel(logging.WARNING)
    logging.getLogger("ddtrace.internal").setLevel(logging.WARNING)
    logging.getLogger("ddtrace.internal.writer").setLevel(logging.WARNING)
    logging.getLogger("ddtrace.internal.telemetry").setLevel(logging.WARNING)

    # Suppress the "datadog context not present in ASGI request scope" warning
    # This warning appears when using custom spans (DD_TRACE_FASTAPI_ENABLED=false)
    # It's harmless and doesn't affect functionality
    logging.getLogger("ddtrace.contrib.asgi").setLevel(logging.ERROR)

    # Note: ddtrace.auto is imported at module level in __init__.py (before this function)
    # This ensures it's imported before other libraries are imported
    from ddtrace import patch_all

    # Get instrumentation settings from settings.toml
    trace_redis = get_bool_setting(
        CONFIG_KEY_REDIS_ENABLED,
        DEFAULT_TRACE_REDIS_ENABLED,
        env_config_manager,
    )
    trace_psycopg = get_bool_setting(
        CONFIG_KEY_PSYCOPG_ENABLED,
        DEFAULT_TRACE_PSYCOPG_ENABLED,
        env_config_manager,
    )
    trace_sqlalchemy = get_bool_setting(
        CONFIG_KEY_SQLALCHEMY_ENABLED,
        DEFAULT_TRACE_SQLALCHEMY_ENABLED,
        env_config_manager,
    )
    trace_requests = get_bool_setting(
        CONFIG_KEY_REQUESTS_ENABLED,
        DEFAULT_TRACE_REQUESTS_ENABLED,
        env_config_manager,
    )
    trace_aiohttp = get_bool_setting(
        CONFIG_KEY_AIOHTTP_ENABLED,
        DEFAULT_TRACE_AIOHTTP_ENABLED,
        env_config_manager,
    )
    trace_grpc = get_bool_setting(
        CONFIG_KEY_GRPC_ENABLED,
        DEFAULT_TRACE_GRPC_ENABLED,
        env_config_manager,
    )

    trace_enabled = {
        "redis": trace_redis,
        "psycopg": trace_psycopg,
        "sqlalchemy": trace_sqlalchemy,
        "requests": trace_requests,
        "aiohttp": trace_aiohttp,
        "grpc": trace_grpc,
    }

    # Configure service names for each instrumented library
    # Each component gets its own service name (separate services)
    service_names, component_names = configure_service_names(
        application,
        client,
        env,
        trace_enabled,
        env_config_manager,
    )

    # Get service naming mode for debug output
    service_naming_mode = get_service_naming_mode(env_config_manager)

    # DEBUG: Print service names that were configured
    print("\n" + "=" * 80)
    print("🔍 DATADOG SERVICE CONFIGURATION DEBUG")
    print("=" * 80)
    print(f"📊 Service Naming Mode: {service_naming_mode}")
    print(f"📋 Service Names Configured: {service_names}")
    print(f"🔧 Trace Enabled: {trace_enabled}")
    print("\n📍 Environment Variables Set:")
    env_vars_to_check = [
        "DD_SERVICE",
        "DD_REDIS_SERVICE",
        "DD_POSTGRES_SERVICE",
        "DD_PSYCOPG_SERVICE",
        "DD_DB_SERVICE",
        "DD_SQLALCHEMY_SERVICE",
        "DD_REQUESTS_SERVICE",
        "DD_AIOHTTP_SERVICE",
        "DD_GRPC_SERVICE",
        "DD_MISC_SERVICE",
    ]
    for var in env_vars_to_check:
        value = os.getenv(var, "NOT SET")
        status = "✅" if value != "NOT SET" else "❌"
        print(f"  {status} {var} = {value}")
    print("=" * 80 + "\n")

    # CRITICAL: Call patch_all() as early as possible after configuring service names
    # This ensures libraries are patched before they're imported elsewhere in the application.
    # If FastAPI, SQLAlchemy, or other libraries are imported before patch_all runs,
    # some instrumentation might fail to "hook" onto the classes.
    # Enable auto-instrumentation based on settings
    # NOTE: Each instrumented library creates a SEPARATE service in Datadog:
    # - Main FastAPI app: Uses DD_SERVICE (e.g., "base-pricing-lesliespool-be-dev")
    # - Redis: Uses DD_REDIS_SERVICE (pattern: "{application}-{client}-redis-{env}")
    # - PostgreSQL: Uses DD_POSTGRES_SERVICE (pattern: "{application}-{client}-postgres-{env}")
    # - Requests: Uses DD_REQUESTS_SERVICE (pattern: "{application}-{client}-requests-{env}")
    # - aiohttp: Uses DD_AIOHTTP_SERVICE (pattern: "{application}-{client}-aiohttp-{env}")
    # - Jinja2: Uses DD_SERVICE (inherits main service - template rendering is part of app)
    # All services follow the same naming pattern as DD_SERVICE for consistency.
    # Custom service names can override the pattern via settings.toml or environment variables.
    # This separation allows you to see service dependencies and performance per component.
    patch_all(
        redis=trace_redis,
        psycopg=trace_psycopg,
        sqlalchemy=trace_sqlalchemy,
        requests=trace_requests,
        aiohttp=trace_aiohttp,
        jinja2=True,  # Enable Jinja2 instrumentation - spans inherit DD_SERVICE
    )

    # CRITICAL: Configure service names in ddtrace.config AFTER patch_all()
    # Environment variables (DD_POSTGRES_SERVICE, etc.) are set above, but we also
    # need to configure ddtrace.config to ensure service names are properly applied.
    # This is especially important for hybrid mode where only some services are separate.
    try:
        from ddtrace import config

        # Configure service names for libraries that should have separate services
        # (based on what's in service_names dict - which depends on the naming mode)
        if "redis" in service_names and trace_enabled.get("redis"):
            try:
                config.redis["service_name"] = service_names["redis"]
                print(f"✅ Redis service configured: {service_names['redis']}")
            except (AttributeError, KeyError):
                pass

        if "postgres" in service_names and (trace_enabled.get("psycopg") or trace_enabled.get("sqlalchemy")):
            postgres_service = service_names["postgres"]
            try:
                # Try both service_name and service (ddtrace might use either)
                if hasattr(config, "psycopg"):
                    config.psycopg["service_name"] = postgres_service
                    # Also try setting it as service attribute if it exists
                    if hasattr(config.psycopg, "service"):
                        config.psycopg.service = postgres_service
                print(f"✅ PostgreSQL (psycopg) service configured: {postgres_service}")
            except (AttributeError, KeyError, TypeError) as e:
                print(f"⚠️ Failed to configure psycopg service: {e}")
            try:
                # Try both service_name and service (ddtrace might use either)
                if hasattr(config, "sqlalchemy"):
                    config.sqlalchemy["service_name"] = postgres_service
                    # Also try setting it as service attribute if it exists
                    if hasattr(config.sqlalchemy, "service"):
                        config.sqlalchemy.service = postgres_service
                print(
                    f"✅ PostgreSQL (sqlalchemy) service configured: {postgres_service}",
                )
            except (AttributeError, KeyError, TypeError) as e:
                print(f"⚠️ Failed to configure sqlalchemy service: {e}")

        # Only configure requests/aiohttp/grpc if they're in service_names (separate mode)
        # In hybrid mode, they're NOT in service_names, so they'll use main service
        if "requests" in service_names and trace_enabled.get("requests"):
            try:
                config.requests["service_name"] = service_names["requests"]
                print(f"✅ Requests service configured: {service_names['requests']}")
            except (AttributeError, KeyError):
                pass

        if "aiohttp" in service_names and trace_enabled.get("aiohttp"):
            try:
                config.aiohttp["service_name"] = service_names["aiohttp"]
                print(f"✅ aiohttp service configured: {service_names['aiohttp']}")
            except (AttributeError, KeyError):
                pass

        if "grpc" in service_names and trace_enabled.get("grpc"):
            try:
                config.grpc["service_name"] = service_names["grpc"]
                print(f"✅ gRPC service configured: {service_names['grpc']}")
            except (AttributeError, KeyError):
                pass

        # Print final configuration summary
        print("\n" + "=" * 80)
        print("📊 FINAL SERVICE CONFIGURATION SUMMARY")
        print("=" * 80)
        print(f"Mode: {service_naming_mode.upper()}")
        print(f"\nServices Created ({len(service_names)} total):")
        for component, service_name in service_names.items():
            enabled_status = "✅ ENABLED" if trace_enabled.get(component, False) else "⚠️ DISABLED"
            print(f"  • {component:12} → {service_name} ({enabled_status})")
        print("=" * 80 + "\n")
    except ImportError:
        # ddtrace config might not be available
        pass

    # Configure libraries based on service naming mode
    # In "separate" mode: use misc service for templates
    # In "hybrid" or "service_centric" mode: use main service for everything
    main_service_name = os.getenv("DD_SERVICE")
    misc_service_name = service_names.get("misc")
    service_naming_mode = get_service_naming_mode(env_config_manager)

    try:
        from ddtrace import config

        # Determine which service to use for templates/unknown operations
        if service_naming_mode == SERVICE_NAMING_MODE_SEPARATE and misc_service_name:
            # Separate mode: use misc service
            template_service = misc_service_name
            service_type = "misc service"
        else:
            # Hybrid or service_centric mode: use main service
            template_service = main_service_name
            service_type = "main service"

        if template_service:
            # Jinja2 template rendering
            try:
                config.jinja2["service_name"] = template_service
                print(
                    f"✅ Jinja2 template rendering configured to use {service_type}: {template_service}",
                )
            except (AttributeError, KeyError):
                pass

            # Configure other libraries that might create unnamed spans
            libraries_to_configure = [
                "celery",  # If using Celery
                "boto3",  # AWS SDK
                "botocore",  # AWS SDK core
                "elasticsearch",  # Elasticsearch client
                "pymongo",  # MongoDB
                "kafka",  # Kafka client
            ]

            configured_libs = []
            for lib_name in libraries_to_configure:
                try:
                    if hasattr(config, lib_name):
                        lib_config = getattr(config, lib_name)
                        if isinstance(lib_config, dict):
                            lib_config["service_name"] = template_service
                            configured_libs.append(lib_name)
                except Exception:
                    # Library might not be installed or config might not exist
                    pass

            if configured_libs:
                print(
                    f"✅ Additional libraries configured to use {service_type}: {', '.join(configured_libs)}",
                )

            if service_naming_mode == SERVICE_NAMING_MODE_SEPARATE:
                print(
                    f"✅ Misc service configured: {misc_service_name} " "(templates, unknown operations will use this)",
                )
            else:
                print(
                    f"✅ All operations configured to use main service: {main_service_name} "
                    f"(mode: {service_naming_mode})",
                )

    except ImportError:
        # ddtrace config might not be available
        pass

    # Store component names and misc service name for span processor
    # These descriptive names will be automatically added as tags to spans
    from . import span_processor

    span_processor.set_component_names(component_names)
    misc_service_name = service_names.get("misc")
    if misc_service_name:
        span_processor.set_misc_service_name(misc_service_name)

    # Note: DD_SERVICE environment variable (already set) acts as the default service name
    # for all spans. Any span without an explicit service name will inherit DD_SERVICE.
    # Library-specific configurations (jinja2, etc.) ensure those libraries use the main service.
    # The span processor can be called manually where needed to add component tags.

    # Component tags will be added automatically by ddtrace auto-instrumentation
    # The component names are stored and can be accessed via span_processor module
    # For manual tagging, use: from src.shared.datadog.span_processor import add_component_tags

    # Store component names globally for use in span tagging
    # These descriptive names will be added as "component.name" tags to spans
    # The tags make it easy to identify components in Datadog UI
    #
    # Component names stored:
    # - postgres: "core-base-pricing-lesliespool-postgres-dev (PostgreSQL queries)"
    # - redis: "core-base-pricing-lesliespool-redis-dev (Redis commands)"
    # - requests: "core-base-pricing-lesliespool-requests-dev (HTTP requests)"
    # - aiohttp: "core-base-pricing-lesliespool-aiohttp-dev (async HTTP calls)"
    #
    # Note: Tags are added automatically by ddtrace auto-instrumentation based on span names.
    # The component.name tags will appear in Datadog trace details.
    #
    # To add tags manually in your code:
    #   from ddtrace import tracer
    #   span = tracer.current_span()
    #   if span:
    #       span.set_tag("component.name", component_names.get("postgres"))

    return service_names, trace_enabled
