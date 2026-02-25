"""Schema for data ingestion Slack template context."""

from dataclasses import dataclass


@dataclass
class DataIngestionSlackContext:
    process_name: str
    status: str
    client_name: str | None = None
    environment: str | None = None
    initiated_by_name: str | None = None
    initiated_by_email: str | None = None
    timestamp: str | None = None
    execution_duration: str | None = None
    error_message: str | None = None
    use_attachments: bool | None = None
    channel: str | None = None
    process_results: list[dict] | None = None
