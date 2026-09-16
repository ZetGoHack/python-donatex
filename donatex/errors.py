class TokenExpiredError(Exception):
    """Is being raised when OAuth token is expired"""

class AuthConfigError(Exception):
    """Is being raised when the authorization configuration is incorrect or incomplete."""

class ApiError(Exception):
    """Is being raised when API threw an error"""

class InvalidScopeError(Exception):
    """Is being raised when the specified scopes are invalid"""

class TransportNotReadyError(Exception):
    """Is being raised when transport was not properly started"""

class FloodWaitError(Exception):
    """Is being raised when api returned 429 Too many requests"""

class ArgumentsConflictError(Exception):
    """Is being raised when incompatible arguments are entered"""
