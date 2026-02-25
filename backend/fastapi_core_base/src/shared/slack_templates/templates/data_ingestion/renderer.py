"""Renderer for data ingestion Slack messages."""

from typing import Any

from src.shared.notifier.subjects import build_standard_subject
from src.shared.slack_templates.base import SlackRenderResult
from src.shared.slack_templates.shared import blocks
from src.shared.slack_templates.shared.utils import format_timestamp_ist


def build_subject(context: dict[str, Any]) -> str:
    """Build subject for data ingestion Slack messages."""
    return build_standard_subject(
        category=context.get("category", "data_ingestion"),
        status=context["status"],
        process_name=context["process_name"],
        client=context.get("client_name"),
        environment=context.get("environment"),
        app_name="BaseSmart",
        include_icon=True,
        include_app_name=False,
    )


def build_slack_payload(context: dict[str, Any]) -> SlackRenderResult:
    process_name = context["process_name"]
    status = context["status"]
    client_name = context.get("client_name")
    environment = context.get("environment")
    initiated_by_name = context.get("initiated_by_name")
    initiated_by_email = context.get("initiated_by_email")
    execution_duration = context.get("execution_duration")
    error_message = context.get("error_message")
    timestamp = context.get("timestamp") or format_timestamp_ist()
    use_attachments = context.get("use_attachments")
    channel = context.get("channel")

    env_display = (environment or "Prod").upper()
    slack_client_display = (client_name or "").strip().title()

    slack_fields: list[dict[str, Any]] = [
        {"type": "mrkdwn", "text": "*Process Name:*"},
        {"type": "mrkdwn", "text": process_name},
        {"type": "mrkdwn", "text": "*Client:*"},
        {"type": "mrkdwn", "text": slack_client_display or "—"},
        {"type": "mrkdwn", "text": "*Environment:*"},
        {"type": "mrkdwn", "text": env_display},
    ]
    if initiated_by_name or initiated_by_email:
        initiated_by_display = (
            f"{initiated_by_name or ''} " f"{f'<{initiated_by_email}>' if initiated_by_email else ''}"
        ).strip()
        slack_fields.extend(
            [
                {"type": "mrkdwn", "text": "*Initiated by:*"},
                {"type": "mrkdwn", "text": initiated_by_display},
            ],
        )
    timestamp_label = "Failure Timestamp" if status == "failure" else "Success Timestamp"
    slack_fields.extend(
        [
            {"type": "mrkdwn", "text": "*Start Timestamp:*"},
            {"type": "mrkdwn", "text": context.get("start_time") or "—"},
            {"type": "mrkdwn", "text": f"*{timestamp_label}:*"},
            {"type": "mrkdwn", "text": timestamp},
        ],
    )
    if execution_duration:
        slack_fields.extend(
            [
                {"type": "mrkdwn", "text": "*Execution Duration:*"},
                {"type": "mrkdwn", "text": execution_duration},
            ],
        )

    slack_sections = blocks.fields_sections(slack_fields)
    slack_blocks: list[dict] = [
        blocks.header_block(build_subject(context)),
        blocks.context_block(f"*Generated at:* {timestamp}"),
    ]
    slack_blocks.extend(slack_sections)

    error_block = blocks.error_section(error_message)
    if error_block:
        slack_blocks.extend([blocks.divider_block(), error_block])

    slack_color = "good" if status == "success" else "danger"
    attachments = [{"color": slack_color, "blocks": slack_blocks}]

    return SlackRenderResult(
        text=build_subject(context),
        blocks=slack_blocks,
        attachments=attachments,
        use_attachments=use_attachments,
        channel=channel,
    )
