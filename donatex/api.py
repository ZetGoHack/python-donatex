from .types import User
from ._transport import Transport

BASE_API_URL = "https://donatex.gg/api"


class Api:
    """DonateX API - формирует API запросы, парсит ответы в рабочие классы"""

    def __init__(self, transport: Transport, base_url: str = BASE_API_URL):
        self._transport = transport
        self._api_url = base_url


    # region Public Methods


    async def get_me(self) -> User:
        raw = await self._send_request("/v1/user/me", "GET")

        result = User._parse(raw)

        return result


    # endregion

    async def _connect(self):
        return await self._transport.start()

    async def _disconnect(self):
        return await self._transport.stop()

    async def _send_request(self, endpoint: str, method: str, data: dict = None):
        data = data if data else dict()
        method = method.upper()
        url = self._api_url + endpoint

        if method == "GET":
            runner = self._transport._get
            result = await runner(url, params=data)

        elif method == "POST":
            runner = self._transport._post

            result = await runner(url, json=data)

        elif method == "DELETE":
            runner = self._transport._delete

            result = await runner(url)

        else:
            raise ValueError(f"Unknown method: {method}")

        return result


