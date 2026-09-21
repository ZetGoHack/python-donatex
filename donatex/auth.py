import base64
import hashlib
import secrets
import time
import urllib.parse

from abc import ABC, abstractmethod

from . import errors
from .utils import validate_scopes

_AUTHORIZE_URL = "https://donatex.gg/api/connect/authorize"
_TOKEN_URL = "https://donatex.gg/api/connect/token"


class AuthStrategy(ABC):
    _TYPE = "BASE"

    def __init__(self):
        super().__init__()
        self._access_token = None

    @abstractmethod
    async def get_access_token(self) -> str: ...

    def is_authorized(self) -> bool:
        return bool(self._access_token)

    def _bind_transport(self, token_request) -> None: ...


class ExternalTokenAuth(AuthStrategy):
    """Авторизация с бессрочным токеном только под личный аккаунт"""
    _TYPE = "EXTERNAL"

    def __init__(self, token: str):
        self._access_token = token

    async def get_access_token(self) -> str:
        return self._access_token


class OAuthStrategy(AuthStrategy):

    def __init__(self, client_id, scopes=None):
        super().__init__()
        scopes = scopes or frozenset()
        validate_scopes(scopes)
        if not scopes:
            raise errors.AuthConfigError(
                "Не указано ни одного scope. Токен без scopes не имеет смысла"
            )
        self._client_id = client_id
        self._scopes = scopes
        self._refresh_token = None
        self._expires_at = None
        self._redirect_uri = None
        self._code_verifier = None
        self._token_request = None

    def _bind_transport(self, token_request) -> None:
        self._token_request = token_request

    def get_authorize_url(self, redirect_uri: str, state: str | None = None) -> str:
        """Ссылка для получения согласия пользователя при OAuth-авторизации"""
        self._redirect_uri = redirect_uri
        self._code_verifier = secrets.token_urlsafe(64)
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(self._code_verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )

        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(sorted(self._scopes)),
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        if state is not None:
            params["state"] = state
        return f"{_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    @abstractmethod
    def _build_token_payload(self, code: str) -> dict: ...

    @abstractmethod
    def _build_refresh_payload(self) -> dict: ...

    def _store_tokens(
        self,
        access_token: str,
        refresh_token: str | None = None,
        expires_in: float | None = None,
        **_,
    ) -> None:
        self._access_token = access_token
        if refresh_token is not None:
            self._refresh_token = refresh_token
        self._expires_at = time.time() + expires_in if expires_in is not None else None

    def _expired(self) -> bool:
        if self._expires_at is None:
            return False
        return time.time() >= self._expires_at

    async def authorize(self, code: str) -> None:
        if self._token_request is None:
            raise errors.AuthRequiredError(
                "Auth не привязан к транспорту — authorize() нельзя вызвать напрямую, только через Client"
            )
        data = await self._token_request(_TOKEN_URL, self._build_token_payload(code))
        self._store_tokens(**data)

    async def refresh(self) -> None:
        if not self._refresh_token:
            raise errors.AuthRequiredError(
                "Нет refresh_token — нужно заново пройти authorize()"
            )
        data = await self._token_request(_TOKEN_URL, self._build_refresh_payload())
        self._store_tokens(**data)

    async def get_access_token(self) -> str:
        if self._expired():
            await self.refresh()
        return self._access_token


class OAuthConfidentialAuth(OAuthStrategy):
    """Для серверных приложений с несколькими пользователями"""
    _TYPE = "OAUTH_CONF"

    def __init__(self, client_id, client_secret, scopes=None):
        super().__init__(client_id, scopes=scopes)
        self._client_secret = client_secret

    def _build_token_payload(self, code: str) -> dict:
        return {
            "grant_type": "authorization_code",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "code": code,
            "redirect_uri": self._redirect_uri,
            "code_verifier": self._code_verifier,
        }

    def _build_refresh_payload(self) -> dict:
        return {
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": self._refresh_token,
        }


class OAuthPublicAuth(OAuthStrategy):
    """Для SPA и мобильных клиентов"""
    _TYPE = "OAUTH_PUB"

    def _build_token_payload(self, code: str) -> dict:
        return {
            "grant_type": "authorization_code",
            "client_id": self._client_id,
            "code": code,
            "redirect_uri": self._redirect_uri,
            "code_verifier": self._code_verifier,
        }

    def _build_refresh_payload(self) -> dict:
        return {
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "refresh_token": self._refresh_token,
        }


AuthType = ExternalTokenAuth | OAuthConfidentialAuth | OAuthPublicAuth
