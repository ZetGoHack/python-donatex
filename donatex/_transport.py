import httpx

from .auth import AuthType
from . import errors


class Transport:
    def __init__(self, auth: AuthType, proxy: str | None = None):
        self._auth = auth
        self._proxy = proxy
        self.is_ready = False
        self._client = None

    async def start(self):
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
        if not self._auth.is_authorized():
            raise errors.AuthRequiredError(
                "Клиент не авторизован. Для OAuth сначала вызовите client.authorize(code)"
            )
        token = await self._auth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
        }

    async def _token_request(self, url: str, data: dict) -> dict:
        if not self.is_ready:
            raise errors.TransportNotReadyError(
                "Транспорт не готов вызывать запросы к API"
            )
        resp = await self._client.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200:
            raise errors.ApiError(resp.text)

        return resp.json()

    async def _request(self, method: str, url: str, **kwargs) -> "httpx.Response":
        if not self.is_ready:
            raise errors.TransportNotReadyError(
                "Транспорт не готов вызывать запросы к API"
            )
        headers = await self._get_headers()

        return await getattr(self._client, method)(url, headers=headers, **kwargs)

    async def _get(self, url: str, **kwargs):
        resp = await self._request("get", url, **kwargs)
        if resp.status_code != 200:
            raise errors.ApiError(resp.text)

        return resp.json()

    async def _post(self, url: str, **kwargs):
        resp = await self._request("post", url, **kwargs)
        if resp.status_code not in (200, 204):
            raise errors.ApiError(resp.text)
        if resp.status_code == 204:
            return None

        return resp.json()

    async def _delete(self, url: str, **kwargs):
        resp = await self._request("delete", url, **kwargs)
        if resp.status_code != 204:
            raise errors.ApiError(resp.text)

        return None
