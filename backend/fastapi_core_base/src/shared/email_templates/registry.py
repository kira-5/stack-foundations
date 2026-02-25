"""Template registry for email templates."""

from app.email_templates.base import EmailTemplate

_TEMPLATE_REGISTRY: dict[str, type[EmailTemplate]] = {}


def register_template(template_cls: type[EmailTemplate]) -> type[EmailTemplate]:
    """Register a template class."""
    template_key = getattr(template_cls, "template_key", None)
    if not template_key:
        raise ValueError("Template class must define template_key.")
    if template_key in _TEMPLATE_REGISTRY:
        raise ValueError(f"Template key already registered: {template_key}")
    _TEMPLATE_REGISTRY[template_key] = template_cls
    return template_cls


def get_template(template_key: str) -> EmailTemplate:
    """Get a template instance by key."""
    template_cls = _TEMPLATE_REGISTRY.get(template_key)
    if not template_cls:
        raise KeyError(f"Template not found: {template_key}")
    return template_cls()


def list_templates() -> list[str]:
    """List registered template keys."""
    return sorted(_TEMPLATE_REGISTRY.keys())
