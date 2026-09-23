class TokenExpiredError(Exception):
    """Is being raised when OAuth token is expired"""

class AuthConfigError(Exception):
    """Is being raised when the authorization configuration is incorrect or incomplete."""

class AuthRequiredError(Exception):
    """Is being raised when a request needs a valid access token that hasn't been obtained yet (e.g. OAuth authorize() wasn't called)"""

class ApiError(Exception):
    """Is being raised when API threw an error"""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

class NotFoundError(ApiError):
    """Is being raised when a resource looked up by id doesn't exist, was deleted, or doesn't belong to the token owner"""

class InvalidScopeError(Exception):
    """Is being raised when the specified scopes are invalid"""

class TransportNotReadyError(Exception):
    """Is being raised when transport was not properly started"""

class FloodWaitError(Exception):
    """Is being raised when api returned 429 Too many requests"""

class ArgumentsConflictError(Exception):
    """Is being raised when incompatible arguments are entered"""
