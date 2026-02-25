"""Centralized email subject templates."""

from typing import Any


def build_standard_subject(
    category: str,
    status: str,
    process_name: str,
    client: str | None = None,
    environment: str | None = None,
    app_name: str = "BaseSmart",
    include_icon: bool = False,
    include_app_name: bool = True,
    **kwargs: Any,
) -> str:
    """Build a standardized subject line based on notification category."""
    env_display = (environment or "Prod").strip().upper()
    client_display = (client or "").strip().title()
    status_display = status.strip().upper()

    # Icon mapping (primarily for Slack)
    icon = ""
    if include_icon:
        icons = {
            "SUCCESS": "✅",
            "FAILURE": "❌",
            "WARNING": "⚠️",
        }
        icon = f"{icons.get(status_display, '')} "

    # -------------------------------------------------------------
    # New Minimal & Professional Format
    # Pattern: {STATUS}: {ProcessName} | {Client} ({Env}) | {AppName}
    # Example: SUCCESS: Baseline Metrics Refresh | Lesliespool (DEV) | BaseSmart

    # Helper to format client/env
    context_parts = []
    if client_display:
        context_parts.append(client_display)
    if env_display:
        context_parts.append(f"({env_display})")
    context_str = " ".join(context_parts) if context_parts else ""

    app_part = f" | {app_name}" if include_app_name else ""

    # Branch logic based on category
    if category == "data_ingestion":
        # Core subject: {icon}{STATUS}: {ProcessName} | {Client} ({Env}) | {AppName}
        subject_base = f"{icon}{status_display}: {process_name} | {context_str}{app_part}"
        return subject_base

    if category == "strategy":
        # Strategy context: Append specific Strategy Name/ID
        # Format: {STATUS}: {ProcessName} - {StrategyName} (ID: {ID}) | {Client} ({Env}) | {AppName}
        strategy_name = kwargs.get("strategy_name")
        strategy_id = kwargs.get("strategy_id")

        process_part = process_name
        extra_info = []
        if strategy_name:
            extra_info.append(strategy_name)
        if strategy_id:
            extra_info.append(f"(ID: {strategy_id})")

        if extra_info:
            process_part = f"{process_name} - {' '.join(extra_info)}"

        return f"{icon}{status_display}: {process_part} | {context_str}{app_part}"

    if category == "cron_job":
        # Format: {STATUS}: {ProcessName} | {Client} ({Env}) | {AppName}
        subject_base = f"{icon}{status_display}: {process_name} | {context_str}{app_part}"
        return subject_base

    # Default fallback
    subject_base = f"{icon}{status_display}: {process_name} | {context_str}{app_part}"
    return subject_base
