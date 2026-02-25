"""Version management: dynamic version generation for deployment tracking."""

import os
import subprocess
from datetime import datetime

from app.configuration.config import EnvConfigManager


def _get_logger():
    """Get logger lazily (only when needed, after LoggerFactory is initialized)."""
    try:
        from app.services.logger import LoggingService

        return LoggingService.get_logger(__name__)
    except Exception:
        # Fallback to print if logger not available yet
        import logging

        return logging.getLogger(__name__)


def get_deployment_metadata() -> tuple[str | None, str | None, str | None]:
    """Get deployment metadata from environment variables (set by Ansible/CI/CD).

    :return: Tuple of (build_id, job_id, launched_by)
    """
    build_id = os.getenv("BUILD_ID") or os.getenv("DEPLOYMENT_ID") or os.getenv("REVISION_ID")
    job_id = os.getenv("JOB_ID") or os.getenv("ANSIBLE_JOB_ID")
    launched_by = os.getenv("LAUNCHED_BY") or os.getenv("DEPLOYMENT_USER") or os.getenv("USER")
    started_at = os.getenv("STARTED")
    finished_at = os.getenv("FINISHED")

    # Also try to log if logger is available
    try:
        logger = _get_logger()
        logger.info(f"Build ID: {build_id}")
        logger.info(f"Job ID: {job_id}")
        logger.info(f"Launched by: {launched_by}")
        logger.info(f"Started at: {started_at}")
        logger.info(f"Finished at: {finished_at}")
    except Exception:
        pass  # Logger not available yet, print statements above will handle it

    return build_id, job_id, launched_by


def get_git_commit_hash() -> str | None:
    """Get git commit hash (short format).

    :return: Git commit hash or None if not available
    """
    try:
        git_commit = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .strip()
        )
        return git_commit
    except Exception:
        return None


def generate_dynamic_version(
    env_config_manager: EnvConfigManager,
) -> tuple[str, str | None, str | None, str | None]:
    """Generate dynamic version for deployment tracking.

    Priority: 1. BUILD_ID/REVISION_ID (from Ansible) → 2. Git commit → 3. Timestamp

    :param env_config_manager: Configuration manager instance
    :return: Tuple of (dd_version, build_id, job_id, launched_by)
    """
    # Read DD_VERSION from datadog.toml (can be overridden by environment variable)
    dd_version = env_config_manager.get_dynamic_setting(
        "DD_VERSION",
        os.getenv("DD_VERSION", None),  # Fallback to env var if not in config
    )

    # Get deployment metadata
    build_id, job_id, launched_by = get_deployment_metadata()

    # If version is still default or not set, try to make it unique per deployment
    if not dd_version or dd_version == "1.0.0":
        deployment_timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H:%M:%S")
        # Priority 1: Use BUILD_ID/REVISION_ID from Ansible (preferred when available)
        if build_id:
            dd_version = f"{launched_by}-{build_id}-{deployment_timestamp}"
            print(f"✅ Using BUILD_ID/REVISION_ID for version: {dd_version}")
        else:
            # Priority 2: Try to get git commit hash (best for tracking code changes)
            git_commit = get_git_commit_hash()

            # Construct dynamic version: prefer git commit, then timestamp
            if git_commit:
                if launched_by:
                    dd_version = f"{launched_by}-{git_commit}-{deployment_timestamp}"
                else:
                    dd_version = f"{git_commit}-{deployment_timestamp}"
                print(f"✅ Using git commit for version: {dd_version}")
                try:
                    _get_logger().info(f"✅ Using git commit for version: {dd_version}")
                except Exception:
                    pass
            else:
                dd_version = f"{launched_by}-{deployment_timestamp}"
                print(f"✅ Using timestamp for version: {dd_version}")
                try:
                    _get_logger().info(f"✅ Using timestamp for version: {dd_version}")
                except Exception:
                    pass

    os.environ["DD_VERSION"] = str(dd_version)
    print(f"✅ Datadog Version: {dd_version}")
    try:
        _get_logger().info(f"✅ Datadog Version: {dd_version}")
    except Exception:
        pass

    return dd_version, build_id, job_id, launched_by
