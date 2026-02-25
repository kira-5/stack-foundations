from enum import Enum

# Define a fallback user ID for local environments
FALLBACK_USER_ID = 251

LOCAL = "local"
BASE_PRICING_LOCAL = "base-pricing-local"
LOCAL_ENVIRONMENTS = [LOCAL, BASE_PRICING_LOCAL]

# Environment names
DEVELOPMENT = "development"
STAGING = "staging"
PRODUCTION = "production"

# Default values
DEFAULT_REQUEST_ID = "no_request_id"
DEFAULT_ENV = ""


class Environment(Enum):
    """Enum for environment types."""

    LOCAL = LOCAL
    DEVELOPMENT = DEVELOPMENT
    STAGING = STAGING
    PRODUCTION = PRODUCTION


class UserIDSource(Enum):
    """Enum for user ID sources."""

    ENVIRONMENT = "environment"
    REQUEST = "request"
    FALLBACK = "fallback"
