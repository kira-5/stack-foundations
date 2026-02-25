"""Template implementation for strategy failure emails."""

from typing import Any

from src.shared.email_templates.base import EmailRenderResult
from src.shared.email_templates.registry import register_template
from src.shared.email_templates.templates.strategy_failure.renderer import (
    build_email_html,
    build_subject,
)


@register_template
class StrategyFailureEmailTemplate:
    """Email template for strategy processing failures."""

    template_key = "strategy_failure"

    def render(self, context: dict[str, Any]) -> EmailRenderResult:
        subject = build_subject(context)
        html = build_email_html(context)
        return EmailRenderResult(subject=subject, html=html)
