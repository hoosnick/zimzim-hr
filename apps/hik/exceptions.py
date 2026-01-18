class HikClientError(Exception):
    """Base exception for all HikClient errors"""

    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AuthenticationError(HikClientError):
    """Raised when authentication fails"""

    pass


class TokenExpiredError(AuthenticationError):
    """Raised when the access token has expired"""

    pass


class APIError(HikClientError):
    """Raised when the API returns an error response"""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        status_code: int | None = None,
    ):
        super().__init__(message, error_code)
        self.status_code = status_code


class NetworkError(HikClientError):
    """Raised when network-related errors occur"""

    pass


class ValidationError(HikClientError):
    """Raised when data validation fails"""

    pass
