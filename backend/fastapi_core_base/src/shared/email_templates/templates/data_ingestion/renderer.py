"""Renderer for data ingestion emails."""

import html as html_module
from datetime import datetime, timezone
from typing import Any

from src.shared.email_templates.shared import blocks
from src.shared.email_templates.shared.email_css import get_email_css
from src.shared.email_templates.shared.utils import format_timestamp_ist
from src.shared.notifier.subjects import build_standard_subject

# Section separator (shared by Daily Data Refresh and Baseline Metrics Refresh emails)
SECTION_SEPARATOR = """
<hr style="margin: 24px 0; height: 1px; background: linear-gradient(to right, transparent, #e0e0e0 20%, #e0e0e0 80%, transparent); border: none;">
"""

# Preheader padding: non-breaking spaces to fill any remaining preview space
PREHEADER_PADDING = "&#160;" * 50


def _generate_info_table(
    process_name: str,
    process_id: str | None = None,
    client_name: str | None = None,
    timestamp: str = "",
    execution_duration: str | None = None,
    initiated_by_name: str | None = None,
    initiated_by_email: str | None = None,
    environment: str | None = None,
    start_time: str | None = None,
    status: str = "success",
    additional_info: dict[str, str] | None = None,
) -> str:
    """Generate HTML for process information table."""
    label_style = "padding: 5px 0; color: #666666; font-weight: 400; font-size: 13px; vertical-align: top;"
    value_style = "padding: 5px 0; color: #000000; font-weight: 700; word-break: break-word;"
    muted_text_style = "padding: 5px 0; color: #6b7280; font-weight: 400; font-size: 13px; " "word-break: break-word;"
    _env = (environment or "Production").strip().upper()
    if _env == "DEV":
        env_pill_style = (
            "padding: 2px 10px; color: #475569; font-weight: 600; font-size: 12px; "
            "background-color: #F1F5F9; border-radius: 12px;"
        )
    elif _env == "TEST":
        env_pill_style = (
            "padding: 2px 10px; color: #065F46; font-weight: 600; font-size: 12px; "
            "background-color: #ECFDF5; border-radius: 12px;"
        )
    elif _env == "UAT":
        env_pill_style = (
            "padding: 2px 10px; color: #0369A1; font-weight: 600; font-size: 12px; "
            "background-color: #E0F2FE; border-radius: 12px;"
        )
    else:
        env_pill_style = (
            "padding: 2px 10px; color: #92400E; font-weight: 600; font-size: 12px; "
            "background-color: #FEF3C7; border-radius: 12px;"
        )
    process_id_pill_style = (
        "padding: 2px 10px; color: #4338CA; font-weight: 600; font-size: 12px; "
        "background-color: #E0E7FF; border-radius: 12px;"
    )

    process_id_row = (
        f"""<tr>
            <td width="140" style="{label_style}">Process ID:</td>
            <td style="padding: 5px 0; word-break: break-word;"><span style="{process_id_pill_style}">{process_id}</span></td>
        </tr>"""
        if process_id
        else ""
    )

    client_display = (client_name or "").capitalize() if client_name else ""
    client_row = (
        f"""<tr>
            <td width="140" style="{label_style}">Client:</td>
            <td style="{value_style}">{client_display}</td>
        </tr>"""
        if client_name
        else ""
    )

    initiated_by_content = (initiated_by_name or "N/A").capitalize()
    if initiated_by_email and initiated_by_name:
        initiated_by_content += f'<br><a href="mailto:{initiated_by_email}" style="display: inline-block; margin-top: 4px; padding: 2px 10px; background-color: #2563EB; color: #FFFFFF !important; font-size: 12px; font-weight: 600; text-decoration: none; border-radius: 4px;">{initiated_by_email}</a>'
    initiated_by_row = (
        f"""<tr>
            <td width="140" style="{label_style}">Initiated By:</td>
            <td style="{value_style}">{initiated_by_content}</td>
        </tr>"""
        if initiated_by_name
        else ""
    )

    execution_duration_row = (
        f"""<tr>
            <td width="140" style="{label_style}">Execution Duration:</td>
            <td style="{muted_text_style}">{execution_duration}</td>
        </tr>"""
        if execution_duration
        else ""
    )

    env_display = (environment or "Production").upper()
    environment_row = f"""<tr>
            <td width="140" style="{label_style}">Environment:</td>
            <td style="padding: 5px 0; word-break: break-word;"><span style="{env_pill_style}">{env_display}</span></td>
        </tr>"""

    additional_rows = ""
    if additional_info:
        for key, value in additional_info.items():
            if key == "Tenant ID":
                continue
            additional_rows += f"""<tr>
            <td width="140" style="{label_style}">{key}:</td>
            <td style="{value_style}">{value}</td>
        </tr>"""

    timestamp_display = timestamp or ""
    if timestamp and timestamp.endswith(" IST"):
        timestamp_display = timestamp[:-4] + " <strong style='color: #6b7280;'>IST</strong>"

    timestamp_label = "Failure Timestamp" if status == "failure" else "Success Timestamp"
    timestamp_row = f"""<tr>
            <td width="140" style="{label_style}">{timestamp_label}:</td>
            <td style="{muted_text_style}">{timestamp_display or "—"}</td>
        </tr>"""

    start_time_display = start_time or ""
    if start_time and start_time.endswith(" IST"):
        start_time_display = start_time[:-4] + " <strong style='color: #6b7280;'>IST</strong>"
    start_time_row = (
        f"""<tr>
            <td width="140" style="{label_style}">Start Timestamp:</td>
            <td style="{muted_text_style}">{start_time_display}</td>
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
                            <td width="140" style="{label_style}">Process Name:</td>
                            <td style="{value_style}">{process_name}</td>
                        </tr>
                        {process_id_row}
                        {client_row}
                        {environment_row}
                        {initiated_by_row}
                        {start_time_row}
                        {timestamp_row}
                        {execution_duration_row}
                        {additional_rows}
                    </table>
                </td>
            </tr>
        </table>
        """ + SECTION_SEPARATOR


def _generate_process_list_html(
    process_results: list[dict[str, str]] | None = None,
) -> str:
    """Generate HTML for process execution summary."""
    if not process_results:
        return ""

    rows = []
    for item in process_results:
        name = item.get("name", "Unknown")
        status = item.get("status", "unknown")
        phase = item.get("phase", "")

        if status == "success":
            icon = "&#10003;"
            status_text = "Success"
            border_style = "border-left: 4px solid #2e7d32;"
            bg_style = "background: linear-gradient(to right, #f0fdf4 0%, #ffffff 100%);"
            status_style = "background-color: #e8f5e9; color: #2e7d32;"
            name_style = "font-weight: 500; color: #1f2937; word-break: break-word;"
            icon_color = "color: #2e7d32;"
        elif status == "failure":
            icon = "&#10007;"
            status_text = "Failure"
            border_style = "border-left: 4px solid #ef4444;"
            bg_style = "background-color: #fef2f2;"
            status_style = "background-color: #dc2626; color: #ffffff; font-weight: 700;"
            name_style = "font-weight: 500; color: #991b1b; word-break: break-word;"
            icon_color = "color: #dc2626;"
        else:
            icon = "&#9675;"
            status_text = "Not Run"
            border_style = "border-left: 4px solid #e5e7eb;"
            bg_style = "background-color: #f9fafb;"
            status_style = (
                "background-color: #f3f4f6; color: #94A3B8; font-weight: 500; "
                "padding: 2px 6px; border-radius: 4px; border: 1px solid #e5e7eb;"
            )
            name_style = "font-weight: 500; color: #A0AEC0; word-break: break-word;"
            icon_color = "color: #A0AEC0;"
        row_opacity = "opacity: 0.6;" if status not in ("success", "failure") else ""

        if status == "success":
            if phase == "pre-strategy-sync":
                phase_style = "background-color: #E0F2FE; color: #0369A1;"
            elif phase == "post-strategy-sync":
                phase_style = "background-color: #D1FAE5; color: #065F46;"
            else:
                phase_style = "background-color: #f3f4f6; color: #6b7280;"
        elif status == "failure":
            if phase in ("pre-strategy-sync", "post-strategy-sync"):
                phase_style = "background-color: #fee2e2; color: #991b1b;"
            else:
                phase_style = "background-color: #fee2e2; color: #991b1b;"
        else:
            if phase:
                phase_style = "background-color: #F1F5F9; color: #94A3B8;"
            else:
                phase_style = "background-color: #F1F5F9; color: #94A3B8;"
        phase_badge = (
            f'<span style="font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 4px; '
            f'{phase_style} margin-left: 8px; text-transform: uppercase; letter-spacing: 0.5px;">{phase}</span>'
            if phase
            else ""
        )
        rows.append(
            f"""
                <tr>
                    <td style="padding: 8px 14px 8px 8px; {border_style} {bg_style} {row_opacity} border-radius: 6px; font-size: 13px;">
                        <table width="100%" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                                <td width="28" style="font-size: 16px; font-weight: 700; vertical-align: middle; text-align: center; padding-right: 12px;"><span style="{icon_color}">{icon}</span></td>
                                <td style="{name_style}">{name}{phase_badge}</td>
                                <td width="68" align="right" style="font-size: 11px; font-weight: 600; padding: 2px 6px; border-radius: 4px; text-align: center; {status_style}">{status_text}</td>
                            </tr>
                        </table>
                    </td>
                </tr>
                """,
        )

    rows_html = "".join(rows)

    return f"""
        <div style="margin-top: 24px; margin-bottom: 24px; padding: 20px; border: 1px solid #E2E8F0; border-radius: 8px; background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);">
            <div style="font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px;">Process Execution Summary</div>
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-spacing: 0 4px;">
                {rows_html}
            </table>
        </div>
        """ + SECTION_SEPARATOR


def build_email_html(context: dict[str, Any]) -> str:
    """Build data ingestion email HTML."""
    css = get_email_css()
    process_name = context["process_name"]
    status = context["status"]
    process_id = context.get("process_id")
    client_name = context.get("client_name")
    execution_duration = context.get("execution_duration")
    initiated_by_name = context.get("initiated_by_name")
    initiated_by_email = context.get("initiated_by_email")
    environment = context.get("environment")
    additional_info = context.get("additional_info")
    process_results = context.get("process_results")
    error_message = context.get("error_message")
    traceback = context.get("traceback")

    timestamp = context.get("timestamp") or format_timestamp_ist()
    reference_id = (
        context.get("reference_id") or process_id or (f"DI-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    )

    start_time = context.get("start_time")

    info_table = _generate_info_table(
        process_name=process_name,
        process_id=process_id,
        client_name=client_name,
        timestamp=timestamp,
        start_time=start_time,
        status=status,
        execution_duration=execution_duration,
        initiated_by_name=initiated_by_name,
        initiated_by_email=initiated_by_email,
        environment=environment,
        additional_info=additional_info,
    )

    process_list = _generate_process_list_html(process_results=process_results)

    error_section = ""
    traceback_section = ""
    if status == "failure":
        failed_task_name = None
        if process_results:
            for item in process_results:
                if item.get("status") == "failure":
                    failed_task_name = item.get("name")
                    break
        error_section = blocks.generate_error_section(
            error_message,
            include_heading=True,
            failed_task_name=failed_task_name,
        )
        traceback_section = blocks.generate_traceback_section(traceback)

    header_gradient = (
        "linear-gradient(135deg, #1E5128 0%, #4E944F 100%)"
        if status == "success"
        else "linear-gradient(135deg, #8B1E1E 0%, #5A1212 100%)"
    )

    header_title = f"{process_name} Success" if status == "success" else f"{process_name} Failure"

    preheader = "Data Ingestion Source: MTP Base Pricing. " "Open this email to view the reports details. "

    success_message = ""
    if status == "success":
        total_steps = len(process_results) if process_results else 0
        completed_steps = sum(1 for r in process_results if r.get("status") == "success") if process_results else 0
        duration_text = (execution_duration or "").strip()
        if total_steps and completed_steps is not None:
            quick_stats = f"Verified {completed_steps}/{total_steps} steps completed"
            quick_stats += f" in {duration_text}." if duration_text else "."
        else:
            quick_stats = f"Completed in {duration_text}." if duration_text else "All steps completed successfully."
        quick_stats = html_module.escape(quick_stats)
        success_message = f"""
            <div style="margin-top: 0; margin-bottom: 0; padding: 22px; background-color: #FFFFFF; border: 1px solid #E0E0E0; border-left: 4px solid #34A853; border-radius: 8px;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
                    <td style="vertical-align: middle; width: 100%;">
                        <div style="font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">STATUS</div>
                        <div style="color: #1f2937; font-size: 13px; line-height: 1.6; font-weight: 500; word-wrap: break-word;">
                            The {process_name} process completed successfully.<br>
                            <span style="font-size: 13px; color: #2e7d32; font-weight: 700;">{quick_stats}</span>
                        </div>
                    </td>
                    <td style="vertical-align: middle; width: 140px; text-align: right; padding-left: 16px;">
                        <div class="success-card-watermark" style="color: #2e7d32; opacity: 0.12; -ms-transform: rotate(-15deg); transform: rotate(-15deg); display: inline-block;">
                            <table cellpadding="0" cellspacing="0" border="0" align="center"><tr><td align="center" style="padding: 0;">
                                <div style="width: 120px; height: 120px; border-radius: 50%; border: 3px solid #2e7d32; background-color: rgba(46,125,50,0.15); margin: 0 auto; line-height: 120px; text-align: center; font-size: 56px;">&#10003;</div>
                                <div style="margin-top: -26px; background-color: #2e7d32; color: #ffffff; padding: 5px 14px; font-size: 11px; font-weight: 700; letter-spacing: 0.12em; text-align: center;">SUCCESS</div>
                            </td></tr></table>
                        </div>
                    </td>
                </tr></table>
            </div>
            """

    failure_status_message = ""
    if status == "failure":
        total_steps = len(process_results) if process_results else 0
        completed_before_failure = 0
        if process_results:
            for r in process_results:
                if r.get("status") == "failure":
                    break
                if r.get("status") == "success":
                    completed_before_failure += 1
        if total_steps:
            failure_quick_stats = f"{completed_before_failure}/{total_steps} steps completed before failure."
        else:
            failure_quick_stats = "Process did not complete successfully."
        failure_quick_stats = html_module.escape(failure_quick_stats)
        failure_status_message = f"""
            <div style="margin-top: 0; margin-bottom: 0; padding: 22px; background-color: #FFFFFF; border: 1px solid #E0E0E0; border-left: 4px solid #D93025; border-radius: 8px;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
                    <td style="vertical-align: middle; width: 100%;">
                        <div style="font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">STATUS</div>
                        <div style="color: #1f2937; font-size: 13px; line-height: 1.6; font-weight: 500; word-wrap: break-word;">
                            The {process_name} process ended in failure.<br>
                            <span style="font-size: 13px; color: #DC2626; font-weight: 700;">{failure_quick_stats}</span>
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

    return (
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{header_title}</title>
            <style>
                {css}
            </style>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #F2F4F6;">
            <div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">{preheader}{PREHEADER_PADDING}</div>
            <div style="max-width: 800px; margin: 60px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);">
                <header style="padding: 20px 40px 20px 24px; background: {header_gradient}; color: #ffffff; border-bottom: 1px solid rgba(255, 255, 255, 0.1);" role="banner">
                    <h1 style="font-size: 22px; font-weight: 600; margin: 0; letter-spacing: 0.5px;">
                        {header_title} <span style="font-size: 12px; font-weight: 500; opacity: 0.95; white-space: nowrap;">| MTP Base Pricing</span>
                    </h1>
                </header>

                <div style="margin: 24px 16px; margin-bottom: 20px;">
                <main style="padding: 24px;" role="main">
                    {info_table}

                    {process_list}

                    {success_message}

                    """
        + (SECTION_SEPARATOR if error_section else "")
        + f"""
                    {error_section}
                    """
        + (SECTION_SEPARATOR if (error_section and traceback_section) else "")
        + f"""
                    {traceback_section}
                    """
        + (SECTION_SEPARATOR if failure_status_message else "")
        + f"""
                    {failure_status_message}
                    """
        + f"""
                </main>
                </div>

                <footer style="margin-top: 20px; padding: 20px; border-top: 1px solid #E0E0E0; font-size: 11px; color: #64748B; text-align: center; background: #F1F3F5;" role="contentinfo">
                    <div style="max-width: 500px; margin: 0 auto;">
                        <div style="margin-bottom: 12px; font-size: 16px; font-weight: 700; color: #1E293B;">MTP Base Pricing</div>
                        <div style="margin-bottom: 12px; display: inline-block; padding: 8px 16px; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 12px; color: #64748B;">
                            {process_name}-{status.upper()} | Reference ID: <strong style="color: #4338CA; font-weight: 600;">{reference_id}</strong>
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
    )


def build_subject(context: dict[str, Any]) -> str:
    """Build subject for data ingestion emails."""
    return build_standard_subject(
        category=context.get("category", "data_ingestion"),
        status=context["status"],
        process_name=context["process_name"],
        client=context.get("client_name"),
        environment=context.get("environment"),
        app_name="BaseSmart",
    )
