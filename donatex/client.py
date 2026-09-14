from .api import Api
from .auth import ExternalTokenAuth, OAuthConfidentialAuth, OAuthPublicAuth
from .errors import AuthConfigError
from ._transport import Transport


class Client:
    """DonateX клиент, основа для общения с DonateX API

    Параметры:
        api_token (``str``):
            Готовый External token для авторизации одного стримера
            Имеет приоритет над остальными способами аутентификациию
        
        client_id (``str``):
            ID клиента (конфиденциальный/публичный) для авторизации нескольких
            пользователей

        client_secret (``str``):
            Secret конфиденциального клиента
            Используется только в связке с ``client_id``

    """
    def __init__(self, api_token: str = None, client_id: str = None, client_secret: str = None):
        if api_token:
            self._auth = ExternalTokenAuth(api_token)
        elif client_id and client_secret:
            return # TODO
            self._auth = OAuthConfidentialAuth(client_id, client_secret)
        elif client_id:
            self._auth = OAuthPublicAuth(client_id)
        else:
            raise AuthConfigError(
                "" # TODO
            )

        self._transport = Transport(self._auth)
        self._api = Api(self._transport)

    async def _invoke(self):
        pass

    # region Public Methods

    async def start(self):
        pass

    async def authorize(self):
        pass

    # endregion Public Methods