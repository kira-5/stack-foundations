from src.shared.notifier.payloads import AlertChannel, AlertPayload, EmailPayload, SlackPayload
from src.shared.notifier.providers.email_provider import send_email
from src.shared.notifier.providers.slack_provider import send_slack
from src.shared.services.logging_service import LoggingService

logger = LoggingService.get_logger(__name__)


class NotifierService:
    @staticmethod
    async def send(payload: AlertPayload, dry_run: bool = False) -> bool:
        results: list[bool] = []
        channels = list(payload.channels)

        if AlertChannel.EMAIL in channels:
            if payload.email is None:
                logger.warning("Email channel requested without email payload.")
                results.append(False)
            else:
                results.append(send_email(payload.email, dry_run=dry_run))

        if AlertChannel.SLACK in channels:
            if payload.slack is None:
                logger.warning("Slack channel requested without slack payload.")
                results.append(False)
            else:
                results.append(
                    await send_slack(
                        payload.slack,
                        dry_run=dry_run,
                        use_attachments=payload.slack.use_attachments,
                        process_key=payload.process_key,
                    ),
                )

        if not results:
            logger.warning("No alert channels requested; nothing sent.")
            return False

        return all(results)


notifier_service = NotifierService()


def smoke_test_notifier() -> AlertPayload:
    email_payload = EmailPayload(
        subject="Smoke Test Alert",
        body="This is a smoke test payload.",
        recipients=["example@company.com"],
    )
    slack_payload = SlackPayload(text="Smoke test payload for Slack.")
    return AlertPayload(
        channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
        email=email_payload,
        slack=slack_payload,
    )
