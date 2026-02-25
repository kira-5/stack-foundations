import smtplib
from email.message import EmailMessage

from app.configuration.config import env_config_manager
from app.notifier.payloads import EmailPayload
from app.services.logger import LoggingService

logger = LoggingService.get_logger(__name__)


def _parse_bool(value: object | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_smtp_config() -> dict | None:
    smtp_host = env_config_manager.get_dynamic_setting("MAIL_SERVER")
    smtp_port = env_config_manager.get_dynamic_setting("MAIL_PORT")
    smtp_username = env_config_manager.get_dynamic_setting("MAIL_USERNAME")
    smtp_password = env_config_manager.get_dynamic_setting("MAIL_PASSWORD")
    mail_from = env_config_manager.get_dynamic_setting("MAIL_FROM")
    mail_tls = _parse_bool(env_config_manager.get_dynamic_setting("MAIL_TLS"))
    mail_ssl = _parse_bool(env_config_manager.get_dynamic_setting("MAIL_SSL"))

    if not smtp_host or not smtp_port or not smtp_username or not smtp_password:
        logger.warning("Email SMTP config incomplete; skipping email send.")
        return None

    try:
        smtp_port = int(smtp_port)
    except (TypeError, ValueError):
        smtp_port = 587

    return {
        "host": smtp_host,
        "port": smtp_port,
        "username": smtp_username,
        "password": smtp_password,
        "from_address": mail_from or smtp_username,
        "use_tls": mail_tls,
        "use_ssl": mail_ssl,
    }


def _build_email_message(payload: EmailPayload, from_address: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = payload.subject
    message["From"] = from_address
    message["To"] = ", ".join(payload.recipients)
    message.set_content(payload.body, subtype=payload.subtype)

    for attachment in payload.attachments:
        message.add_attachment(
            attachment.content,
            maintype=attachment.mime_type.split("/")[0],
            subtype=attachment.mime_type.split("/")[-1],
            filename=attachment.filename,
        )

    return message


def send_email(payload: EmailPayload, dry_run: bool = False) -> bool:
    if not payload.recipients:
        logger.warning("Email recipients missing; skipping email send.")
        return False

    smtp_config = _get_smtp_config()
    if not smtp_config:
        return False

    if dry_run:
        logger.info("Dry-run enabled for email send.")
        return True

    message = _build_email_message(payload, smtp_config["from_address"])

    try:
        if smtp_config["use_ssl"]:
            server = smtplib.SMTP_SSL(
                smtp_config["host"],
                smtp_config["port"],
            )
        else:
            server = smtplib.SMTP(
                smtp_config["host"],
                smtp_config["port"],
            )

        with server:
            server.ehlo()
            if smtp_config["use_tls"]:
                server.starttls()
                server.ehlo()
            server.login(smtp_config["username"], smtp_config["password"])
            server.send_message(message)
        return True
    except Exception as exc:
        logger.error(f"Failed to send email: {exc}")
        return False
