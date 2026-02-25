"""Email template package."""

# Ensure templates are registered on import.
from app.email_templates.templates import (  # noqa: F401
    data_ingestion,  # noqa: F401
    strategy_failure,  # noqa: F401
)
