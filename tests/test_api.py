import asyncio
import datetime
import time
from unittest.mock import AsyncMock

import pytest

from donatex import types, errors
from donatex.api import Api, ApiLimiter


def make_api() -> tuple[Api, AsyncMock]:
    mock_transport = AsyncMock()
    api = Api(mock_transport, limiter=ApiLimiter(min_interval=0))
    return api, mock_transport


async def test_get_me_requests_correct_endpoint_and_parses_user():
    api, transport = make_api()
    transport._get.return_value = {
        "id": "u1",
        "username": "zgo",
        "avatarUrl": "https://x/a.png",
    }

    user = await api.get_me()

    transport._get.assert_awaited_once()
    called_url = transport._get.call_args.args[0]
    assert called_url.endswith("/v1/user/me")
    assert isinstance(user, types.User)
    assert user.username == "zgo"


async def test_get_donations_conflicting_period_args_raise():
    api, _ = make_api()

    with pytest.raises(errors.ArgumentsConflictError):
        await api.get_donations(
            offset=0,
            limit=10,
            period="Day",
            custom_period=types.CustomPeriod(
                start_date=datetime.datetime(2026, 1, 1),
                end_date=datetime.datetime(2026, 1, 2),
            ),
        )


async def test_get_donations_single_page_without_auto_paginate(donation_raw):
    api, transport = make_api()
    transport._get.return_value = [donation_raw()] * 100

    result = await api.get_donations(offset=0, limit=250, auto_paginate=False)

    assert transport._get.await_count == 1
    assert len(result) == 100


async def test_get_donations_auto_paginate_stops_when_page_smaller_than_take(donation_raw):
    api, transport = make_api()

    transport._get.side_effect = [
        [donation_raw(id=f"a{i}") for i in range(100)],
        [donation_raw(id=f"b{i}") for i in range(20)],
    ]

    result = await api.get_donations(offset=0, limit=150, auto_paginate=True)

    assert transport._get.await_count == 2
    assert len(result) == 120

    first_call_params = transport._get.call_args_list[0].kwargs["params"]
    second_call_params = transport._get.call_args_list[1].kwargs["params"]
    assert first_call_params["skip"] == 0
    assert first_call_params["take"] == 100
    assert second_call_params["skip"] == 100
    assert second_call_params["take"] == 50


async def test_limiter_enforces_min_interval_between_calls():
    limiter = ApiLimiter(min_interval=0.05)

    t0 = time.monotonic()
    await limiter.fw_protection()
    await limiter.fw_protection()
    elapsed = time.monotonic() - t0

    assert elapsed >= 0.05


async def test_limiter_serializes_concurrent_calls():
    limiter = ApiLimiter(min_interval=0.05)

    t0 = time.monotonic()
    await asyncio.gather(*(limiter.fw_protection() for _ in range(3)))
    elapsed = time.monotonic() - t0

    assert elapsed >= 0.1
