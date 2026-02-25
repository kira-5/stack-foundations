"""Schema for strategy failure email template context."""

from dataclasses import dataclass


@dataclass
class StrategyFailureEmailContext:
    strategy_id: int
    strategy_name: str
    failure_type: str
    error_message: str | None = None
    redirect_url: str | None = None
    traceback: str | None = None
    category: str | None = None
    can_retry: bool = False
    client_name: str | None = None
    model_type: str | None = None
    environment: str | None = None
    initiated_by_name: str | None = None
    initiated_by_email: str | None = None
    execution_duration: str | None = None
    start_time: str | None = None
    timestamp: str | None = None
