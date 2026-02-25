"""Renderer for strategy failure emails."""

import html as html_module
from datetime import datetime, timezone
from typing import Any

from src.shared.email_templates.shared import blocks
from src.shared.email_templates.shared.utils import format_timestamp_ist
from src.shared.notifier.subjects import build_standard_subject


def _is_code_syntax_error(
    error_message: str | None = None,
    traceback: str | None = None,
) -> bool:
    error_text = (error_message or "").lower()
    traceback_text = (traceback or "").lower()
    combined_text = f"{error_text} {traceback_text}"
    syntax_error_keywords = [
        "syntaxerror",
        "indentationerror",
        "taberror",
        "invalid syntax",
    ]
    return any(keyword in combined_text for keyword in syntax_error_keywords)


def _is_file_not_found_error(
    error_message: str | None = None,
    traceback: str | None = None,
) -> bool:
    error_text = (error_message or "").lower()
    traceback_text = (traceback or "").lower()
    combined_text = f"{error_text} {traceback_text}"
    file_not_found_keywords = [
        "files do not exist",
        "file not found",
        "filenotfounderror",
        "no such file",
        "cannot find file",
        "file does not exist",
        "file missing",
    ]
    return any(keyword in combined_text for keyword in file_not_found_keywords)


def determine_can_retry(
    error_message: str | None = None,
    traceback: str | None = None,
) -> bool:
    """Determine if an error can be retried based on error type."""
    error_text = (error_message or "").lower()
    traceback_text = (traceback or "").lower()
    combined_text = f"{error_text} {traceback_text}"

    if _is_code_syntax_error(error_message, traceback):
        return False

    if any(
        keyword in combined_text
        for keyword in [
            "gurobi",
            "failed to call gurobi",
            "gurobi api",
            "optimization failed",
        ]
    ):
        return True

    if _is_file_not_found_error(error_message, traceback):
        return True

    error_type_label, _ = _detect_error_type(error_message, traceback, can_retry=False)
    if error_type_label in ["Network Error", "Timeout Error"]:
        return True
    if error_type_label == "Code Error":
        return False
    if error_type_label == "Validation Error":
        return True
    return True


def _detect_error_type(
    error_message: str | None = None,
    traceback: str | None = None,
    can_retry: bool = False,
) -> tuple[str, str]:
    """Detect error type from error message and traceback."""
    error_text = (error_message or "").lower()
    traceback_text = (traceback or "").lower()
    combined_text = f"{error_text} {traceback_text}"

    if any(
        keyword in combined_text
        for keyword in [
            "network error",
            "connectionerror",
            "connection error",
            "connection refused",
            "connection timeout",
            "connection reset",
            "failed to establish",
            "unreachable",
            "dns",
        ]
    ):
        return "Network Error", "error-badge-network"

    if any(
        keyword in combined_text
        for keyword in [
            "timeout",
            "timed out",
            "timeouterror",
            "worker lost",
            "stuck",
            "exceeded",
            "deadline",
        ]
    ):
        return "Timeout Error", "error-badge-timeout"

    if _is_file_not_found_error(error_message, traceback):
        return "Validation Error", "error-badge-validation"

    if any(
        keyword in combined_text
        for keyword in [
            "validation error",
            "valueerror",
            "invalid",
            "missing required",
            "invalid format",
            "invalid data",
            "malformed",
            "parse error",
        ]
    ):
        return "Validation Error", "error-badge-validation"

    if any(
        keyword in combined_text
        for keyword in [
            "attributeerror",
            "typeerror",
            "keyerror",
            "indexerror",
            "syntaxerror",
            "indentationerror",
            "nameerror",
            "import error",
            "module not found",
            "undefined",
            "not defined",
        ]
    ):
        return "Code Error", "error-badge-code"

    if can_retry:
        return "Transient Error", "error-badge-transient"

    return "Error", "error-badge-general"


def _format_model_type(model_type: str | None) -> str:
    if not model_type:
        return "N/A"

    model_type_map = {
        "rule_based_pricing": "Rule Based Pricing",
        "optimization_based_pricing": "Optimization Based Pricing",
        "user_simulated_prices": "User Simulated Prices",
        "edit_price_and_simulate": "Edit Price and Simulate",
        "enforce_price_and_simulate": "Enforce Price and Simulate",
        "explain_report": "Explain Report",
    }

    return model_type_map.get(model_type, model_type.replace("_", " ").title())


def _get_error_severity(error_type_label: str, can_retry: bool) -> tuple[str, str]:
    if error_type_label in ["Code Error"]:
        return "Critical", "severity-critical"
    if error_type_label in ["Network Error", "Timeout Error"]:
        return "High", "severity-high"
    if error_type_label in ["Validation Error"]:
        return "Medium", "severity-medium"
    return "High" if not can_retry else "Medium", ("severity-high" if not can_retry else "severity-medium")


def build_email_html(context: dict[str, Any]) -> str:
    """Build HTML for strategy failure emails."""
    strategy_id = context["strategy_id"]
    strategy_name = context["strategy_name"]
    failure_type = context["failure_type"]
    error_message = context.get("error_message")
    traceback = context.get("traceback")
    can_retry = context.get("can_retry", False)
    client_name = context.get("client_name")
    model_type = context.get("model_type")
    environment = context.get("environment")
    initiated_by_name = context.get("initiated_by_name")
    initiated_by_email = context.get("initiated_by_email")
    execution_duration = context.get("execution_duration")
    start_time = context.get("start_time")

    failure_type_map = {
        "preprocessing": "Pre-processing",
        "optimization": "Optimization",
        "postprocessing": "Post-processing",
    }
    failure_type_display = failure_type_map.get(failure_type, "Processing")

    effective_can_retry = can_retry or determine_can_retry(
        error_message=error_message,
        traceback=traceback,
    )

    error_type_label, error_badge_class = _detect_error_type(
        error_message=error_message,
        traceback=traceback,
        can_retry=effective_can_retry,
    )

    severity_label, severity_class = _get_error_severity(
        error_type_label,
        effective_can_retry,
    )

    progress_indicator = ""  # Reserved: can be added in the future

    error_section = blocks.generate_error_section(error_message)
    traceback_section = blocks.generate_traceback_section(traceback)
    retry_section = blocks.generate_retry_section(
        effective_can_retry,
        error_type_label=error_type_label,
    )

    timestamp = context.get("timestamp") or format_timestamp_ist()
    reference_id = f"STR-{strategy_id}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    start_time_ist = None
    if start_time:
        if isinstance(start_time, str) and start_time.endswith(" IST"):
            start_time_ist = start_time
        else:
            try:
                if isinstance(start_time, str):
                    if start_time.endswith("Z"):
                        start_dt = datetime.fromisoformat(
                            start_time.replace("Z", "+00:00"),
                        )
                    else:
                        start_dt = datetime.fromisoformat(start_time)
                else:
                    start_dt = start_time
                if isinstance(start_dt, datetime):
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                    start_time_ist = format_timestamp_ist(start_dt)
            except Exception:
                pass

    timeline = blocks.generate_execution_timeline(
        failure_type=failure_type,
        timestamp=timestamp,
        error_message=error_message,
        error_type_label=error_type_label,
        start_time_ist=start_time_ist,
        execution_duration=execution_duration,
    )

    strategy_info_table = blocks.generate_strategy_info_table(
        strategy_id=strategy_id,
        strategy_name=strategy_name,
        model_type=model_type,
        client_name=client_name,
        environment=environment,
        initiated_by_name=initiated_by_name,
        initiated_by_email=initiated_by_email,
        timestamp=timestamp,
        execution_duration=execution_duration,
        format_model_type_func=_format_model_type,
        start_time=start_time_ist,
    )

    quick_stats = f"Failure during {failure_type_display}."
    quick_stats = html_module.escape(quick_stats)
    failure_status_card = f"""
            <div style="margin-top: 0; margin-bottom: 0; padding: 22px; background-color: #FFFFFF; border: 1px solid #E0E0E0; border-left: 4px solid #D93025; border-radius: 8px;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
                    <td style="vertical-align: middle; width: 100%;">
                        <div style="font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">STATUS</div>
                        <div style="color: #1f2937; font-size: 13px; line-height: 1.6; font-weight: 500; word-wrap: break-word;">
                            The strategy simulation ended in failure.<br>
                            <span style="font-size: 13px; color: #DC2626; font-weight: 700;">{quick_stats}</span>
                        </div>
                    </td>
                    <td style="vertical-align: middle; width: 140px; text-align: right; padding-left: 16px;">
                        <div class="failure-card-watermark" style="color: #b91c1c; opacity: 0.12; -ms-transform: rotate(-15deg); transform: rotate(-15deg); display: inline-block;">
                            <table cellpadding="0" cellspacing="0" border="0" align="center"><tr><td align="center" style="padding: 0;">
                                <div style="width: 120px; height: 120px; border-radius: 50%; border: 3px solid #b91c1c; background-color: rgba(185,28,28,0.12); margin: 0 auto; line-height: 120px; text-align: center; font-size: 56px;">&#10007;</div>
                                <div style="margin-top: -26px; background-color: #b91c1c; color: #ffffff; padding: 5px 14px; font-size: 11px; font-weight: 700; letter-spacing: 0.12em; text-align: center;">FAILURE</div>
                            </td></tr></table>
                        </div>
                    </td>
                </tr></table>
            </div>
            """

    html = blocks.generate_email_html(
        strategy_id=strategy_id,
        strategy_name=strategy_name,
        failure_type=failure_type,
        timestamp=timestamp,
        reference_id=reference_id,
        progress_indicator=progress_indicator,
        timeline=timeline,
        error_section=error_section,
        traceback_section=traceback_section,
        retry_section=retry_section,
        button_section="",
        strategy_info_table=strategy_info_table,
        failure_status_card=failure_status_card,
    )

    return html


def build_subject(context: dict[str, Any]) -> str:
    """Build subject for strategy failure emails."""
    return build_standard_subject(
        category=context.get("category", "strategy"),
        status="FAILURE",
        process_name="Strategy Simulation",
        client=context.get("client_name"),
        environment=context.get("environment"),
        app_name="BaseSmart",
        strategy_name=context["strategy_name"],
        strategy_id=context["strategy_id"],
    )
