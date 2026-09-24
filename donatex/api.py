import asyncio
import time
import secrets

from . import types, errors
from ._transport import Transport

BASE_API_URL = "https://donatex.gg/api"

_GET_DONATIONS_LIMIT_MAX = 100

# Лимиты DonateX API из документации
_RATE_LIMIT_PER_SECOND = 10
_RATE_LIMIT_PER_MINUTE = 600
_RATE_LIMIT_PER_HOUR = 10000

_MIN_REQUEST_INTERVAL = max(
    1 / _RATE_LIMIT_PER_SECOND,
    60 / _RATE_LIMIT_PER_MINUTE,
    3600 / _RATE_LIMIT_PER_HOUR,
)


class ApiLimiter:
    """держит фиксированный интервал между запросами, чтобы не превышать
    рейтлимиты API (10/сек, 600/мин, 10000/час)."""

    def __init__(self, min_interval: float = _MIN_REQUEST_INTERVAL):
        self._min_interval = min_interval
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def fw_protection(self):
        async with self._lock:
            now = time.monotonic()
            delay = self._min_interval - (now - self._last_call)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last_call = time.monotonic()


class Api:
    """DonateX API - формирует API запросы, парсит ответы в рабочие классы"""

    def __init__(
        self,
        transport: Transport,
        base_url: str = BASE_API_URL,
        limiter: ApiLimiter | None = None,
    ):
        self._transport = transport
        self._api_url = base_url
        self._api_limiter = limiter or ApiLimiter()

    # region Public Methods

    async def get_me(self):
        raw = await self._send_request("/v1/user/me", "GET")

        result = types.User._parse(raw)

        return result

    async def get_donations(
        self,
        offset: int,
        limit: int,
        query: str | None,
        hide_test: bool | None,
        period: types.PeriodScope | None,
        custom_period: types.CustomPeriod | None,
        sort_order: types.SortScope | None,
        auto_paginate: bool,
    ):
        data = {}

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

        raw_results: list[dict] = []
        current_offset = offset
        remaining = limit

        while remaining > 0:
            take = min(_GET_DONATIONS_LIMIT_MAX, remaining)
            page_data = {**data, "skip": current_offset, "take": take}

            page: list[dict] = await self._send_request(
                "/v1/donations", "GET", data=page_data
            )
            raw_results.extend(page)

            if not auto_paginate or len(page) < take:
                break

            current_offset += take
            remaining -= take

        return [types.Donation._parse(raw) for raw in raw_results]

    async def get_current_track(self):
        raw = await self._send_request("/v1/music/current", "GET")

        result = types.TrackState._parse(raw)

        return result

    async def get_current_goal(self):
        try:
            raw = await self._send_request("/v1/goals/current", "GET")
        except errors.ApiError as e:
            if e.status_code == 404:
                return None
            raise

        result = types.GoalState._parse(raw)

        return result

    async def get_donators_top(self, period: types.PeriodScope, count: int | None):
        data = {"period": period}

        if count is not None:
            data["count"] = count

        raw_results: list[dict] = await self._send_request(
            "/v1/top-donators", "GET", data
        )

        return [types.TopDonator._parse(raw) for raw in raw_results]

    async def get_characters(self):
        raw_results: list[dict] = await self._send_request("/v1/ai/characters", "GET")

        return [types.AICharacter._parse(raw) for raw in raw_results]

    async def get_character(self, id: str):
        endpoint = f"/v1/ai/characters/{id}"

        try:
            raw = await self._send_request(endpoint, "GET")
        except errors.ApiError as e:
            if e.status_code == 404:
                raise errors.NotFoundError(
                    f"Персонаж {id!r} не найден, удалён или принадлежит другому пользователю",
                    status_code=404,
                ) from e
            raise

        result = types.AICharacter._parse(raw)

        return result

    async def get_subscriptions(self):
        raw_results: list[dict] = await self._send_request(
            "/v1/webhooks/subscriptions", "GET"
        )

        return [types.WebhookSubscription._parse(raw) for raw in raw_results]

    async def send_test_donation(
        self,
        username: str,
        amount: float,
        currency: types.CurrencyScope,
        message: str | None,
        ai_response: bool | None,
    ):
        data = {"username": username, "amount": amount, "currency": currency}

        if message is not None:
            data["message"] = message
        if ai_response is not None:
            data["withAIResponse"] = ai_response

        raw = await self._send_request("/v1/test-donation", "POST", data)

        return raw

    async def skip_donation(self, id: str):
        endpoint = f"/v1/donations/{id}/skip"

        raw = await self._send_request(endpoint, "POST")

        return raw

    async def skip_current_track(self):
        raw = await self._send_request("/v1/music/skip-current", "POST")

        result = types.TrackSkipResult._parse(raw)

        return result

    async def skip_current_donation(self):
        raw = await self._send_request("/v1/donations/skip-current", "POST")

        result = types.DonationSkipResult._parse(raw)

        return result

    async def create_subscription(
        self,
        url: str,
        event_type: types.EventTypeScope,
        client_id: str | None,
        secret: str | None,
    ):
        if not url.startswith("https://"):
            raise errors.ArgumentsConflictError("url подписки должен быть HTTPS")

        secret = secret or secrets.token_urlsafe(32)

        data = {
            "url": url,
            "eventType": event_type,
            "secret": secret,
        }

        if client_id is not None:
            data["clientId"] = client_id

        raw = await self._send_request("/v1/webhooks/subscriptions", "POST", data)

        result = types.SubscriptionCreated(
            subscription=types.WebhookSubscription._parse(raw),
            secret=secret,
        )

        return result

    async def delete_subscription(self, id: str):
        endpoint = f"/v1/webhooks/subscriptions/{id}"

        raw = await self._send_request(endpoint, "DELETE")

        return raw

    async def activate_subscription(self, id: str):
        endpoint = f"/v1/webhooks/subscriptions/{id}/activate"

        raw = await self._send_request(endpoint, "POST")

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

        await self._api_limiter.fw_protection()

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
