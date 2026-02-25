"""Service for rendering Slack templates."""

from dataclasses import asdict, is_dataclass
from typing import Any

from src.shared.slack_templates.base import SlackRenderResult
from src.shared.slack_templates.registry import get_template


class SlackTemplateService:
    """Single entry-point for rendering Slack templates."""

    @staticmethod
    def render(template_key: str, context: Any) -> SlackRenderResult:
        if context is None:
            context_dict: dict[str, Any] = {}
        elif is_dataclass(context) and not isinstance(context, type):
            context_dict = asdict(context)
        elif isinstance(context, dict):
            context_dict = context
        else:
            raise TypeError("context must be a dict or dataclass instance")

        template = get_template(template_key)
        return template.render(context_dict)


slack_template_service = SlackTemplateService()
