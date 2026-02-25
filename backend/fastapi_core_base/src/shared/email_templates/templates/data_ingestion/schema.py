"""Schema for data ingestion email template context."""

from dataclasses import dataclass


@dataclass
class DataIngestionEmailContext:
    process_name: str
    status: str
    reference_id: str | None = None
    timestamp: str | None = None
    process_id: str | None = None
    client_name: str | None = None
    execution_duration: str | None = None
    initiated_by_name: str | None = None
    initiated_by_email: str | None = None
    environment: str | None = None
    traceback: str | None = None
    category: str | None = None
    error_message: str | None = None
    process_results: list[dict[str, str]] | None = None
    start_time: str | None = None
