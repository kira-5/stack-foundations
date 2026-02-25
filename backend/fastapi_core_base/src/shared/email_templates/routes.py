from fastapi import APIRouter

from src.shared.notifier.payloads import AlertChannel, AlertPayload, EmailPayload
from src.shared.notifier.settings import (
    get_notifier_bool_setting,
    get_notifier_recipients_setting,
)
# TODO: Locate or implement CustomRouteHandler in src.shared
from src.shared.middleware.custom_route_handler import CustomRouteHandler
from src.shared.services.email_template_service import email_template_service
from src.shared.services.logging_service import LoggingService
from src.shared.services.notifier_service import NotifierService

logger = LoggingService.get_logger(__name__)

email_templates_router = APIRouter()  # route_class=CustomRouteHandler


@email_templates_router.get("/email-templates/test-data-ingestion-success")
async def email_templates_test_data_ingestion_success(
    process_key: str = "DAILY_DATA_REFRESH",
    dry_run: bool = False,
):
    # 1. Fetch Configuration
    email_enabled = await get_notifier_bool_setting(process_key, "EMAIL", "ENABLED")
    email_recipients = await get_notifier_recipients_setting(
        process_key,
        "EMAIL",
        "RECIPIENTS",
    )

    if not email_enabled or not email_recipients:
        return {
            "success": False,
            "message": f"Email disabled or no recipients for {process_key}",
            "config": {"enabled": email_enabled, "recipients": email_recipients},
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
    result = email_template_service.render("data_ingestion", context)

    # 3. Create Payload and Send
    payload = AlertPayload(
        channels=[AlertChannel.EMAIL],
        process_key=process_key,
        email=EmailPayload(
            subject=result.subject,
            body=result.html,
            recipients=email_recipients,
            subtype="html",
        ),
    )

    success = await NotifierService.send(payload, dry_run=dry_run)
    return {
        "success": success,
        "dry_run": dry_run,
        "config_used": {
            "process_key": process_key,
            "email_recipients": email_recipients,
        },
        "channels": [channel.value for channel in payload.channels],
    }


@email_templates_router.get("/email-templates/test-data-ingestion-failure")
async def email_templates_test_data_ingestion_failure(
    process_key: str = "BASELINE_METRICS_REFRESH",
    dry_run: bool = False,
):
    # 1. Fetch Configuration
    email_enabled = await get_notifier_bool_setting(process_key, "EMAIL", "ENABLED")
    email_recipients = await get_notifier_recipients_setting(
        process_key,
        "EMAIL",
        "RECIPIENTS",
    )

    if not email_enabled or not email_recipients:
        return {
            "success": False,
            "message": f"Email disabled or no recipients for {process_key}",
            "config": {"enabled": email_enabled, "recipients": email_recipients},
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
        "traceback": 'Traceback (most recent call last):\n  File "pipeline.py", line 42, in run\nValueError: Invalid schema',
    }
    result = email_template_service.render("data_ingestion", context)

    # 3. Create Payload and Send
    payload = AlertPayload(
        channels=[AlertChannel.EMAIL],
        process_key=process_key,
        email=EmailPayload(
            subject=result.subject,
            body=result.html,
            recipients=email_recipients,
            subtype="html",
        ),
    )

    success = await NotifierService.send(payload, dry_run=dry_run)
    return {
        "success": success,
        "dry_run": dry_run,
        "config_used": {
            "process_key": process_key,
            "email_recipients": email_recipients,
        },
        "channels": [channel.value for channel in payload.channels],
    }


@email_templates_router.get("/email-templates/test-strategy-failure")
async def email_templates_test_strategy_failure(
    process_key: str = "STRATEGY_FAILURE",
    dry_run: bool = False,
):
    # 1. Fetch Configuration
    email_enabled = await get_notifier_bool_setting(process_key, "EMAIL", "ENABLED")
    email_recipients = await get_notifier_recipients_setting(
        process_key,
        "EMAIL",
        "RECIPIENTS",
    )

    if not email_enabled or not email_recipients:
        return {
            "success": False,
            "message": f"Email disabled or no recipients for {process_key}",
            "config": {"enabled": email_enabled, "recipients": email_recipients},
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
        "traceback": 'Traceback (most recent call last):\n  File "optimizer.py", line 88, in solve\nTimeoutError: Gurobi API timeout',
        "execution_duration": "2 minutes 18 seconds",
    }
    result = email_template_service.render("strategy_failure", context)

    # 3. Create Payload and Send
    payload = AlertPayload(
        channels=[AlertChannel.EMAIL],
        process_key=process_key,
        email=EmailPayload(
            subject=result.subject,
            body=result.html,
            recipients=email_recipients,
            subtype="html",
        ),
    )

    success = await NotifierService.send(payload, dry_run=dry_run)
    return {
        "success": success,
        "dry_run": dry_run,
        "config_used": {
            "process_key": process_key,
            "email_recipients": email_recipients,
        },
        "channels": [channel.value for channel in payload.channels],
    }
