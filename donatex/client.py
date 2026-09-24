from .api import Api
from .auth import ExternalTokenAuth, OAuthConfidentialAuth, OAuthPublicAuth
from . import errors
from . import types
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

        token_scopes (``frozenset[str]``):
            Scopes access-токена, запрашиваемые при авторизации.
            Используется только в связке с ``OAuth`` авторизацией.
            Список из: ``"donations.read"``, ``"donations.write"``, ``"user.read"``,
            ``"donations.subscribe"``, ``"offline_access"``, ``"openid"``, ``"profile"``
            Дефолт: ``{"openid", "offline_access", "donations.read"}``

        proxy (``str``, *optional*):
            Прокси для HTTP-транспорта (например ``"http://user:pass@host:port"``).
            По умолчанию клиент не читает системные настройки прокси

    """

    def __init__(
        self,
        api_token: str = None,
        client_id: str = None,
        client_secret: str = None,
        token_scopes: set[types.TokenScope] = set(
            {"openid", "offline_access", "donations.read"}
        ),
        proxy: str | None = None,
    ):
        self._connected = False

        if api_token:
            self._auth = ExternalTokenAuth(api_token)
        elif client_id and client_secret:
            self._auth = OAuthConfidentialAuth(
                client_id, client_secret, scopes=token_scopes
            )
        elif client_id:
            self._auth = OAuthPublicAuth(client_id, scopes=token_scopes)
        else:
            raise errors.AuthConfigError(
                "Не было указано достаточно аргументов для выбора авторизации"
            )

        self._transport = Transport(self._auth, proxy=proxy)
        self._auth._bind_transport(self._transport._token_request)
        self._api = Api(self._transport)

    async def _invoke(self, api_method):
        if not self._connected:
            raise ConnectionError("Клиент ещё не был запущен")

        return await api_method

    # region Public Methods

    async def connect(self) -> bool:
        """Поднять транспорт (HTTP-клиент). Для OAuth это ещё не значит,
        что клиент авторизован - до вызова `authorize(code)` запросы к
        API будут падать с `AuthRequiredError`"""
        await self._api._connect()

        self._connected = True
        return True

    async def disconnect(self):
        """Отключить клиент"""
        await self._api._disconnect()

        self._connected = False

    async def start(self):
        """Запустить клиент (поднять транспорт)

        Для OAuth требуется авторизация. Проходит отдельным
        шагом через `get_authorize_url()`/`authorize()`.
        """
        if await self.connect():
            return self

    async def get_me(self) -> types.User:
        """Получить данные текущего авторизованного пользователя

        Этот метод возвращает обработанный ``donatex.types.User``"""
        return await self._invoke(self._api.get_me())

    async def get_donations(
        self,
        offset: int,
        limit: int,
        query: str | None = None,
        hide_test: bool | None = None,
        period: types.PeriodScope | None = None,
        custom_period: types.CustomPeriod | None = None,
        sort_order: types.SortScope | None = None,
        auto_paginate: bool = False,
    ) -> list[types.Donation]:
        """Поиск, фильтрация по периоду и пагинация донатов стримера. По умолчанию возвращаются все донаты от новых к старым.

        Parameters:
            offset (``int``):
                Смещение

            limit (``int``):
                Количество записей. До 100 результатов за запрос. Можно указать больше с
                ``auto_paginate=True``

            query (``str``, *optional*):
                Поиск по тексту сообщения или нику

            hide_test (``bool``, *optional*):
                Скрыть тестовые донаты

            period (``str``, *optional*):
                Период выборки. Один из: ``"Day"``, ``"Week"``, ``"Month"``, ``"AllTime"``,
                ``"CurrentStream"``, ``"Last24Hours"``, ``"Last7Days"``, ``"Last30Days"``,
                ``"CurrentYear"``, ``"Last365Days"``. Конфликтует с ``custom_period``

            custom_period (:class:`~donatex.types.CustomPeriod`):
                Свой период выборки с указанной начальной и конечной UTC датой.
                Время не учитывается

            sort_order (``str``, *optional*):
                Порядок сортировки. Один из: ``"NewestFirst"``, ``"OldestFirst"``

            auto_paginate (``bool``, *optional*):
                Автоматическая пагинация с получением ``limit`` объектов"""
        donations: list[types.Donation] = await self._invoke(
            self._api.get_donations(
                offset=offset,
                limit=limit,
                query=query,
                hide_test=hide_test,
                period=period,
                custom_period=custom_period,
                sort_order=sort_order,
                auto_paginate=auto_paginate,
            )
        )
        for donation in donations:
            donation._bind(self)

        return donations

    async def get_current_track(self) -> types.TrackState:
        """Возвращает текущее состояние воспроизведения: играет ли сейчас музыка и какой трек
        стоит первым в очереди.

        ⚠️ Чтобы трек попал в очередь, донат должен быть показан на стриме, или скипнут через API
        """
        return await self._invoke(self._api.get_current_track())

    async def get_current_goal(self) -> types.GoalState | None:
        """Возвращает активную цель стримера. Суммы цели всегда представлены в рублях.
        Если активной цели нет, возвращает ``None``"""
        return await self._invoke(self._api.get_current_goal())

    async def get_donators_top(
        self, period: types.PeriodScope, count: int = 10
    ) -> list[types.TopDonator]:
        """Возвращает топ донатеров стримера за выбранный период, отсортированный по
        суммарной сумме донатов в рублях. Учитывает скрытых донатеров из настроек стримера.
        """
        return await self._invoke(self._api.get_donators_top(period, count))

    async def get_characters(self) -> list[types.AICharacter]:
        """Возвращает персонажей владельца токена, включая неактивных. Удалённые персонажи
        не возвращаются. Если персонажей нет, ответ — пустой массив []. Сортировка: по имени,
        затем по ID"""
        return await self._invoke(self._api.get_characters())

    async def get_character(self, id: str) -> types.AICharacter:
        """Получить ИИ-персонажа по id

        Кидает ``NotFoundError``, если персонаж не найден, удалён или
        принадлежит другому пользователю"""
        return await self._invoke(self._api.get_character(id))

    async def get_subscriptions(self) -> list[types.WebhookSubscription]:
        """Получить список активных подписок текущего стримера

        ⚠️ Удалённые через ``delete()``/``delete_subscription()`` подписки в этот
        список не попадают, хотя формально не стёрты — их можно вернуть через
        ``activate()``/``activate_subscription()`` по сохранённому ``id``"""
        subscriptions: list[types.WebhookSubscription] = await self._invoke(
            self._api.get_subscriptions()
        )
        for subscription in subscriptions:
            subscription._bind(self)

        return subscriptions

    async def send_test_donation(
        self,
        username: str,
        amount: float,
        currency: types.CurrencyScope,
        message: str | None = None,
        ai_response: bool = None,
    ) -> None:
        """Отправляет тестовый донат

        Parameters:
            username (``str``):
                Имя донатера

            amount (``float``):
                Сумма

            currency (``str``):
                Валюта доната. Может быть одной из ``"RUB"``, ``"USD"``,
                ``"KZT"``, ``"EUR"``

            ai_response (``bool``, *optional*):
                Синтез ответа ИИ (если разрешено)

            message (``str``, *optional*):
                Текст сообщения"""
        return await self._invoke(
            self._api.send_test_donation(
                username, amount, currency, message, ai_response
            )
        )

    async def skip_donation(self, id: str) -> None:
        """Пропускает конкретный донат по его ID — независимо от того, является ли он текущим в очереди.
        Помечает донат как показанный"""
        return await self._invoke(self._api.skip_donation(id))

    async def skip_current_track(self) -> types.TrackSkipResult:
        """Пропускает текущий трек в музыкальном виджете стримера и помечает донат как воспроизведенный"""
        return await self._invoke(self._api.skip_current_track())

    async def skip_current_donation(self) -> types.DonationSkipResult:
        """Пропускает текущий показываемый донат (TTS, анимация). Аналог кнопки «Скип» в личном
        кабинете стримера. Помечает донат как показанный"""
        return await self._invoke(self._api.skip_current_donation())

    async def create_subscription(
        self,
        url: str,
        event_type: types.EventTypeScope,
        secret: str | None = None,
        client_id: str | None = None,
    ) -> types.SubscriptionCreated:
        """Регистрирует webhook. Требуется HTTPS и секрет для подписи

        Возвращает ``(subscription, secret)`` - если ``secret`` не указан,
        он генерируется автоматически"""
        if client_id is None and self._auth._TYPE != "EXTERNAL":
            client_id = self._auth._client_id

        result: types.SubscriptionCreated = await self._invoke(
            self._api.create_subscription(url, event_type, client_id, secret)
        )
        result.subscription._bind(self)

        return result

    async def delete_subscription(self, id: str) -> None:
        """Мягкое удаление подписки. Доставки прекращаются, подписку можно снова активировать"""
        return await self._invoke(self._api.delete_subscription(id))

    async def activate_subscription(self, id: str) -> None:
        """Повторно включает ранее отключенную подписку и сбрасывает счетчик ошибок"""
        return await self._invoke(self._api.activate_subscription(id))

    async def stop(self):
        """Остановить клиент и закрыть транспорт

        Кидает ``ConnectionError``, если клиент уже остановлен или ещё не был запущен"""
        if not self._connected:
            raise ConnectionError("Клиент уже остановлен")

        await self.disconnect()
        return

    def get_authorize_url(
        self, redirect_uri: str, state: str | None = None
    ) -> types.AuthorizeUrl:
        """Ссылка для получения согласия пользователя при OAuth авторизации

        Откройте её в браузере - после согласия DonateX сделает редирект на
        ``redirect_uri`` с параметром ``code`` в query, который нужно передать
        в `authorize()`
        Не имеет смысла при авторизации через ``api_token``

        Parameters:
            redirect_uri (``str``):
                URL, на который DonateX вернёт пользователя с ``code``.
                Должен совпадать с тем, что зарегистрирован у OAuth приложения

            state (``str``, *optional*):
                Произвольное значение для защиты от CSRF — вернётся в редиректе
                без изменений, сверьте его на своей стороне

        Возвращает ``(url, code_verifier)``. Если ``authorize()`` будет вызван
        в другом экземпляре ``Client``, сохраните ``code_verifier`` на
        своей стороне и передайте его в ``authorize()``
        """
        if self._auth._TYPE == "EXTERNAL":
            raise errors.AuthConfigError(
                "get_authorize_url() не применим при авторизации через api_token"
            )
        return self._auth.get_authorize_url(redirect_uri, state=state)

    async def authorize(
        self,
        code: str,
        code_verifier: str | None = None,
        redirect_uri: str | None = None,
    ) -> None:
        """Обменять ``code`` из редиректа на access/refresh токены и завершить OAuth авторизацию

        Не нужен при авторизации через ``api_token`` - вызов будет проигнорирован

        Parameters:
            code (``str``):
                Значение параметра ``code`` из query редиректа на ваш ``redirect_uri``

            code_verifier (``str``, *optional*):
                ``code_verifier`` из ``get_authorize_url()``. Нужен, только если
                ссылка была получена в другом экземпляре ``Client``

            redirect_uri (``str``, *optional*):
                Тот же ``redirect_uri``, что и в ``get_authorize_url()``. Нужен
                вместе с ``code_verifier``
        """
        if self._auth._TYPE == "EXTERNAL":
            return

        await self._auth.authorize(
            code, code_verifier=code_verifier, redirect_uri=redirect_uri
        )

    # endregion Public Methods

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, *_):
        try:
            await self.stop()
        except ConnectionError:
            pass
