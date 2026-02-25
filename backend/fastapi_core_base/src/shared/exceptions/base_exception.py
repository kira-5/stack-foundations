# base_exception.py
class CoreBaseException(Exception):
    """Base class for global exceptions.

    Can be extended for exceptions in any context (not limited to HTTP).
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        user_id: str = None,
        data: dict = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = (
            status_code  # Optional, you can use this for HTTP-related contexts
        )
        self.user_id = user_id
        self.data = data

    def __str__(self) -> str:
        return self.message
