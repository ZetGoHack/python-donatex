import httpx

from .auth import AuthType


class Transport:
    def __init__(self, auth: AuthType):
        self._auth = auth
        self.is_ready = False # TODO
        self._client = None

    async def start(self):
        # TODO: логика авторизации и подстановки токена для начальной настройки
        if not self._auth.is_authorized():
            return
        headers = {
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(headers=headers)
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

    async def _get(self, endpoint: str, **kwargs):
        pass

    async def _post(self, endpoint: str, **kwargs):
        pass

