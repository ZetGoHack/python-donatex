from .api import Api
from .auth import ExternalTokenAuth, OAuthConfidentialAuth, OAuthPublicAuth
from .errors import AuthConfigError
from .types import TokenScope
from .utils import validate_scopes
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
            Дефолт: ``{"openid", "offline_access", "donations.read"}``

    """

    def __init__(
        self,
        api_token: str = None,
        client_id: str = None,
        client_secret: str = None,
        token_scopes: set[TokenScope] = set({"openid", "offline_access", "donations.read"}),
    ):
        self._connected = False

        validate_scopes(token_scopes)

        if api_token:
            self._auth = ExternalTokenAuth(api_token)
        elif client_id and client_secret:
            self._auth = OAuthConfidentialAuth(client_id, client_secret, scopes=token_scopes)
        elif client_id:
            self._auth = OAuthPublicAuth(client_id, scopes=token_scopes)
        else:
            raise AuthConfigError("Не было указано достаточно аргументов для выбора авторизации")

        self._transport = Transport(self._auth)
        self._api = Api(self._transport)

    async def _invoke(self):
        pass

    # region Public Methods

    async def connect(self) -> bool:
        """Подключить клиент"""
        await self._api._connect() # TODO

        self._connected = True

        return True

    async def disconnect(self):
        """Отключить клиент"""
        await self._api._disconnect()

        self._connected = False

    async def start(self):
        """Запустить клиент

        Этот метод запускает транспорт и, по необходимости, запрашивает авторизацию (если указаны OAuth ключи)
        """
        if await self.connect():
            return self

        # TODO: флоу авторизации

        

    async def stop(self):
        if not self._connected:
            raise ConnectionError("Клиент уже остановлен")

        await self.disconnect()
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
