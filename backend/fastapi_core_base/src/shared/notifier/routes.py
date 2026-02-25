from fastapi import APIRouter

from src.shared.notifier.payloads import AlertChannel, AlertPayload, EmailPayload, SlackPayload
from src.shared.notifier.settings import (
    get_notifier_bool_setting,
    get_notifier_recipients_setting,
)
from src.shared.middleware.custom_route_handler import CustomRouteHandler
from src.shared.services.logging_service import LoggingService
from src.shared.services.notifier_service import NotifierService

logger = LoggingService.get_logger(__name__)

notifier_router = APIRouter(route_class=CustomRouteHandler)


@notifier_router.get("/notifier")
async def notifier_test(
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

    slack_enabled = await get_notifier_bool_setting(process_key, "SLACK", "ENABLED")

    # 2. Build Payload
    channels = []
    email_payload = None
    slack_payload = None

    if email_enabled and email_recipients:
        channels.append(AlertChannel.EMAIL)
        email_payload = EmailPayload(
            subject=f"Notifier Test: {process_key}",
            body=f"Test message for {process_key}. Configured recipients: {email_recipients}",
            recipients=email_recipients,
        )

    if slack_enabled:
        channels.append(AlertChannel.SLACK)
        slack_payload = SlackPayload(
            text=f"Test message for {process_key} via Slack.",
        )

    # 3. Send if any channels enabled
    success = False
    if channels:
        payload = AlertPayload(
            channels=channels,
            email=email_payload,
            slack=slack_payload,
        )
        success = await NotifierService.send(payload, dry_run=dry_run)
    else:
        logger.warning(f"No enabled channels found for process {process_key}")

    return {
        "success": success,
        "dry_run": dry_run,
        "config_used": {
            "process_key": process_key,
            "email": {"enabled": email_enabled, "recipients": email_recipients},
            "slack": {"enabled": slack_enabled},
        },
        "channels_sent": [c.value for c in channels],
    }
