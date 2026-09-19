import httpx

from .auth import AuthType
from .errors import ApiError, TransportNotReadyError


class Transport:
    def __init__(self, auth: AuthType, proxy: str | None = None):
        self._auth = auth
        self._proxy = proxy
        self.is_ready = False
        self._client = None

    async def start(self):
        # TODO: логика авторизации и подстановки токена для начальной настройки
        if not self._auth.is_authorized():
            raise NotImplementedError()
        headers = {
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(
            headers=headers, trust_env=False, proxy=self._proxy
        )
        self.is_ready = True
        return self.is_ready

    async def stop(self):
        if self._client:
            await self._client.aclose()

        self._client = None
        self.is_ready = False

    async def _get_headers(self) -> dict:
        token = await self._auth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
        }

    # TODO: мб гейтинг для is_ready

    async def _get(self, url: str, **kwargs):
        if not self.is_ready:
            raise TransportNotReadyError("Транспорт не готов вызывать запросы к API")
        headers = await self._get_headers()

        resp = await self._client.get(url, headers=headers, **kwargs)
        if resp.status_code != 200:
            raise ApiError(resp.text)
        raw = resp.json()

        return raw

    async def _post(self, url: str, **kwargs):
        if not self.is_ready:
            raise TransportNotReadyError("Транспорт не готов вызывать запросы к API")
        headers = await self._get_headers()

        resp = await self._client.post(url, headers=headers, **kwargs)
        if resp.status_code not in (200, 204):
            raise ApiError(resp.text)
        if resp.status_code == 204:
            return None

        raw = resp.json()

        return raw

    async def _delete(self, url: str, **kwargs):
        if not self.is_ready:
            raise TransportNotReadyError("Транспорт не готов вызывать запросы к API")
        headers = await self._get_headers()

        resp = await self._client.delete(url, headers=headers, **kwargs)
        if resp.status_code != 204:
            raise ApiError(resp.text)

        return None
