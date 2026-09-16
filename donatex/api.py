from . import types, errors
from ._transport import Transport

BASE_API_URL = "https://donatex.gg/api"


class Api:
    """DonateX API - формирует API запросы, парсит ответы в рабочие классы"""

    def __init__(self, transport: Transport, base_url: str = BASE_API_URL):
        self._transport = transport
        self._api_url = base_url

    # region Public Methods

    async def get_me(self) -> types.User:
        raw = await self._send_request("/v1/user/me", "GET")

        result = types.User._parse(raw)

        return result

    async def get_donations(
        self,
        offset: int,
        limit: int,
        query: str | None = None,
        hide_test: bool | None = None,
        period: types.PeriodScope | None = None,
        custom_period: types.CustomPeriod | None = None,
        sort_order: types.SortScope | None = None,
    ):
        data = {
            "skip": offset,
            "take": limit,
        }

        if query is not None:
            data["query"] = query

        if hide_test is not None:
            data["hideTest"] = hide_test

        if period is not None:
            if custom_period is None:
                data["period"] = period
            else:
                raise errors.ArgumentsConflictError(
                    "Указаны конфликтующие аргументы:"
                    " `period` и `custom_period` не могут быть указаны одновременно"
                )

        if custom_period is not None:
            data.update(custom_period.to_params())

        if sort_order is not None:
            data["sortOrder"] = sort_order

        raw: list[dict] = await self._send_request("/v1/donations", "GET", data=data)

        # TODO: Donation class

        return raw

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
