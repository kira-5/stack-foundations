import contextvars
from contextlib import contextmanager
from typing import Generator

# Global context variable for the current tenant ID
_current_tenant_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_tenant_id", default=None
)

class TenantContext:
    """Manages the current tenant context using contextvars."""

    @staticmethod
    def set_tenant_id(tenant_id: str | None) -> contextvars.Token:
        """Sets the current tenant ID and returns a token for resetting."""
        return _current_tenant_id.set(tenant_id)

    @staticmethod
    def get_tenant_id() -> str | None:
        """Retrieves the current tenant ID from context."""
        return _current_tenant_id.get()

    @staticmethod
    def reset_tenant_id(token: contextvars.Token) -> None:
        """Resets the tenant ID to the value prior to the set operation."""
        _current_tenant_id.reset(token)

    @classmethod
    @contextmanager
    def tenant_scope(cls, tenant_id: str | None) -> Generator[str | None, None, None]:
        """Context manager to temporarily set a tenant ID."""
        token = cls.set_tenant_id(tenant_id)
        try:
            yield tenant_id
        finally:
            cls.reset_tenant_id(token)
