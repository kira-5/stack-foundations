"""Shared layout helpers for email templates."""


def build_email_wrapper(
    header_title: str,
    header_gradient: str,
    preheader: str,
    body_html: str,
    footer_reference: str | None = None,
    footer_title: str = "MTP Base Pricing",
) -> str:
    """Wrap body content in a common email layout."""
    footer_reference_html = ""
    if footer_reference:
        footer_reference_html = (
            '<div style="margin-bottom: 12px; display: inline-block; padding: 8px 16px; '
            "background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; "
            f'font-size: 12px; color: #64748B;">{footer_reference}</div>'
        )
    return f"""
        <div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">{preheader}</div>
        <div style="max-width: 800px; margin: 60px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);">
            <header style="padding: 20px 40px 20px 24px; background: {header_gradient}; color: #ffffff; border-bottom: 1px solid rgba(255, 255, 255, 0.1);" role="banner">
                <h1 style="font-size: 22px; font-weight: 600; margin: 0; letter-spacing: 0.5px;">
                    {header_title} <span style="font-size: 12px; font-weight: 500; opacity: 0.95; white-space: nowrap;">| {footer_title}</span>
                </h1>
            </header>
            <div style="margin: 24px 16px; margin-bottom: 20px;">
                <main style="padding: 24px;" role="main">
                    {body_html}
                </main>
            </div>
            <footer style="margin-top: 20px; padding: 20px; border-top: 1px solid #E0E0E0; font-size: 11px; color: #64748B; text-align: center; background: #F1F3F5;" role="contentinfo">
                <div style="max-width: 500px; margin: 0 auto;">
                    <div style="margin-bottom: 12px; font-size: 16px; font-weight: 700; color: #1E293B;">{footer_title}</div>
                    {footer_reference_html}
                    <div style="margin-top: 15px; font-size: 11px; color: #94A3B8;">
                        This is an automated notification. Please do not reply to this email.
                    </div>
                </div>
            </footer>
        </div>
    """
