from abc import ABC, abstractmethod


class AuthStrategy(ABC):
    _TYPE = "BASE"
    @abstractmethod
    async def get_access_token(self) -> str: ...

    @abstractmethod
    async def refresh(self): ...


class ExternalTokenAuth(AuthStrategy):
    _TYPE = "EXTERNAL"
    def __init__(self, token: str):
        self.token = token

    async def get_access_token(self) -> str:
        return self.token


class OAuthConfidentialAuth(AuthStrategy):
    _TYPE = "OAUTH_CONF"
    def __init__(self, client_id, client_secret): ...
    async def authorize(self): ...
    async def get_access_token(self) -> str:
        if self._expired():
            await self.refresh()
        return self._access_token


class OAuthPublicAuth(AuthStrategy):
    _TYPE = "OAUTH_PUB"
    def __init__(self, client_id): ...
    async def get_access_token(self) -> str:
        if self._expired():
            self.refresh()
        return self._access_token

AuthType = (
    ExternalTokenAuth |
    OAuthConfidentialAuth |
    OAuthPublicAuth
)
