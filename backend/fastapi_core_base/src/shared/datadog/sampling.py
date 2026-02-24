"""Sampling configuration: per-service trace sampling rates."""

import json
import os
from typing import Any

from app.configuration.config import EnvConfigManager

from .constants import (
    CONFIG_KEY_AIOHTTP_SAMPLE_RATE,
    CONFIG_KEY_GRPC_SAMPLE_RATE,
    CONFIG_KEY_MAIN_SAMPLE_RATE,
    CONFIG_KEY_MISC_SAMPLE_RATE,
    CONFIG_KEY_POSTGRES_SAMPLE_RATE,
    CONFIG_KEY_REDIS_SAMPLE_RATE,
    CONFIG_KEY_REQUESTS_SAMPLE_RATE,
    DEFAULT_AIOHTTP_SAMPLE_RATE,
    DEFAULT_GRPC_SAMPLE_RATE,
    DEFAULT_MAIN_APP_SAMPLE_RATE,
    DEFAULT_MISC_SAMPLE_RATE,
    DEFAULT_POSTGRES_SAMPLE_RATE,
    DEFAULT_REDIS_SAMPLE_RATE,
    DEFAULT_REQUESTS_SAMPLE_RATE,
)


def get_sample_rate_setting(
    key: str,
    default: float,
    env_config_manager: EnvConfigManager,
) -> float:
    """Get sampling rate from environment or settings.toml.

    :param key: Configuration key name
    :param default: Default value if not found
    :param env_config_manager: Configuration manager instance
    :return: Sampling rate as float (0.0 to 1.0)
    """
    env_value = os.getenv(key)
    if env_value:
        try:
            return float(env_value)
        except ValueError:
            return default

    # Fall back to settings.toml
    setting_value = getattr(
        env_config_manager.environment_settings,
        key,
        default,
    )
    if isinstance(setting_value, (int, float)):
        return float(setting_value)
    if isinstance(setting_value, str):
        try:
            return float(setting_value)
        except ValueError:
            return default
    return default


def configure_sampling_rules(
    dd_service: str,
    service_names: dict[str, str],
    trace_enabled: dict[str, bool],
    env_config_manager: EnvConfigManager,
) -> None:
    """Configure per-service trace sampling rates.

    Lower sampling for high-volume services (redis, postgres) reduces
    costs and noise. Higher sampling for main app ensures full
    visibility for debugging.

    :param dd_service: Main service name
    :param service_names: Dictionary of service names by component
    :param trace_enabled: Dictionary of trace enabled flags by component
    :param env_config_manager: Configuration manager instance
    """
    # Get sampling rates for each service
    main_app_sample_rate = get_sample_rate_setting(
        CONFIG_KEY_MAIN_SAMPLE_RATE,
        DEFAULT_MAIN_APP_SAMPLE_RATE,
        env_config_manager,
    )
    redis_sample_rate = get_sample_rate_setting(
        CONFIG_KEY_REDIS_SAMPLE_RATE,
        DEFAULT_REDIS_SAMPLE_RATE,
        env_config_manager,
    )
    postgres_sample_rate = get_sample_rate_setting(
        CONFIG_KEY_POSTGRES_SAMPLE_RATE,
        DEFAULT_POSTGRES_SAMPLE_RATE,
        env_config_manager,
    )
    requests_sample_rate = get_sample_rate_setting(
        CONFIG_KEY_REQUESTS_SAMPLE_RATE,
        DEFAULT_REQUESTS_SAMPLE_RATE,
        env_config_manager,
    )
    aiohttp_sample_rate = get_sample_rate_setting(
        CONFIG_KEY_AIOHTTP_SAMPLE_RATE,
        DEFAULT_AIOHTTP_SAMPLE_RATE,
        env_config_manager,
    )
    grpc_sample_rate = get_sample_rate_setting(
        CONFIG_KEY_GRPC_SAMPLE_RATE,
        DEFAULT_GRPC_SAMPLE_RATE,
        env_config_manager,
    )
    misc_sample_rate = get_sample_rate_setting(
        CONFIG_KEY_MISC_SAMPLE_RATE,
        DEFAULT_MISC_SAMPLE_RATE,
        env_config_manager,
    )

    # Configure sampling rules per service using DD_TRACE_SAMPLING_RULES
    # Format: JSON array of rules: [{"service": "service-name", "sample_rate": 0.1}, ...]
    sampling_rules: list[dict[str, Any]] = []

    # Main app sampling (already set via DD_TRACE_SAMPLE_RATE, but include for completeness)
    if main_app_sample_rate < 1.0:
        sampling_rules.append(
            {"service": dd_service, "sample_rate": main_app_sample_rate},
        )

    # Redis sampling
    if trace_enabled.get("redis") and redis_sample_rate < 1.0:
        redis_service_name = service_names.get("redis")
        if redis_service_name:
            sampling_rules.append(
                {"service": redis_service_name, "sample_rate": redis_sample_rate},
            )

    # PostgreSQL sampling
    if (trace_enabled.get("psycopg") or trace_enabled.get("sqlalchemy")) and postgres_sample_rate < 1.0:
        postgres_service_name = service_names.get("postgres")
        if postgres_service_name:
            sampling_rules.append(
                {"service": postgres_service_name, "sample_rate": postgres_sample_rate},
            )

    # Requests sampling
    if trace_enabled.get("requests") and requests_sample_rate < 1.0:
        requests_service_name = service_names.get("requests")
        if requests_service_name:
            sampling_rules.append(
                {
                    "service": requests_service_name,
                    "sample_rate": requests_sample_rate,
                },
            )

    # aiohttp sampling
    if trace_enabled.get("aiohttp") and aiohttp_sample_rate < 1.0:
        aiohttp_service_name = service_names.get("aiohttp")
        if aiohttp_service_name:
            sampling_rules.append(
                {"service": aiohttp_service_name, "sample_rate": aiohttp_sample_rate},
            )

    # gRPC sampling
    if trace_enabled.get("grpc") and grpc_sample_rate < 1.0:
        grpc_service_name = service_names.get("grpc")
        if grpc_service_name:
            sampling_rules.append(
                {"service": grpc_service_name, "sample_rate": grpc_sample_rate},
            )

    # Misc service sampling (templates, unknown operations)
    misc_service_name = service_names.get("misc")
    if misc_service_name and misc_sample_rate < 1.0:
        sampling_rules.append(
            {"service": misc_service_name, "sample_rate": misc_sample_rate},
        )

    # Set sampling rules if any are configured
    if sampling_rules:
        os.environ["DD_TRACE_SAMPLING_RULES"] = json.dumps(sampling_rules)
        print("✅ Per-Service Sampling Rates Configured:")
        for rule in sampling_rules:
            sample_percent = rule["sample_rate"] * 100
            print(f"   - {rule['service']}: {sample_percent:.0f}%")
