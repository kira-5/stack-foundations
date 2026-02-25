from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AlertChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"


@dataclass(frozen=True)
class EmailAttachment:
    filename: str
    content: bytes
    mime_type: str = "application/octet-stream"


@dataclass(frozen=True)
class EmailPayload:
    subject: str
    body: str
    recipients: list[str]
    subtype: str = "html"
    attachments: list[EmailAttachment] = field(default_factory=list)


@dataclass(frozen=True)
class SlackPayload:
    text: str
    channel: str | None = None
    blocks: list[dict[str, Any]] | None = None
    attachments: list[dict[str, Any]] | None = None
    use_attachments: bool | None = None


@dataclass(frozen=True)
class AlertPayload:
    channels: Iterable[AlertChannel]
    process_key: str = "SYSTEM"
    email: EmailPayload | None = None
    slack: SlackPayload | None = None
