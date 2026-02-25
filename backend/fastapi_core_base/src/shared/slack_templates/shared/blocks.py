"""Slack block helpers."""

from collections.abc import Iterable
from typing import Any


def header_block(text: str) -> dict[str, Any]:
    return {
        "type": "header",
        "text": {"type": "plain_text", "text": text},
    }


def context_block(text: str) -> dict[str, Any]:
    return {
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": text}],
    }


def divider_block() -> dict[str, Any]:
    return {"type": "divider"}


def fields_sections(
    fields: Iterable[dict[str, Any]],
    chunk_size: int = 10,
) -> list[dict]:
    sections: list[dict] = []
    buffer: list[dict[str, Any]] = []
    for field in fields:
        buffer.append(field)
        if len(buffer) == chunk_size:
            sections.append({"type": "section", "fields": buffer})
            buffer = []
    if buffer:
        sections.append({"type": "section", "fields": buffer})
    return sections


def error_section(error_message: str | None) -> dict[str, Any] | None:
    if not error_message:
        return None
    truncated_error = error_message[:1200]
    if len(error_message) > 1200:
        truncated_error = f"{truncated_error}…"
    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*Error:*\n```{truncated_error}```"},
    }
