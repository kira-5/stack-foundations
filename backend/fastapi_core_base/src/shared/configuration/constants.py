# List of keys for database configuration secrets to be fetched from Google Secret Manager
GCP_SECRET_KEYS = sorted(
    [
        "db_host",
        "db_port",
        "db_name",
        "db_user",
        "db_password",
        "connection_string",
    ],
)

MTP_SECRET_KEYS = sorted(
    [
        "AUTH_TOKEN_ISS",
        "CLIENT_NAME",
        "CLOUD_RUN",
        "DEPLOY_ENV",
        "GCP_DATA_PROJECT_ID",
        "GCP_PROJECT_ID",
        "PGBOUNCER_HOST",
        "PGBOUNCER_PASSWORD",
        "PGBOUNCER_PORT",
        "PGBOUNCER_USER",
        "REDIS_HOST",
        "REDIS_PASSWORD",
        "REDIS_PORT",
        "SERVICE_ACCOUNT_ID",
        "UNIVERSAL_USE_REDIS",
    ],
)

EMAIL_NOTIFICATION_SECRET_KEYS = sorted(
    [
        "EMAIL_NOTIFICATION_SMTP_HOST",
        "EMAIL_NOTIFICATION_SMTP_PORT",
        "EMAIL_NOTIFICATION_SMTP_USERNAME",
        "EMAIL_NOTIFICATION_SMTP_PASSWORD",
        "mail_username",
        "mail_password",
        "mail_from",
        "mail_port",
        "mail_server",
        "mail_tls",
        "mail_ssl",
        "use_credentials",
        "validate_certs",
    ],
)
# =============================================================================
# 4. Global API Status Constants
# =============================================================================
API_TITLE = "Base Pricing Platform API"
API_PREFIX = "/api/v1"
FAILURE_FLAG = "failure"
SUCCESS_FLAG = "success"
STATUS_ERROR = 500
STATUS_SUCCESS = 200
ERROR_MESSAGE = "An unexpected technical error occurred. Please contact support."


class LogEmoji:
    """Emoji constants for logging status indication."""
    ENVIRONMENT = "🌐"
    ENVIRONMENT_SWITCH = "🔄"
    START_STATUS = "🚀"
    SERVER_SHUTDOWN = "🛑"
    SERVER_STARTUP = "⚡"
    CONFIGURATION = "⚙️"
    ERROR_STATUS = "❌"
    WARNING_STATUS = "⚠️"
    SUCCESS_STATUS = "✅"
    CLEANUP_STATUS = "🧹"
    DB_STATUS = "💾"
    REDIS_STATUS = "🧠"
    EXTERNAL_API = "📡"
    USER_STATUS = "👤"
