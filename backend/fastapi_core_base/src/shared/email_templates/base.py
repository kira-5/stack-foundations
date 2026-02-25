"""Base definitions for email templates."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class EmailRenderResult:
    """Rendered email output."""

    subject: str
    html: str


class EmailTemplate(Protocol):
    """Email template interface."""

    template_key: str

    def render(self, context: dict[str, Any]) -> EmailRenderResult:
        """Render email subject and HTML."""
