class TokenExpired(Exception):
    """Is being raised when OAuth token is expired"""

class AuthConfigError(Exception):
    """Is being raised when the authorization configuration is incorrect or incomplete."""
