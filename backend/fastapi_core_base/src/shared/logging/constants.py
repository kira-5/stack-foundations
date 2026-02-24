# Date format constants
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Logger names constants
LOGGER_APPLICATION = "application"
LOGGER_FASTAPI = "fastapi"
LOGGER_UVICORN = "uvicorn"
LOGGER_UVICORN_ACCESS = "uvicorn.access"
LOGGER_UVICORN_ERROR = "uvicorn.error"

# Log level constants
LOG_LEVEL_DEBUG_LOWERCASE = "debug"
LOG_LEVEL_INFO_LOWERCASE = "info"
LOG_LEVEL_WARNING_LOWERCASE = "warning"
LOG_LEVEL_ERROR_LOWERCASE = "error"
LOG_LEVEL_CRITICAL_LOWERCASE = "critical"
LOG_LEVEL_RESET_LOWERCASE = "reset"

# Log level constants (for display and standard logging)
LOG_LEVEL_DEBUG_UPPERCASE = "DEBUG"
LOG_LEVEL_INFO_UPPERCASE = "INFO"
LOG_LEVEL_WARNING_UPPERCASE = "WARNING"
LOG_LEVEL_ERROR_UPPERCASE = "ERROR"
LOG_LEVEL_CRITICAL_UPPERCASE = "CRITICAL"
LOG_LEVEL_RESET_UPPERCASE = "RESET"

# ANSI color codes constants
LOG_COLORS = {
    LOG_LEVEL_DEBUG_UPPERCASE: "\033[36m",  # Cyan
    LOG_LEVEL_INFO_UPPERCASE: "\033[32m",  # Green
    LOG_LEVEL_WARNING_UPPERCASE: "\033[33m",  # Yellow
    LOG_LEVEL_ERROR_UPPERCASE: "\033[31m",  # Red
    LOG_LEVEL_CRITICAL_UPPERCASE: "\033[35m",  # Magenta
    LOG_LEVEL_RESET_UPPERCASE: "\033[0m",  # Reset
}

# Log format types
LOG_FORMAT_MTP_TYPE = "mtp"
LOG_FORMAT_SIMPLE_TYPE = "simple"
LOG_FORMAT_STRUCTURED_TYPE = "structured"
LOG_FORMAT_DETAILED_TYPE = "detailed"

# Message separator constants
DASH_SEPARATOR = " - "
PIPE_SEPARATOR = " | "
EQUALS_SEPARATOR = " = "

# Message format templates constants
LOG_FORMAT_MTP_TEMPLATE = "%(message)s"  # MTP format is handled in the service layer
LOG_FORMAT_SIMPLE_TEMPLATE = "%(levelname)s: %(message)s"
LOG_FORMAT_STRUCTURED_TEMPLATE = (
    f"%(asctime)s{PIPE_SEPARATOR}%(levelname)s{PIPE_SEPARATOR}%(message)s{PIPE_SEPARATOR}%(extra)s"
)
LOG_FORMAT_DETAILED_TEMPLATE = (
    f"%(asctime)s{PIPE_SEPARATOR}"
    f"%(name)s{PIPE_SEPARATOR}"
    f"%(levelname)s{PIPE_SEPARATOR}"
    f"[%(filename)s:%(lineno)d]{PIPE_SEPARATOR}"
    f"%(message)s{PIPE_SEPARATOR}"
    f"%(extra)s"
)

# Default log level constants
DEFAULT_LOG_LEVEL = LOG_LEVEL_INFO_UPPERCASE

# Logger names constants
LOGGER_NAMES = [
    LOGGER_FASTAPI,
    LOGGER_UVICORN,
    LOGGER_UVICORN_ACCESS,
    LOGGER_UVICORN_ERROR,
]

# Service enable/disable configuration keys (for settings.toml)
LOG_SERVICE_REDIS_ENABLED = "LOG_SERVICE_REDIS_ENABLED"
LOG_SERVICE_POSTGRES_ENABLED = "LOG_SERVICE_POSTGRES_ENABLED"
LOG_SERVICE_REQUESTS_ENABLED = "LOG_SERVICE_REQUESTS_ENABLED"
LOG_SERVICE_AIOHTTP_ENABLED = "LOG_SERVICE_AIOHTTP_ENABLED"
LOG_SERVICE_GRPC_ENABLED = "LOG_SERVICE_GRPC_ENABLED"
LOG_SERVICE_MISC_ENABLED = "LOG_SERVICE_MISC_ENABLED"
LOG_SERVICE_APPLICATION_ENABLED = "LOG_SERVICE_APPLICATION_ENABLED"
LOG_SERVICE_UVICORN_ENABLED = "LOG_SERVICE_UVICORN_ENABLED"

# Default: all services enabled
DEFAULT_SERVICE_ENABLED = True

LOG_LEVEL_LOWERCASE = [
    LOG_LEVEL_DEBUG_LOWERCASE,
    LOG_LEVEL_INFO_LOWERCASE,
    LOG_LEVEL_WARNING_LOWERCASE,
    LOG_LEVEL_ERROR_LOWERCASE,
    LOG_LEVEL_CRITICAL_LOWERCASE,
    LOG_LEVEL_RESET_LOWERCASE,
]

LOG_LEVEL_UPPERCASE = [
    LOG_LEVEL_DEBUG_UPPERCASE,
    LOG_LEVEL_INFO_UPPERCASE,
    LOG_LEVEL_WARNING_UPPERCASE,
    LOG_LEVEL_ERROR_UPPERCASE,
    LOG_LEVEL_CRITICAL_UPPERCASE,
    LOG_LEVEL_RESET_UPPERCASE,
]

LOG_FORMAT_TYPES = [
    LOG_FORMAT_MTP_TYPE,
    LOG_FORMAT_SIMPLE_TYPE,
    LOG_FORMAT_STRUCTURED_TYPE,
    LOG_FORMAT_DETAILED_TYPE,
]

# Log format mapping constants
LOG_FORMATS = {
    LOG_FORMAT_MTP_TYPE: LOG_FORMAT_MTP_TEMPLATE,
    LOG_FORMAT_SIMPLE_TYPE: LOG_FORMAT_SIMPLE_TEMPLATE,
    LOG_FORMAT_STRUCTURED_TYPE: LOG_FORMAT_STRUCTURED_TEMPLATE,
    LOG_FORMAT_DETAILED_TYPE: LOG_FORMAT_DETAILED_TEMPLATE,
}

# Log level mapping constants
LOG_LEVELS = {
    LOG_LEVEL_DEBUG_LOWERCASE: LOG_LEVEL_DEBUG_UPPERCASE,
    LOG_LEVEL_INFO_LOWERCASE: LOG_LEVEL_INFO_UPPERCASE,
    LOG_LEVEL_WARNING_LOWERCASE: LOG_LEVEL_WARNING_UPPERCASE,
    LOG_LEVEL_ERROR_LOWERCASE: LOG_LEVEL_ERROR_UPPERCASE,
    LOG_LEVEL_CRITICAL_LOWERCASE: LOG_LEVEL_CRITICAL_UPPERCASE,
}

# Handler types
HANDLER_FILE = "file"
HANDLER_TERMINAL = "terminal"
HANDLER_DATADOG = "datadog"

# Service logger constants
LOGGER_SERVICE_SEPARATED = "service_separated"

# Service component names
SERVICE_REDIS = "redis"
SERVICE_POSTGRES = "postgres"
SERVICE_REQUESTS = "requests"
SERVICE_AIOHTTP = "aiohttp"
SERVICE_GRPC = "grpc"
SERVICE_MISC = "misc"
SERVICE_APPLICATION = "application"
SERVICE_UVICORN = "uvicorn"

# Service colors (ANSI color codes)
# Dark-to-light gradient: UVICORN (darkest) -> APPLICATION -> POSTGRES -> REDIS -> REQUESTS -> AIOHTTP -> GRPC -> MISC (lightest)
# Optimized for both dark and white terminal backgrounds
# Each service uses progressively lighter shades of their color family
SERVICE_COLORS = {
    SERVICE_UVICORN: "\033[32m",  # Dark Green (darkest) - Uvicorn (server/FastAPI)
    SERVICE_APPLICATION: "\033[38;5;28m",  # Medium-Dark Green - Application (main app code)
    SERVICE_POSTGRES: "\033[38;5;18m",  # Dark Blue - PostgreSQL (database)
    SERVICE_REDIS: "\033[38;5;88m",  # Dark Red - Redis (cache/memory)
    SERVICE_REQUESTS: "\033[38;5;130m",  # Medium Brown/Orange - Requests (sync HTTP)
    SERVICE_AIOHTTP: "\033[38;5;30m",  # Medium-Dark Cyan - aiohttp (async HTTP)
    SERVICE_GRPC: "\033[38;5;90m",  # Medium-Dark Magenta - gRPC (RPC calls)
    SERVICE_MISC: "\033[38;5;240m",  # Medium Gray (lightest) - Misc (templates, etc.)
}

# Logger name patterns mapped to services
# Format: {logger_pattern: service_name}
SERVICE_LOGGER_PATTERNS = {
    # Redis
    "redis": SERVICE_REDIS,
    "redis.client": SERVICE_REDIS,
    "redis.connection": SERVICE_REDIS,
    "redis.pool": SERVICE_REDIS,
    # PostgreSQL
    "psycopg": SERVICE_POSTGRES,
    "psycopg.pool": SERVICE_POSTGRES,
    "sqlalchemy": SERVICE_POSTGRES,
    "sqlalchemy.engine": SERVICE_POSTGRES,
    "sqlalchemy.pool": SERVICE_POSTGRES,
    "database_service": SERVICE_POSTGRES,  # Database service queries
    "app.services.database_service": SERVICE_POSTGRES,  # Full module path
    # Requests (synchronous HTTP)
    "urllib3": SERVICE_REQUESTS,
    "urllib3.connectionpool": SERVICE_REQUESTS,
    "requests": SERVICE_REQUESTS,
    "requests.packages": SERVICE_REQUESTS,
    # aiohttp (async HTTP)
    "aiohttp": SERVICE_AIOHTTP,
    "aiohttp.client": SERVICE_AIOHTTP,
    "aiohttp.server": SERVICE_AIOHTTP,
    "aiohttp.connector": SERVICE_AIOHTTP,
    # gRPC
    "grpc": SERVICE_GRPC,
    "_cygrpc": SERVICE_GRPC,
    "google.cloud": SERVICE_GRPC,
    # Misc
    "jinja2": SERVICE_MISC,
    "jinja2.loaders": SERVICE_MISC,
    # Uvicorn/FastAPI
    "uvicorn": SERVICE_UVICORN,
    "uvicorn.access": SERVICE_UVICORN,
    "uvicorn.error": SERVICE_UVICORN,
    "fastapi": SERVICE_UVICORN,
}
