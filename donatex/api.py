from ._transport import Transport

BASE_API_URL = "https://donatex.gg/api/"


class Api:
    """DonateX API"""

    def __init__(self, transport: Transport, base_url: str = BASE_API_URL):
        self._transport = transport

    async def _send_request(self, endpoint: str, method: str):
        pass


