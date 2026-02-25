"""Base definitions for Slack templates."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class SlackRenderResult:
    """Rendered Slack output."""

    text: str
    blocks: list[dict[str, Any]] | None = None
    attachments: list[dict[str, Any]] | None = None
    use_attachments: bool | None = None
    channel: str | None = None


class SlackTemplate(Protocol):
    """Slack template interface."""

    template_key: str

    def render(self, context: dict[str, Any]) -> SlackRenderResult:
        """Render Slack message."""
