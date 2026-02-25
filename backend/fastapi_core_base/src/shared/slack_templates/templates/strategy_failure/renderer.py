"""Renderer for strategy failure Slack messages."""

from typing import Any

from src.shared.notifier.subjects import build_standard_subject
from src.shared.slack_templates.base import SlackRenderResult
from src.shared.slack_templates.shared import blocks
from src.shared.slack_templates.shared.utils import format_timestamp_ist


def build_subject(context: dict[str, Any]) -> str:
    """Build subject for strategy failure Slack messages."""
    return build_standard_subject(
        category=context.get("category", "strategy"),
        status="FAILURE",
        process_name="Strategy Simulation",
        client=context.get("client_name"),
        environment=context.get("environment"),
        app_name="BaseSmart",
        strategy_name=context["strategy_name"],
        strategy_id=context["strategy_id"],
        include_icon=True,
        include_app_name=False,
    )


def build_slack_payload(context: dict[str, Any]) -> SlackRenderResult:
    """Build Slack payload for strategy failure."""
    strategy_id = context["strategy_id"]
    strategy_name = context["strategy_name"]
    failure_type = context.get("failure_type")
    error_message = context.get("error_message")
    client_name = context.get("client_name")
    model_type = context.get("model_type")
    environment = context.get("environment")
    initiated_by_name = context.get("initiated_by_name")
    initiated_by_email = context.get("initiated_by_email")
    execution_duration = context.get("execution_duration")
    timestamp = context.get("timestamp") or format_timestamp_ist()
    use_attachments = context.get("use_attachments")
    channel = context.get("channel")

    env_display = (environment or "Prod").upper()
    slack_client_display = (client_name or "").strip().title()

    slack_fields: list[dict[str, Any]] = [
        {"type": "mrkdwn", "text": "*Strategy ID:*"},
        {"type": "mrkdwn", "text": str(strategy_id)},
        {"type": "mrkdwn", "text": "*Strategy Name:*"},
        {"type": "mrkdwn", "text": strategy_name},
        {"type": "mrkdwn", "text": "*Optimization Type:*"},
        {"type": "mrkdwn", "text": model_type or "—"},
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

    slack_fields.extend(
        [
            {"type": "mrkdwn", "text": "*Start Timestamp:*"},
            {"type": "mrkdwn", "text": context.get("start_time") or "—"},
            {"type": "mrkdwn", "text": "*Failure Timestamp:*"},
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
    if failure_type:
        slack_fields.extend(
            [
                {"type": "mrkdwn", "text": "*Failure Stage:*"},
                {"type": "mrkdwn", "text": failure_type},
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

    attachments = [{"color": "danger", "blocks": slack_blocks}]

    return SlackRenderResult(
        text=build_subject(context),
        blocks=slack_blocks,
        attachments=attachments,
        use_attachments=use_attachments,
        channel=channel,
    )
