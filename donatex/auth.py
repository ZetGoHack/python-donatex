import time

from abc import ABC, abstractmethod

from .errors import AuthConfigError
from .utils import validate_scopes


class AuthState:
    """TODO"""


class AuthStrategy(ABC):
    _TYPE = "BASE"

    def __init__(self):
        super().__init__()
        self._access_token = None

    @abstractmethod
    async def get_access_token(self) -> str: ...

    def is_authorized(self) -> bool:
        return bool(self._access_token)


class ExternalTokenAuth(AuthStrategy):
    _TYPE = "EXTERNAL"

    def __init__(self, token: str):
        self._access_token = token

    async def get_access_token(self) -> str:
        return self._access_token


class OAuthConfidentialAuth(AuthStrategy):  # TODO
    _TYPE = "OAUTH_CONF"

    def __init__(self, client_id, client_secret, scopes=None):
        super().__init__()
        scopes = scopes or frozenset()
        validate_scopes(scopes)
        if not scopes:
            raise AuthConfigError(
                "Не указано ни одного scope. Токен без scopes не имеет смысла"
            )
        self._client_id = client_id
        self._client_secret = client_secret
        self._scopes = scopes

    async def authorize(self): ...
    async def refresh(self): ...
    async def get_access_token(self) -> str:
        if await self._expired():
            await self.refresh()
        return self._access_token

    async def _expired(self): ...


class OAuthPublicAuth(AuthStrategy):  # TODO
    _TYPE = "OAUTH_PUB"

    def __init__(self, client_id, scopes=None):
        super().__init__()
        scopes = scopes or frozenset()
        validate_scopes(scopes)
        if not scopes:
            raise AuthConfigError(
                "Не указано ни одного scope. Токен без scopes не имеет смысла"
            )
        self._client_id = client_id
        self._scopes = scopes

    async def authorize(self): ...
    async def refresh(self): ...
    async def get_access_token(self) -> str:
        if await self._expired():
            await self.refresh()
        return self._access_token

    async def _expired(self): ...


AuthType = ExternalTokenAuth | OAuthConfidentialAuth | OAuthPublicAuth
