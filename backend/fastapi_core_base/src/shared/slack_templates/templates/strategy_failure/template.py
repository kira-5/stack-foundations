"""Template implementation for strategy failure Slack messages."""

from typing import Any

from src.shared.slack_templates.base import SlackRenderResult
from src.shared.slack_templates.registry import register_template
from src.shared.slack_templates.templates.strategy_failure.renderer import build_slack_payload


@register_template
class StrategyFailureSlackTemplate:
    """Slack template for strategy processing failures."""

    template_key = "strategy_failure"

    def render(self, context: dict[str, Any]) -> SlackRenderResult:
        return build_slack_payload(context)
