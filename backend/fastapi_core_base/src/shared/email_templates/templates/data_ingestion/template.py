"""Template implementation for data ingestion emails."""

from typing import Any

from src.shared.email_templates.base import EmailRenderResult
from src.shared.email_templates.registry import register_template
from src.shared.email_templates.templates.data_ingestion.renderer import (
    build_email_html,
    build_subject,
)


@register_template
class DataIngestionEmailTemplate:
    """Email template for data ingestion notifications."""

    template_key = "data_ingestion"

    def render(self, context: dict[str, Any]) -> EmailRenderResult:
        subject = build_subject(context)
        html = build_email_html(context)
        return EmailRenderResult(subject=subject, html=html)
