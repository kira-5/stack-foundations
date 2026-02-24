"""Span processor to automatically add component tags to spans and ensure service
names."""

import os
from typing import TYPE_CHECKING, Any

from ddtrace.ext import SpanTypes

# Type hint for Span - avoid direct import to prevent version compatibility issues
if TYPE_CHECKING:
    try:
        from ddtrace import Span
    except ImportError:
        # Fallback for type checking if Span is not directly importable
        Span = Any
else:
    # At runtime, use Any to avoid import errors
    Span = Any

# Component name mapping (set by instrumentation.py)
_component_names: dict[str, str] = {}

# Misc service name (for templates, unknown operations)
_misc_service_name: str | None = None


def set_component_names(component_names: dict[str, str]) -> None:
    """Set component names for span tagging.

    :param component_names: Dictionary mapping component types to
        descriptive names
    """
    global _component_names
    _component_names = component_names


def set_misc_service_name(service_name: str) -> None:
    """Set misc service name for templates and unknown operations.

    :param service_name: Misc service name (from DD_MISC_SERVICE)
    """
    global _misc_service_name
    _misc_service_name = service_name


def add_component_tags(span: Span) -> None:
    """Add component.name tag to span based on span type and ensure service name.

    This function:
    1. Ensures all spans have a service name (uses main service if unnamed)
    2. Adds component tags for known component types

    :param span: Datadog span object
    """
    if not span:
        return

    # CRITICAL: Ensure all spans have a service name
    # If span has no service or has "unnamed-python-service", use misc service
    span_service = getattr(span, "service", None)

    # Get misc service name (for templates, unknown operations)
    misc_service = _misc_service_name or os.getenv("DD_MISC_SERVICE")

    # Fix unnamed/unknown services - use misc service instead of main service
    # This keeps main service clean and focused on FastAPI request/response logic
    if not span_service or span_service in ("unnamed-python-service", "python"):
        if misc_service:
            span.service = misc_service

    span_name = span.name or ""
    span_type = span.span_type or ""

    # Map span names/types to component types
    component_type: str | None = None

    # PostgreSQL/SQLAlchemy spans
    if span_name.startswith("postgres.") or span_name.startswith("sqlalchemy."):
        component_type = "postgres"
    # Redis spans
    elif span_name.startswith("redis."):
        component_type = "redis"
    # HTTP requests (synchronous)
    elif span_name.startswith("requests.") or span_type == SpanTypes.HTTP:
        component_type = "requests"
    # Async HTTP requests
    elif span_name.startswith("aiohttp."):
        component_type = "aiohttp"
    # Jinja2 template rendering
    elif span_name.startswith("jinja2.") or ".j2" in span_name:
        component_type = "jinja2"
    # gRPC spans
    elif span_name.startswith("grpc.") or "grpc" in span_name.lower():
        component_type = "grpc"

    # Add component.name tag if we have a matching component
    if component_type and component_type in _component_names:
        component_name = _component_names[component_type]
        span.set_tag("component.name", component_name)
        span.set_tag("component.type", component_type)

        # Also add operation tag for better filtering
        if span_name:
            span.set_tag("operation", span_name)
