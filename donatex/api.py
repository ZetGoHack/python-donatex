from ._transport import Transport

BASE_API_URL = "https://donatex.gg/api/"


class Api:
    """DonateX API - формирует API запросы, парсит ответы в рабочие классы"""

    def __init__(self, transport: Transport, base_url: str = BASE_API_URL):
        self._transport = transport
        self._api_url = base_url

    async def _connect(self):
        return await self._transport.start()

    async def _disconnect(self):
        return await self._transport.stop()

    async def _send_request(self, endpoint: str, method: str):
        pass


