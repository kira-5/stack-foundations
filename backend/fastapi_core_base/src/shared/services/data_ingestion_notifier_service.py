import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

from src.shared.configuration.config import env_config_manager
from src.shared.email_templates.templates.data_ingestion.schema import (
    DataIngestionEmailContext,
)
from src.shared.notifier.payloads import AlertChannel, AlertPayload, EmailPayload, SlackPayload
from src.shared.notifier.settings import (
    get_notifier_bool_setting,
    get_notifier_category,
    get_notifier_recipients_setting,
)
from src.shared.services.email_template_service import email_template_service
from src.shared.services.logging_service import LoggingService
from src.shared.services.notifier_service import notifier_service
from src.shared.services.slack_template_service import slack_template_service
from src.shared.services.user_service import user_service

logger = LoggingService.get_logger(__name__)


class DataIngestionNotifierService:
    """Service to handle data ingestion notifications via Email and Slack."""

    async def notify(
        self,
        process_key: str,
        status: str,
        user_id: int | None,
        process_id: str,
        start_time: datetime,
        process_results: list[dict] | None = None,
        error_message: str | None = None,
        exception: Exception | None = None,
    ) -> bool:
        """Send data ingestion notifications using NotifierService."""
        try:
            # 1. Prepare context for template rendering
            # Standardize everything to IST
            now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))

            # Ensure start_time is IST-aware for accurate duration
            if start_time.tzinfo is None:
                start_time_ist = start_time.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            else:
                start_time_ist = start_time.astimezone(ZoneInfo("Asia/Kolkata"))

            duration = now_ist - start_time_ist
            total_seconds = int(duration.total_seconds())

            if total_seconds < 0:
                duration_str = "0h 0m 0s"
            else:
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{hours}h {minutes}m {seconds}s"

            # Get initiator info
            initiated_by_email = None
            initiated_by_name = f"User ID: {user_id}" if user_id else "System"

            if user_id:
                try:
                    user_info = await user_service.get_email_by_user_id(user_id)
                    if user_info:
                        initiated_by_email = user_info.get("user_email")
                        if user_info.get("user_name"):
                            initiated_by_name = user_info.get("user_name")
                except Exception as e:
                    logger.warning(f"Failed to fetch user info for {user_id}: {e}")

            # Environment & Client Details
            environment = env_config_manager.get_dynamic_setting(
                "DEPLOYMENT_ENV",
                "Production",
            )
            client_name = env_config_manager.get_dynamic_setting(
                "CLIENT_NAME",
                "Impact Analytics",
            )

            traceback_str = None
            if exception:
                traceback_str = "".join(
                    traceback.format_exception(
                        type(exception),
                        exception,
                        exception.__traceback__,
                    ),
                )

            # Get category from DB
            category = await get_notifier_category(process_key)

            context = DataIngestionEmailContext(
                process_name=process_key.replace("_", " ").title(),
                status=status,
                reference_id=process_id,
                timestamp=now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                start_time=start_time_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                process_id=process_id,
                client_name=client_name,
                execution_duration=duration_str,
                initiated_by_name=initiated_by_name,
                initiated_by_email=initiated_by_email,
                environment=environment,
                category=category,
                process_results=[{k: str(v) for k, v in res.items()} for res in (process_results or [])],
                error_message=error_message,
                traceback=traceback_str,
            )

            # 2. Render and Prepare Payloads
            channels = []
            email_payload = None
            slack_payload = None

            # --- Email Configuration ---
            email_enabled = await get_notifier_bool_setting(
                process_key,
                "EMAIL",
                "ENABLED",
            )
            if email_enabled:
                recipients = await get_notifier_recipients_setting(
                    process_key,
                    "EMAIL",
                    "RECIPIENTS",
                )
                if recipients:
                    email_render_result = email_template_service.render(
                        "data_ingestion",
                        context,
                    )
                    channels.append(AlertChannel.EMAIL)
                    email_payload = EmailPayload(
                        subject=email_render_result.subject,
                        body=email_render_result.html,
                        recipients=recipients,
                        subtype="html",
                    )
                    logger.info(
                        f"Email enabled for {process_key} with recipients: {recipients}",
                    )
                else:
                    logger.warning(
                        f"Email enabled for {process_key} but no recipients found.",
                    )

            # --- Slack Configuration ---
            slack_enabled = await get_notifier_bool_setting(
                process_key,
                "SLACK",
                "ENABLED",
            )
            if slack_enabled:
                slack_render_result = slack_template_service.render(
                    "data_ingestion",
                    context,
                )
                channels.append(AlertChannel.SLACK)
                slack_payload = SlackPayload(
                    text=slack_render_result.text,
                    blocks=slack_render_result.blocks,
                    attachments=slack_render_result.attachments,
                    use_attachments=slack_render_result.use_attachments,
                    channel=slack_render_result.channel,
                )
                logger.info(f"Slack enabled for {process_key}.")

            if not channels:
                logger.warning(f"No notification channels enabled for {process_key}.")
                return False

            # 3. Dispatch Alert
            alert_payload = AlertPayload(
                channels=channels,
                process_key=process_key,
                email=email_payload,
                slack=slack_payload,
            )

            return await notifier_service.send(alert_payload)

        except Exception as e:
            logger.error(
                f"DataIngestionNotifierService.notify failed: {e}",
                exc_info=True,
            )
            return False


data_ingestion_notifier_service = DataIngestionNotifierService()
