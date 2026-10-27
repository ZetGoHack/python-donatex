class TokenExpiredError(Exception):
    """Is being raised when OAuth token is expired"""

class AuthConfigError(Exception):
    """Is being raised when the authorization configuration is incorrect or incomplete."""

class AuthRequiredError(Exception):
    """Is being raised when a request needs a valid access token that hasn't been obtained yet (e.g. OAuth authorize() wasn't called)"""

class ApiError(Exception):
    """Is being raised when API threw an error"""
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        errors: dict[str, list[str]] | None = None,
        trace_id: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or {}
        self.trace_id = trace_id

class BadRequestError(ApiError):
    """Is being raised on 400: invalid parameters or a request that can't be processed"""

class UnauthorizedError(ApiError):
    """Is being raised on 401: token is missing, expired, revoked or reissued"""

class ForbiddenError(ApiError):
    """Is being raised on 403: the token lacks the scope required by the method"""

class NotFoundError(ApiError):
    """Is being raised on 404: when a resource looked up by id doesn't exist, was deleted, or doesn't belong to the token owner"""

class MethodNotAllowedError(ApiError):
    """Is being raised on 405: the path exists but not with this HTTP method"""

class ConflictError(ApiError):
    """Is being raised on 409: the action can't be done in the current state"""

class UnsupportedMediaTypeError(ApiError):
    """Is being raised on 415: the request body isn't JSON"""

class FloodWaitError(ApiError):
    """Is being raised when api returned 429 Too many requests (``retry_after`` is taken from ``Retry-After``)"""
    def __init__(self, message: str, retry_after: float = 1.0, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after

class ServerError(ApiError):
    """Is being raised on 5xx: unexpected error on DonateX's side, retry later"""

class InvalidScopeError(Exception):
    """Is being raised when the specified scopes are invalid"""

class TransportNotReadyError(Exception):
    """Is being raised when transport was not properly started"""

class ArgumentsConflictError(Exception):
    """Is being raised when incompatible arguments are entered"""
