import httpx

from .auth import AuthType


class Transport:
    def __init__(self, auth: AuthType):
        self._auth = auth
        self._client = httpx.AsyncClient()

    async def _get(self, endpoint: str, **kwargs):
        pass

    async def _post(self, endpoint: str, **kwargs):
        pass

