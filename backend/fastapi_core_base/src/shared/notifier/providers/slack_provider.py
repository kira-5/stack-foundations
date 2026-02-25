from typing import Any

import httpx

from src.shared.notifier.payloads import SlackPayload
from src.shared.notifier.settings import get_notifier_setting_value
from src.shared.services.logging_service import LoggingService

logger = LoggingService.get_logger(__name__)


async def _get_slack_webhook(process_key: str = "SYSTEM") -> str | None:
    # Try process-specific webhook first, then fall back to SYSTEM
    webhook = await get_notifier_setting_value(process_key, "SLACK", "WEBHOOK_URL")
    if webhook:
        return webhook
    return await get_notifier_setting_value("SYSTEM", "SLACK", "WEBHOOK_URL")


def _parse_bool(value: object | None, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


async def _use_slack_attachments(process_key: str = "SYSTEM") -> bool:
    val = await get_notifier_setting_value(process_key, "SLACK", "USE_ATTACHMENTS")
    if val is None and process_key != "SYSTEM":
        # Fallback to SYSTEM only if explicit process setting is missing
        val = await get_notifier_setting_value("SYSTEM", "SLACK", "USE_ATTACHMENTS")
    return _parse_bool(val, default=False)


async def _get_slack_verify_ssl(process_key: str = "SYSTEM") -> bool:
    val = await get_notifier_setting_value(process_key, "SLACK", "VERIFY_SSL")
    if val is None and process_key != "SYSTEM":
        val = await get_notifier_setting_value("SYSTEM", "SLACK", "VERIFY_SSL")
    return _parse_bool(val, default=True)


def _extract_blocks_from_attachments(
    attachments: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not attachments:
        return []
    blocks: list[dict[str, Any]] = []
    for attachment in attachments:
        attachment_blocks = attachment.get("blocks")
        if isinstance(attachment_blocks, list):
            blocks.extend(attachment_blocks)
    return blocks


async def send_slack(
    payload: SlackPayload,
    dry_run: bool = False,
    use_attachments: bool | None = None,
    process_key: str = "SYSTEM",
) -> bool:
    webhook_url = await _get_slack_webhook(process_key)
    if not webhook_url:
        logger.warning("Slack webhook URL missing; skipping Slack send.")
        return False

    if dry_run:
        logger.info("Dry-run enabled for Slack send.")
        return True

    body: dict[str, Any] = {"text": payload.text}
    if payload.channel:
        body["channel"] = payload.channel

    if use_attachments is None:
        use_attachments = await _use_slack_attachments(process_key)

    if use_attachments:
        if payload.attachments:
            body["attachments"] = payload.attachments
        elif payload.blocks:
            body["attachments"] = [{"blocks": payload.blocks}]
    else:
        if payload.blocks:
            body["blocks"] = payload.blocks
        else:
            attachment_blocks = _extract_blocks_from_attachments(payload.attachments)
            if attachment_blocks:
                body["blocks"] = attachment_blocks

    verify_ssl = await _get_slack_verify_ssl(process_key)

    # Use httpx for async HTTP requests
    try:
        async with httpx.AsyncClient(verify=verify_ssl) as client:
            response = await client.post(
                webhook_url,
                json=body,
                timeout=10.0,
            )

        if response.status_code >= 400:
            logger.error(
                f"Slack send failed: {response.status_code} {response.text}",
            )
            return False
        return True
    except httpx.RequestError as exc:
        logger.error(f"Failed to send Slack message (RequestError): {exc}")
        return False
    except Exception as exc:
        logger.error(f"Failed to send Slack message: {exc}")
        return False
