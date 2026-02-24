"""Tag management: global tags and deployment tags for Datadog."""

import os


def configure_global_tags(
    client: str,
    env: str,
    application: str,
    server: str,
) -> None:
    """Configure global tags applied to all traces, spans, metrics, and logs.

    :param client: Client name
    :param env: Environment name
    :param application: Application name
    :param server: Server identifier
    """
    # Global Tags - Applied to ALL traces, spans, metrics, and logs
    # Format: key1:value1,key2:value2,key3:value3
    # These tags help filter/search traces by client, environment, application, server
    global_tags = f"client:{client},env:{env},application:{application},server:{server}"

    # Add Cloud Run specific tags if running on Cloud Run
    cloud_run_tags = _get_cloud_run_tags()
    if cloud_run_tags:
        global_tags = f"{global_tags},{cloud_run_tags}"

    os.environ["DD_TAGS"] = global_tags
    print(f"✅ Datadog Global Tags: {global_tags}")


def _get_cloud_run_tags() -> str:
    """Get Cloud Run specific tags from environment variables.

    Cloud Run provides these environment variables:
    - K_SERVICE: Cloud Run service name
    - K_REVISION: Cloud Run revision name
    - K_CONFIGURATION: Cloud Run configuration name

    Returns comma-separated tags string or empty string if not on Cloud Run.
    """
    cloud_run_tags = []

    # Check if running on Cloud Run (K_SERVICE is set by Cloud Run)
    k_service = os.getenv("K_SERVICE")
    if k_service:
        cloud_run_tags.append(f"cloud_run_service:{k_service}")

    k_revision = os.getenv("K_REVISION")
    if k_revision:
        cloud_run_tags.append(f"cloud_run_revision:{k_revision}")

    k_configuration = os.getenv("K_CONFIGURATION")
    if k_configuration:
        cloud_run_tags.append(f"cloud_run_configuration:{k_configuration}")

    # Try to get region from metadata server or environment
    # Cloud Run region is typically in the service URL or can be detected
    # For now, we'll rely on environment variables if set
    cloud_run_region = os.getenv("CLOUD_RUN_REGION") or os.getenv("REGION")
    if cloud_run_region:
        cloud_run_tags.append(f"cloud_run_region:{cloud_run_region}")

    return ",".join(cloud_run_tags) if cloud_run_tags else ""


def add_deployment_tags(
    build_id: str | None,
    job_id: str | None,
    launched_by: str | None,
) -> None:
    """Add deployment metadata tags to global tags.

    :param build_id: Build/Revision ID from Ansible/CI/CD
    :param job_id: Job ID from Ansible
    :param launched_by: User who launched the deployment
    """
    deployment_tags = []

    if job_id:
        deployment_tags.append(f"job_id:{job_id}")
        os.environ["DD_DEPLOYMENT_JOB_ID"] = str(job_id)

    if launched_by:
        deployment_tags.append(f"launched_by:{launched_by}")
        os.environ["DD_DEPLOYMENT_USER"] = str(launched_by)

    if build_id:
        deployment_tags.append(f"build_id:{build_id}")
        os.environ["DD_DEPLOYMENT_BUILD_ID"] = str(build_id)

    # Append deployment tags to existing global tags
    if deployment_tags:
        existing_tags = os.getenv("DD_TAGS", "")
        if existing_tags:
            os.environ["DD_TAGS"] = f"{existing_tags},{','.join(deployment_tags)}"
        else:
            os.environ["DD_TAGS"] = ",".join(deployment_tags)
        print(f"✅ Added deployment tags: {', '.join(deployment_tags)}")
