from .api import Api
from .auth import ExternalTokenAuth, OAuthConfidentialAuth, OAuthPublicAuth
from .errors import AuthConfigError
from .types import TokenScope
from ._transport import Transport


class Client:
    """DonateX клиент, основа для общения с DonateX API

    Parameters:
        api_token (``str``):
            Готовый External token для авторизации одного стримера
            Имеет приоритет над остальными способами аутентификациию

        client_id (``str``):
            OAuth ID клиента (конфиденциальный/публичный) для авторизации нескольких
            пользователей

        client_secret (``str``):
            OAuth Secret конфиденциального клиента
            Используется только в связке с ``client_id``
        
        token_scopes (``set[TokenScope]``):
            Scopes access-токена, запрашиваемые при авторизации.
            Используется только в связке с ``OAuth`` авторизацией 

    """

    def __init__(
        self,
        api_token: str = None,
        client_id: str = None,
        client_secret: str = None,
        token_scopes: frozenset[TokenScope] = set(),
    ):
        self._connected = False

        if api_token:
            self._auth = ExternalTokenAuth(api_token)
        elif client_id and client_secret:
            self._auth = OAuthConfidentialAuth(client_id, client_secret)
        elif client_id:
            self._auth = OAuthPublicAuth(client_id)
        else:
            raise AuthConfigError("")  # TODO

        self._transport = Transport(self._auth)
        self._api = Api(self._transport)

    async def _invoke(self):
        pass

    # region Public Methods

    async def connect(self):
        """Подключить клиент"""

    async def start(self):
        """Запустить клиент

        Этот метод запускает транспорт и, по необходимости, запрашивает авторизацию (если указаны OAuth ключи)
        """
        return self

    async def stop(self):
        if not self._connected:
            raise ConnectionError("Клиент уже остановлен")
        return

    async def authorize(self):
        pass

    # endregion Public Methods

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, *_):
        try:
            await self.stop()
        except ConnectionError:
            pass
