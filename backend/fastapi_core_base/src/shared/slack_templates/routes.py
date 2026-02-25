from fastapi import APIRouter

from src.shared.notifier.payloads import AlertChannel, AlertPayload, SlackPayload
from src.shared.notifier.settings import get_notifier_bool_setting
# TODO: Locate or implement CustomRouteHandler in src.shared
from src.shared.middleware.custom_route_handler import CustomRouteHandler
from src.shared.services.logging_service import LoggingService
from src.shared.services.notifier_service import NotifierService
from src.shared.services.slack_template_service import slack_template_service

logger = LoggingService.get_logger(__name__)

slack_templates_router = APIRouter(route_class=CustomRouteHandler)


@slack_templates_router.get("/slack-templates/test-data-ingestion-success")
async def slack_templates_test_data_ingestion_success(
    process_key: str = "DAILY_DATA_REFRESH",
    dry_run: bool = False,
):
    # 1. Fetch Configuration
    slack_enabled = await get_notifier_bool_setting(process_key, "SLACK", "ENABLED")

    if not slack_enabled:
        return {
            "success": False,
            "message": f"Slack disabled for {process_key}",
            "config": {"enabled": slack_enabled},
        }

    # 2. Render Template
    context = {
        "process_name": "Daily Data Refresh",
        "status": "success",
        "client_name": "acme",
        "environment": "prod",
        "execution_duration": "12 minutes 34 seconds",
        "process_results": [
            {
                "name": "Extract data",
                "status": "success",
                "phase": "pre-strategy-sync",
            },
            {
                "name": "Transform data",
                "status": "success",
                "phase": "post-strategy-sync",
            },
            {"name": "Load data", "status": "success"},
        ],
    }
    result = slack_template_service.render("data_ingestion", context)

    # 3. Create Payload and Send
    payload = AlertPayload(
        channels=[AlertChannel.SLACK],
        process_key=process_key,
        slack=SlackPayload(
            text=result.text,
            blocks=result.blocks,
            attachments=result.attachments,
            use_attachments=result.use_attachments,
            channel=result.channel,
        ),
    )

    success = await NotifierService.send(payload, dry_run=dry_run)
    return {
        "success": success,
        "dry_run": dry_run,
        "config_used": {
            "process_key": process_key,
            "slack_enabled": slack_enabled,
        },
        "channels": [channel.value for channel in payload.channels],
    }


@slack_templates_router.get("/slack-templates/test-data-ingestion-failure")
async def slack_templates_test_data_ingestion_failure(
    process_key: str = "BASELINE_METRICS_REFRESH",
    dry_run: bool = False,
):
    # 1. Fetch Configuration
    slack_enabled = await get_notifier_bool_setting(process_key, "SLACK", "ENABLED")

    if not slack_enabled:
        return {
            "success": False,
            "message": f"Slack disabled for {process_key}",
            "config": {"enabled": slack_enabled},
        }

    # 2. Render Template
    context = {
        "process_name": "Baseline Metrics Refresh",
        "status": "failure",
        "client_name": "acme",
        "environment": "prod",
        "execution_duration": "4 minutes 9 seconds",
        "process_results": [
            {
                "name": "Extract data",
                "status": "success",
                "phase": "pre-strategy-sync",
            },
            {
                "name": "Transform data",
                "status": "failure",
                "phase": "post-strategy-sync",
            },
            {"name": "Load data", "status": "not_run"},
        ],
        "error_message": "Failed to transform data due to invalid schema.",
    }
    result = slack_template_service.render("data_ingestion", context)

    # 3. Create Payload and Send
    payload = AlertPayload(
        channels=[AlertChannel.SLACK],
        process_key=process_key,
        slack=SlackPayload(
            text=result.text,
            blocks=result.blocks,
            attachments=result.attachments,
            use_attachments=result.use_attachments,
            channel=result.channel,
        ),
    )

    success = await NotifierService.send(payload, dry_run=dry_run)
    return {
        "success": success,
        "dry_run": dry_run,
        "config_used": {
            "process_key": process_key,
            "slack_enabled": slack_enabled,
        },
        "channels": [channel.value for channel in payload.channels],
    }


@slack_templates_router.get("/slack-templates/test-strategy-failure")
async def slack_templates_test_strategy_failure(
    process_key: str = "STRATEGY_FAILURE",
    dry_run: bool = False,
):
    # 1. Fetch Configuration
    slack_enabled = await get_notifier_bool_setting(process_key, "SLACK", "ENABLED")

    if not slack_enabled:
        return {
            "success": False,
            "message": f"Slack disabled for {process_key}",
            "config": {"enabled": slack_enabled},
        }

    # 2. Render Template
    context = {
        "strategy_id": 123,
        "strategy_name": "Promo Optimization",
        "failure_type": "optimization",
        "client_name": "acme",
        "environment": "prod",
        "model_type": "optimization_based_pricing",
        "error_message": "Failed to call Gurobi API: timeout while optimizing.",
    }
    result = slack_template_service.render("strategy_failure", context)

    # 3. Create Payload and Send
    payload = AlertPayload(
        channels=[AlertChannel.SLACK],
        process_key=process_key,
        slack=SlackPayload(
            text=result.text,
            blocks=result.blocks,
            attachments=result.attachments,
            use_attachments=result.use_attachments,
            channel=result.channel,
        ),
    )

    success = await NotifierService.send(payload, dry_run=dry_run)
    return {
        "success": success,
        "dry_run": dry_run,
        "config_used": {
            "process_key": process_key,
            "slack_enabled": slack_enabled,
        },
        "channels": [channel.value for channel in payload.channels],
    }
