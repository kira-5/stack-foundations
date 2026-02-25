"""HTML block generators for email templates."""

import html as html_module
import re

from src.shared.email_templates.shared.email_css import get_email_css

# Align with data ingestion email: section separator and preheader
SECTION_SEPARATOR_STRATEGY = """
<hr style="margin: 24px 0; height: 1px; background: linear-gradient(to right, transparent, #e0e0e0 20%, #e0e0e0 80%, transparent); border: none;">
"""
PREHEADER_PADDING_STRATEGY = "&#160;" * 50


def _format_error_message_lines(text: str) -> str:
    """Break error message into readable lines at common delimiters."""
    escaped = html_module.escape(text)
    escaped = re.sub(r" (failed: )", r" failed:<br>  → ", escaped)
    escaped = re.sub(r" (LINE \d+:\s*)", r"<br><strong>\1</strong>", escaped)
    escaped = re.sub(r" (HINT:\s*)", r"<br><strong>HINT:</strong> ", escaped)
    escaped = re.sub(r" (CONTEXT:\s*)", r"<br><strong>CONTEXT:</strong> ", escaped)
    escaped = re.sub(
        r"\((SQLSTATE: \d+)\)",
        r'<span style="font-size: 12px; color: #7f1d1d; background: #fef2f2; padding: 2px 6px; border-radius: 4px;">(\1)</span>',
        escaped,
    )
    escaped = escaped.replace("\n", "<br>")
    return escaped


def generate_error_section(
    error_message: str | None = None,
    include_heading: bool = True,
    failed_task_name: str | None = None,
) -> str:
    """Generate HTML for error details section."""
    if not error_message:
        return ""

    error_display = _format_error_message_lines(error_message)

    block_bg = "background: linear-gradient(to right, #fdf2f2 0%, #ffffff 100%);"
    block_border = "border-left: 5px solid #DC2626;"
    error_message_style = "color: #991b1b; font-size: 14px; " "font-weight: 500; word-wrap: break-word;"
    heading_html = (
        '<div style="font-size: 12px; font-weight: 700; color: #1a1a1a; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 16px; padding-bottom: 8px; background: #fef2f2; border-radius: 6px;">Error Details <span style="font-size: 10px; font-weight: 500; color: #64748B; text-transform: none;">(Scrollable)</span></div>'
        if include_heading
        else ""
    )
    failed_task_header = ""
    if failed_task_name:
        escaped_task = html_module.escape(str(failed_task_name))
        failed_task_header = f'<div style="font-size: 15px; font-weight: 700; color: #991b1b; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #fecaca;">{escaped_task}</div>'

    scroll_container_style = (
        "min-height: 60px; max-height: 120px; overflow-y: scroll; overflow-x: auto; "
        "-webkit-overflow-scrolling: touch; padding: 12px 4px 12px 0;"
    )

    return f"""
        <div style="margin-top: 0; margin-bottom: 0; padding: 22px; {block_bg} {block_border} border-radius: 8px;">
            {heading_html}
            {failed_task_header}
            <div class="error-details-scroll" style="{scroll_container_style}">
                <div style="{error_message_style}">
                    {error_display}
                </div>
            </div>
            <div style="font-size: 10px; color: #64748B; margin-top: 10px; font-style: italic;">Scroll down for full message</div>
        </div>
    """


def generate_traceback_section(traceback: str | None = None) -> str:
    """Generate HTML for traceback section."""
    if not traceback:
        return ""

    traceback_lines = [ln for ln in traceback.strip().split("\n") if ln.strip()]
    formatted_traceback_lines = []
    mono_font = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
    exception_types = (
        "ValueError",
        "TypeError",
        "KeyError",
        "AttributeError",
        "IndexError",
        "RuntimeError",
        "OSError",
        "ImportError",
        "Exception",
    )

    for i, line in enumerate(traceback_lines):
        escaped_line = html_module.escape(line)
        indent_level = len(line) - len(line.lstrip())
        indent_style = f"padding-left: {min(indent_level, 40)}px; color: #9ca3af;" if indent_level > 0 else ""

        is_exception_line = any(line.strip().startswith(exc_type) for exc_type in exception_types)
        is_final_line = i == len(traceback_lines) - 1
        is_error_line = is_exception_line or is_final_line
        line_style = "color: #FF3131; font-weight: 700;" if is_error_line else ""

        formatted_traceback_lines.append(
            f'<div style="margin-bottom: 4px; font-size: 12px; line-height: 1.6; font-family: {mono_font}; {indent_style} {line_style}">{escaped_line}</div>',
        )

    formatted_traceback = "\n".join(formatted_traceback_lines)

    mono_font = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
    return f"""
        <div style="margin-top: 0; padding: 18px; background-color: #1A1A1A; border-left: 4px solid #DC2626; border-radius: 6px;">
            <div style="font-size: 12px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 14px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">Traceback <span style="font-size: 10px; font-weight: 500; color: #64748B; text-transform: none;">(Scrollable)</span></div>
            <div class="traceback-scroll" style="max-height: 220px; overflow-y: scroll; overflow-x: auto; -webkit-overflow-scrolling: touch; font-family: {mono_font}; font-size: 11px; line-height: 1.8; color: #d4d4d4;">
                {formatted_traceback}
            </div>
            <div style="font-size: 10px; color: #64748B; margin-top: 10px; font-style: italic;">Scroll down for full traceback</div>
        </div>
    """


def generate_retry_section(
    can_retry: bool,
    error_type_label: str | None = None,
) -> str:
    """Generate HTML for retry information section."""
    if can_retry:
        if error_type_label == "Validation Error":
            return """
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 0; margin-bottom: 0; background-color: #e8f5e9; border-left: 4px solid #2e7d32; border-radius: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);" role="alert">
                <tr>
                    <td style="padding: 20px;">
                        <table width="100%" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                                <td width="34" valign="top" style="padding-top: 2px;">
                                    <span style="font-size: 20px; line-height: 1; color: #2e7d32;" role="img" aria-label="Retry">↻</span>
                                </td>
                                <td valign="top">
                                    <div style="font-size: 14px; font-weight: 600; margin-bottom: 4px; color: #2e7d32;">Retry the strategy</div>
                                    <p style="font-size: 13px; line-height: 1.5; margin: 0; color: #388e3c;">This appears to be a temporary validation issue. Please retry the strategy.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            """
        return """
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 0; margin-bottom: 0; background-color: #e8f5e9; border-left: 4px solid #2e7d32; border-radius: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);" role="alert">
                <tr>
                    <td style="padding: 20px;">
                        <table width="100%" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                                <td width="34" valign="top" style="padding-top: 2px;">
                                    <span style="font-size: 20px; line-height: 1; color: #2e7d32;" role="img" aria-label="Retry">↻</span>
                                </td>
                                <td valign="top">
                                    <div style="font-size: 14px; font-weight: 600; margin-bottom: 4px; color: #2e7d32;">You can retry this strategy</div>
                                    <p style="font-size: 13px; line-height: 1.5; margin: 0; color: #388e3c;">This appears to be a temporary issue (network error, server busy, or worker timeout). Refreshing or retrying may resolve it.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        """
    return """
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 0; margin-bottom: 0; background-color: #fff7ed; border-left: 4px solid #d97706; border-radius: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);" role="alert">
                <tr>
                    <td style="padding: 20px;">
                        <table width="100%" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                                <td width="34" valign="top" style="padding-top: 2px;">
                                    <span style="font-size: 20px; line-height: 1; color: #d97706;" role="img" aria-label="Warning">⚠</span>
                                </td>
                                <td valign="top">
                                    <div style="font-size: 14px; font-weight: 600; margin-bottom: 4px; color: #b45309;">Code fixes required</div>
                                    <p style="font-size: 13px; line-height: 1.5; margin: 0; color: #b45309;">This looks like a code or syntax error. Retrying won’t help. Please fix the issue and rerun.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        """


def generate_button_section(
    redirect_url: str | None = None,
    can_retry: bool = False,
) -> str:
    """Generate HTML for action buttons section."""
    if not redirect_url:
        return ""

    if can_retry:
        retry_url = f"{redirect_url}?retry=true" if "?" not in redirect_url else f"{redirect_url}&retry=true"
        return f"""
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 20px; margin-bottom: 0;">
                <tr>
                    <td align="right">
                        <table cellpadding="0" cellspacing="0" border="0">
                            <tr>
                                <td style="padding-right: 12px;">
                                    <a href="{retry_url}" style="display: inline-block; padding: 14px 36px; background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3); min-width: 160px; text-align: center;">
                                        ↻ Retry
                                    </a>
                                </td>
                                <td>
                                    <a href="{redirect_url}" style="display: inline-block; padding: 14px 36px; background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 2px 4px rgba(25, 118, 210, 0.3); min-width: 160px; text-align: center;">
                                        View
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        """
    return f"""
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 20px; margin-bottom: 0;">
                <tr>
                    <td align="right">
                        <a href="{redirect_url}" style="display: inline-block; padding: 14px 36px; background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 2px 4px rgba(25, 118, 210, 0.3); min-width: 160px; text-align: center;">
                            View
                        </a>
                    </td>
                </tr>
            </table>
        """


def generate_strategy_info_table(
    strategy_id: int,
    strategy_name: str,
    model_type: str | None,
    client_name: str | None,
    environment: str | None,
    initiated_by_name: str | None,
    initiated_by_email: str | None,
    timestamp: str,
    execution_duration: str | None,
    format_model_type_func,
    start_time: str | None = None,
) -> str:
    """Generate HTML for strategy information table."""
    label_style = "padding: 5px 0; color: #666666; font-weight: 400; font-size: 13px; vertical-align: top;"
    value_style = "padding: 5px 0; color: #000000; font-weight: 700; word-break: break-word;"
    muted_style = "padding: 5px 0; color: #6b7280; font-weight: 400; font-size: 13px; " "word-break: break-word;"

    client_display = (client_name or "").capitalize() if client_name else ""
    client_row = (
        f"""<tr>
            <td width="140" style="{label_style}">Client:</td>
            <td style="{value_style}">{client_display}</td>
        </tr>"""
        if client_name
        else ""
    )

    initiated_by_display = (initiated_by_name or "N/A").capitalize()
    initiated_by_cell = initiated_by_display
    if initiated_by_email:
        initiated_by_cell += (
            f'<br><a href="mailto:{html_module.escape(initiated_by_email)}" '
            'style="display: inline-block; margin-top: 4px; padding: 2px 10px; background-color: #2563EB; '
            'color: #FFFFFF !important; font-size: 12px; font-weight: 600; text-decoration: none; border-radius: 4px;">'
            f"{html_module.escape(initiated_by_email)}</a>"
        )
    initiated_by_row = f"""<tr>
            <td width="140" style="{label_style}">Initiated By:</td>
            <td style="{value_style}">{initiated_by_cell}</td>
        </tr>"""

    execution_duration_row = (
        f"""<tr>
            <td width="140" style="{label_style}">Execution Duration:</td>
            <td style="{muted_style}">{execution_duration}</td>
        </tr>"""
        if execution_duration
        else ""
    )

    _env = (environment or "Production").strip().upper()
    if _env == "DEV":
        _env_style = "padding: 2px 10px; color: #475569; font-weight: 600; font-size: 12px; background-color: #F1F5F9; border-radius: 12px;"
    elif _env == "TEST":
        _env_style = "padding: 2px 10px; color: #065F46; font-weight: 600; font-size: 12px; background-color: #ECFDF5; border-radius: 12px;"
    elif _env == "UAT":
        _env_style = "padding: 2px 10px; color: #0369A1; font-weight: 600; font-size: 12px; background-color: #E0F2FE; border-radius: 12px;"
    else:
        _env_style = "padding: 2px 10px; color: #92400E; font-weight: 600; font-size: 12px; background-color: #FEF3C7; border-radius: 12px;"
    env_display = (environment or "Production").strip().upper()
    environment_pill_html = f'<span style="{_env_style}">{env_display}</span>'

    strategy_id_pill_style = (
        "padding: 2px 10px; color: #4338CA; font-weight: 600; font-size: 12px; "
        "background-color: #E0E7FF; border-radius: 12px;"
    )

    model_type_display = format_model_type_func(model_type) or "—"
    optimization_pill_style = (
        "padding: 2px 10px; color: #4338CA; font-weight: 600; font-size: 12px; "
        "background-color: #E0E7FF; border-radius: 12px;"
    )
    optimization_type_pill_html = (
        f'<span style="{optimization_pill_style}">{html_module.escape(model_type_display)}</span>'
    )

    timestamp_display = timestamp or "—"
    if timestamp and timestamp.endswith(" IST"):
        timestamp_display = html_module.escape(timestamp[:-4]) + " <strong style='color: #6b7280;'>IST</strong>"
    elif timestamp:
        timestamp_display = html_module.escape(timestamp)

    start_time_display = start_time or "—"
    if start_time and start_time.endswith(" IST"):
        start_time_display = html_module.escape(start_time[:-4]) + " <strong style='color: #6b7280;'>IST</strong>"
    elif start_time:
        start_time_display = html_module.escape(start_time)

    start_time_row = (
        f"""<tr>
            <td width="140" style="{label_style}">Start Timestamp:</td>
            <td style="{muted_style}">{start_time_display}</td>
        </tr>"""
        if start_time
        else ""
    )

    return f"""
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom: 24px; font-size: 14px; background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%); border: 1px solid #E2E8F0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <tr>
                <td style="padding: 20px;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                        <tr>
                            <td width="140" style="{label_style}">Strategy ID:</td>
                            <td style="padding: 5px 0; word-break: break-word;"><span style="{strategy_id_pill_style}">{strategy_id}</span></td>
                        </tr>
                        <tr>
                            <td width="140" style="{label_style}">Strategy Name:</td>
                            <td style="{value_style}">{html_module.escape(strategy_name)}</td>
                        </tr>
                        <tr>
                            <td width="140" style="{label_style}">Optimization Type:</td>
                            <td style="padding: 5px 0; word-break: break-word;">{optimization_type_pill_html}</td>
                        </tr>
                        {client_row}
                        <tr>
                            <td width="140" style="{label_style}">Environment:</td>
                            <td style="padding: 5px 0; word-break: break-word;">{environment_pill_html}</td>
                        </tr>
                        {initiated_by_row}
                        {start_time_row}
                        <tr>
                            <td width="140" style="{label_style}">Failure Timestamp:</td>
                            <td style="{muted_style}">{timestamp_display}</td>
                        </tr>
                        {execution_duration_row}
                    </table>
                </td>
            </tr>
        </table>
    """


def generate_execution_timeline(
    failure_type: str,
    timestamp: str,
    error_message: str | None = None,
    error_type_label: str = "Error",
    start_time_ist: str | None = None,
    execution_duration: str | None = None,
) -> str:
    """Generate Execution Timeline HTML (Combined Execution Timeline)."""
    failure_type_map = {
        "preprocessing": ("failed", "pending", "pending"),
        "optimization": ("completed", "failed", "pending"),
        "postprocessing": ("completed", "completed", "failed"),
    }
    states = failure_type_map.get(failure_type, ("failed", "pending", "pending"))

    steps: list[tuple[int, str, str, str, str, bool, bool]] = []
    step_names = ["Pre-Processing", "Optimization", "Post-Processing"]
    step_2_display = "Gurobi Optimization" if states[1] == "failed" else "Optimization"

    def _format_time_only(value: str | None) -> str:
        if not value:
            return ""
        if "IST" in value:
            time_part = value[11:19] if len(value) >= 19 else value.replace("IST", "")
            time_part = time_part.strip()
            return f"{time_part} IST" if time_part and "IST" not in time_part else value
        return value[11:19] if len(value) >= 19 else value

    for i, (state, name) in enumerate(
        zip(states, [step_names[0], step_2_display, step_names[2]]),
    ):
        step_num = i + 1
        if state == "completed":
            time_val = start_time_ist if i == 0 else timestamp
            start_time_only = _format_time_only(time_val)
            steps.append(
                (
                    step_num,
                    name,
                    "completed",
                    "Success",
                    start_time_only,
                    False,
                    False,
                ),
            )
        elif state == "failed":
            time_part = _format_time_only(timestamp)
            steps.append(
                (
                    step_num,
                    name,
                    "failed",
                    "Failure",
                    time_part or "—",
                    True,
                    bool(error_message),
                ),
            )
        else:
            steps.append((step_num, name, "pending", "Pending", "--:--", False, False))

    def _split_error_details(message: str) -> tuple[str, str]:
        lines = [ln.strip() for ln in message.splitlines() if ln.strip()]
        if not lines:
            return "", ""

        point_line = ""
        status_line = ""
        moved_detail = ""

        for ln in lines:
            lower = ln.lower()
            if lower.startswith("point of failure:"):
                point_line = ln.split(":", 1)[1].strip()
                continue
            if lower.startswith("status:"):
                status_line = ln.split(":", 1)[1].strip()
                continue

            if "→" in ln:
                left, right = ln.split("→", 1)
                point_line = point_line or left.strip()
                status_line = status_line or right.strip()
                continue

        if not point_line:
            point_line = lines[0]
        if not status_line and len(lines) > 1:
            status_line = lines[1]

        # Refined logic: Handle dynamic error formats.
        # 1. Strip numeric status code prefix (e.g., "500: ...", "500 ...", "404 - ...")
        #    Regex matches start of line, 3+ digits, optional space, optional separator (: or -), optional space.
        point_line = re.sub(r"^\d{3,}\s*[:|-]?\s*", "", point_line)

        # 2. Try to split "Point: Status" if a colon exists
        if ":" in point_line:
            first_part, rest = point_line.split(":", 1)
            first_part = first_part.strip()
            rest = rest.strip()

            # Heuristic: If the first part is reasonably short (likely a label/class), split it.
            # If it's a long sentence ending in a colon, keep it as the Point.
            if len(first_part) < 50:
                point_line = first_part
                moved_detail = rest

        if moved_detail:
            status_line = f"{moved_detail} - {status_line}" if status_line else moved_detail

        if moved_detail:
            status_line = f"{moved_detail} - {status_line}" if status_line else moved_detail

        def _collapse_status_redundancy(text: str) -> str:
            lowered = text.lower()
            if "gurobi api" in lowered:
                for marker in [
                    "failed to call gurobi api:",
                    "failed to call gurobi api",
                ]:
                    idx = lowered.find(marker)
                    if idx != -1:
                        text = text[:idx] + text[idx + len(marker) :]
                        lowered = text.lower()
            text = re.sub(r"\s{2,}", " ", text)
            text = re.sub(r"\s*:\s*", ": ", text)
            text = re.sub(r"\s*-\s*", " - ", text)
            return text.strip(" -:")

        def _shorten_file_list(text: str) -> str:
            markers = [
                "files do not exist:",
                "files do not exist",
                "missing files:",
                "files missing:",
            ]
            lower = text.lower()
            marker = next((m for m in markers if m in lower), "")
            if not marker:
                return text
            start_idx = lower.find(marker) + len(marker)
            prefix = text[:start_idx].rstrip()
            remainder = text[start_idx:].strip(" :")
            files = [f.strip() for f in remainder.split(",") if f.strip()]
            if len(files) <= 2:
                return text
            shown = ", ".join(files[:2])
            extra = len(files) - 2
            return f"{prefix} {shown}, +{extra} more"

        if status_line:
            status_line = _collapse_status_redundancy(status_line)
            status_line = _shorten_file_list(status_line)

        return point_line, status_line

    def _format_duration_hhmmss(duration_text: str | None) -> str:
        if not duration_text:
            return ""
        cleaned = duration_text.strip()
        if not cleaned:
            return ""
        if ":" in cleaned and any(ch.isdigit() for ch in cleaned):
            return cleaned
        hours = minutes = seconds = 0
        parts = cleaned.replace(",", "").split()
        for idx, part in enumerate(parts):
            if not part.isdigit():
                continue
            value = int(part)
            unit = parts[idx + 1] if idx + 1 < len(parts) else ""
            if unit.startswith("hour"):
                hours = value
            elif unit.startswith("minute"):
                minutes = value
            elif unit.startswith("second"):
                seconds = value
        if hours == minutes == seconds == 0:
            return ""
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    point_of_failure_detail = ""
    status_detail = ""
    status_detail_full = ""
    if error_message:
        point_line, status_line = _split_error_details(error_message.strip())
        point_of_failure_detail = html_module.escape(point_line[:120])
        status_detail_full = html_module.escape(status_line) if status_line else ""
        status_detail = html_module.escape(status_line[:140]) if status_line else ""
    error_badge_upper = html_module.escape(
        (error_type_label or "Error").upper().replace(" ", " "),
    )

    ICON_CELL_BASE = "width: 44px; min-width: 44px; " "vertical-align: middle; text-align: center; padding: 14px 0;"
    SZ = 26

    def _icon_circle(
        symbol: str,
        symbol_color: str,
        bg_color: str,
        border_style: str = "",
    ) -> str:
        border = f" border: {border_style};" if border_style else ""
        return (
            f'<table cellpadding="0" cellspacing="0" border="0" align="center" style="width: {SZ}px; height: {SZ}px; border-radius: 50%; background-color: {bg_color};{border}">'
            f'<tr><td align="center" valign="middle" height="{SZ}" style="height: {SZ}px; line-height: {SZ}px; font-size: 14px; font-weight: 700; color: {symbol_color}; font-family: Arial, sans-serif;">{symbol}</td></tr>'
            f"</table>"
        )

    def icon_completed() -> str:
        glyph = _icon_circle("&#10003;", "#ffffff", "#2e7d32")
        line_color = "#2e7d32"
        return f'<td width="44" valign="middle" style="{ICON_CELL_BASE}"><table cellpadding="0" cellspacing="0" border="0" align="center"><tr><td align="center" valign="middle" style="padding: 0;"><table cellpadding="0" cellspacing="0" border="0"><tr><td align="center" style="width: 44px;"><div style="width: 2px; height: 12px; background-color: {line_color}; margin: 0 auto;"></div></td></tr><tr><td align="center" style="padding: 0;">{glyph}</td></tr><tr><td align="center" style="width: 44px;"><div style="width: 2px; height: 12px; background-color: {line_color}; margin: 0 auto;"></div></td></tr></table></td></tr></table></td>'

    def icon_failed() -> str:
        glyph = _icon_circle("&#10007;", "#ffffff", "#dc2626")
        line_color = "#dc2626"
        return f'<td width="44" valign="middle" style="{ICON_CELL_BASE}"><table cellpadding="0" cellspacing="0" border="0" align="center"><tr><td align="center" valign="middle" style="padding: 0;"><table cellpadding="0" cellspacing="0" border="0"><tr><td align="center" style="width: 44px;"><div style="width: 2px; height: 12px; background-color: {line_color}; margin: 0 auto;"></div></td></tr><tr><td align="center" style="padding: 0;">{glyph}</td></tr><tr><td align="center" style="width: 44px;"><div style="width: 2px; height: 12px; background-color: {line_color}; margin: 0 auto;"></div></td></tr></table></td></tr></table></td>'

    def icon_pending() -> str:
        glyph = f'<div style="opacity: 0.6;">{_icon_circle("&#9675;", "#94A3B8", "#f8fafc", "1px solid #e2e8f0")}</div>'
        line_color = "#e5e7eb"
        return f'<td width="44" valign="middle" style="{ICON_CELL_BASE}"><table cellpadding="0" cellspacing="0" border="0" align="center"><tr><td align="center" valign="middle" style="padding: 0;"><table cellpadding="0" cellspacing="0" border="0"><tr><td align="center" style="width: 44px;"><div style="width: 2px; height: 12px; background-color: {line_color}; margin: 0 auto; opacity: 0.6;"></div></td></tr><tr><td align="center" style="padding: 0;">{glyph}</td></tr><tr><td align="center" style="width: 44px;"><div style="width: 2px; height: 12px; background-color: {line_color}; margin: 0 auto; opacity: 0.6;"></div></td></tr></table></td></tr></table></td>'

    CONTENT_PADDING = "14px 0 14px 16px"

    def content_completed(
        step_num: int,
        name: str,
        start_time_only: str,
        duration: str | None = None,
    ) -> str:
        duration_placeholder = duration or "--:--"
        start_lbl = f"{start_time_only}" if start_time_only else "—"
        return f"""<td valign="middle" style="padding: {CONTENT_PADDING};">
          <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
            <td valign="top" style="padding-right: 16px;">
              <div style="font-size: 11px; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">STEP {step_num} OF 3</div>
              <div style="font-weight: 500; color: #1f2937; font-size: 13px;">{html_module.escape(name)}</div>
              <div style="font-size: 12px; color: #2e7d32; font-weight: 600; margin-top: 4px;">Success</div>
            </td>
                <td align="right" valign="top" style="text-align: right; white-space: nowrap; padding-top: 0;">
              <div style="font-size: 12px; font-weight: 700; color: #2e7d32;">{duration_placeholder}</div>
              <div style="font-size: 10px; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px;">Duration</div>

              <div style="font-size: 12px; font-weight: 600; color: #4b5563; margin-top: 8px;">{start_lbl}</div>
              <div style="font-size: 10px; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px;">Start</div>

              <div style="font-size: 12px; font-weight: 600; color: #2e7d32; margin-top: 8px;">—</div>
              <div style="font-size: 10px; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px;">End</div>
            </td>
          </tr></table>
        </td>"""

    def content_failed(
        step_num: int,
        name: str,
        time_part: str,
        show_pof: bool,
        start_time_part: str,
    ) -> str:
        duration_placeholder = _format_duration_hhmmss(execution_duration) or "--:--"
        elapsed_lbl = f"{time_part}" if time_part else "—"
        start_lbl = f"{start_time_part}" if start_time_part else "—"

        pof_block = ""
        if show_pof and point_of_failure_detail:
            status_block = ""
            if status_detail:
                status_block = f"""
                  <div title="{status_detail_full}" style="margin-top: 8px; display: inline-block; max-width: 66%; font-size: 12px; color: #7f1d1d; background-color: #fef2f2; padding: 4px 8px; border-radius: 6px; border: 1px solid #fecaca; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                    <strong>Status:</strong> {status_detail}
                  </div>"""
            pof_block = f"""
          <div style="background-color: #ffffff; border-radius: 8px; padding: 14px; border: 1px solid #fcdcdc; margin-top: 14px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td width="26" valign="top" style="color: #D93025; font-size: 16px; line-height: 1;">&#8618;</td>
                <td>
                  <div style="font-size: 13px; color: #1f2937; line-height: 1.5;">
                    <strong>Point of Failure:</strong> {point_of_failure_detail}
                  </div>
                  {status_block}
                </td>
              </tr>
            </table>
          </div>"""

        return f"""<td valign="middle" style="padding: {CONTENT_PADDING};">
          <div style="padding: 16px; background-color: #fef6f6; border-radius: 10px; border: 1px solid #fcdcdc;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td valign="top" style="padding-right: 16px;">
                  <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">STEP {step_num} OF 3</div>
                  <div style="font-weight: 500; color: #7f1d1d; font-size: 13px;">
                    {html_module.escape(name)}
                    <span style="margin-left: 8px; background-color: #fff5f5; color: #b91c1c; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 700; border: 1px solid #fbcaca; text-transform: uppercase; letter-spacing: 0.04em;">
                      {error_badge_upper}
                    </span>
                  </div>
                  <div style="font-size: 12px; color: #dc2626; font-weight: 600; margin-top: 4px;">Failure</div>
                </td>
                <td align="right" valign="top" style="text-align: right; white-space: nowrap; padding-top: 0;">
                  <div style="margin-bottom: 4px;">
                    <span style="font-size: 10px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-right: 6px;">Duration</span>
                    <span style="font-size: 12px; font-weight: 700; color: #dc2626;">{duration_placeholder}</span>
                  </div>
                  <div style="margin-bottom: 4px;">
                    <span style="font-size: 10px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-right: 6px;">Start</span>
                    <span style="font-size: 12px; font-weight: 600; color: #4b5563;">{start_lbl}</span>
                  </div>
                  <div>
                    <span style="font-size: 10px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-right: 6px;">Failure</span>
                    <span style="font-size: 12px; font-weight: 600; color: #dc2626;">{elapsed_lbl}</span>
                  </div>
                </td>
              </tr>
            </table>
            {pof_block}
          </div>
        </td>"""

    def content_pending(step_num: int, name: str) -> str:
        return f"""<td valign="middle" style="padding: {CONTENT_PADDING}; opacity: 0.6;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
            <td valign="top" style="padding-right: 16px;">
              <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">STEP {step_num} OF 3</div>
              <div style="font-weight: 500; color: #64748B; font-size: 13px;">{html_module.escape(name)}</div>
              <div style="font-size: 12px; color: #94A3B8; font-weight: 500; margin-top: 4px;">Pending</div>
            </td>
            <td align="right" valign="top" style="text-align: right; white-space: nowrap; padding-top: 0;">
              <div style="font-size: 12px; font-weight: 600; color: #94A3B8;">--:--</div>
            </td>
          </tr></table>
        </td>"""

    rows_html: list[str] = []
    for idx, (
        step_num,
        name,
        state,
        _status_label,
        time_val,
        _is_failed,
        show_pof,
    ) in enumerate(steps):
        if state == "completed":
            icon = icon_completed()
            content = content_completed(step_num, name, time_val, None)
        elif state == "failed":
            icon = icon_failed()
            start_time_part = _format_time_only(start_time_ist)
            content = content_failed(
                step_num,
                name,
                time_val,
                show_pof,
                start_time_part,
            )
        else:
            icon = icon_pending()
            content = content_pending(step_num, name)
        rows_html.append(f"      <tr>\n        {icon}\n        {content}\n      </tr>")
        if idx < len(steps) - 1:
            rows_html.append(
                '      <tr><td colspan="2" style="padding: 6px 0 8px 0;"><div style="height: 1px; background-color: #EEF2F7;"></div></td></tr>',
            )

    inner = "\n".join(rows_html)
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%); border: 1px solid #E2E8F0; border-radius: 8px; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <tr>
    <td style="padding: 24px;">
      <h3 style="margin: 0 0 20px 0; color: #64748B; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">Execution Timeline</h3>
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse: collapse;">
{inner}
      </table>
    </td>
  </tr>
</table>"""


def generate_email_html(
    strategy_id: int,
    strategy_name: str,
    failure_type: str,
    timestamp: str,
    reference_id: str,
    progress_indicator: str,
    timeline: str,
    error_section: str,
    traceback_section: str,
    retry_section: str,
    button_section: str,
    strategy_info_table: str,
    failure_status_card: str = "",
) -> str:
    """Generate complete HTML email content for strategy failures."""
    css = get_email_css()
    preheader = "Strategy Simulation: MTP Base Pricing. " "Open this email to view failure details. "
    sep = SECTION_SEPARATOR_STRATEGY.strip()
    header_strategy_name = html_module.escape(strategy_name)

    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Strategy Simulation Failure</title>
            <style>
                {css}
            </style>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #F2F4F6;">
            <div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">{preheader}{PREHEADER_PADDING_STRATEGY}</div>
            <div style="max-width: 800px; margin: 60px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);">
                <header style="padding: 20px 40px 20px 24px; background: linear-gradient(135deg, #8B1E1E 0%, #5A1212 100%); color: #ffffff; border-bottom: 1px solid rgba(255, 255, 255, 0.1);" role="banner">
                    <h1 style="font-size: 22px; font-weight: 600; margin: 0; letter-spacing: 0.5px;">
                        Strategy Simulation Failure: {header_strategy_name} <span style="font-size: 12px; font-weight: 500; opacity: 0.95; white-space: nowrap;">| MTP Base Pricing</span>
                    </h1>
                </header>

                <div style="margin: 24px 16px; margin-bottom: 20px;">
                <main style="padding: 24px;" role="main">
                    {strategy_info_table}
                    {sep}
                    {timeline}
                    {sep}
                    {retry_section}
                    {sep}
                    {sep}
                    {error_section}
                    {sep}
                    {traceback_section}
                    {sep}
                    {failure_status_card}

                </main>
                </div>

                <footer style="margin-top: 20px; padding: 20px; border-top: 1px solid #E0E0E0; font-size: 11px; color: #64748B; text-align: center; background: #F1F3F5;" role="contentinfo">
                    <div style="max-width: 500px; margin: 0 auto;">
                        <div style="margin-bottom: 12px; font-size: 16px; font-weight: 700; color: #1E293B;">MTP Base Pricing</div>
                        <div style="margin-bottom: 12px; display: inline-block; padding: 8px 16px; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 12px; color: #64748B;">
                            Strategy Simulation-FAILURE | Reference ID: <strong style="color: #4338CA; font-weight: 600;">{reference_id}</strong>
                        </div>
                        <div style="margin-top: 15px; font-size: 11px; color: #94A3B8;">
                            This is an automated notification. Please do not reply to this email.
                        </div>
                    </div>
                </footer>
            </div>
        </body>
        </html>
    """
