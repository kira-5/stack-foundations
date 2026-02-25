from src.shared.configuration import constants as core_constants
from src.shared.exceptions import base_exception as core_base_exception


from typing import Optional

class BusinessCaseException(core_base_exception.CoreBaseException):
    """Exception for business logic errors with custom message and status code."""

    def __init__(
        self,
        message: str,
        status_code: int,
        user_id: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        self.user_id = user_id
        super().__init__(message, status_code, data=data)


class TechnicalException(core_base_exception.CoreBaseException):
    """Exception for technical issues like Python, SQL, or API failures.

    Uses a fixed error message and status code.
    """

    def __init__(self) -> None:
        message = core_constants.ERROR_MESSAGE
        status_code = core_constants.STATUS_ERROR
        super().__init__(message, status_code)
