"""Schema for strategy failure Slack template context."""

from dataclasses import dataclass


@dataclass
class StrategyFailureSlackContext:
    strategy_id: int
    strategy_name: str
    failure_type: str | None = None
    error_message: str | None = None
    client_name: str | None = None
    model_type: str | None = None
    environment: str | None = None
    initiated_by_name: str | None = None
    initiated_by_email: str | None = None
    execution_duration: str | None = None
    timestamp: str | None = None
    use_attachments: bool | None = None
    channel: str | None = None
