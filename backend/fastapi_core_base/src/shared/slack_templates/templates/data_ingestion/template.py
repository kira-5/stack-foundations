"""Template implementation for data ingestion Slack messages."""

from typing import Any

from src.shared.slack_templates.base import SlackRenderResult
from src.shared.slack_templates.registry import register_template
from src.shared.slack_templates.templates.data_ingestion.renderer import build_slack_payload


@register_template
class DataIngestionSlackTemplate:
    """Slack template for data ingestion notifications."""

    template_key = "data_ingestion"

    def render(self, context: dict[str, Any]) -> SlackRenderResult:
        return build_slack_payload(context)
