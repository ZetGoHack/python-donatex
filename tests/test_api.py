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
            query=None,
            hide_test=None,
            period="Day",
            custom_period=types.CustomPeriod(
                start_date=datetime.datetime(2026, 1, 1),
                end_date=datetime.datetime(2026, 1, 2),
            ),
            sort_order=None,
            auto_paginate=False,
        )


async def test_get_donations_single_page_without_auto_paginate(donation_raw):
    api, transport = make_api()
    transport._get.return_value = [donation_raw()] * 100

    result = await api.get_donations(
        offset=0,
        limit=250,
        query=None,
        hide_test=None,
        period=None,
        custom_period=None,
        sort_order=None,
        auto_paginate=False,
    )

    assert transport._get.await_count == 1
    assert len(result) == 100


async def test_get_donations_auto_paginate_stops_when_page_smaller_than_take(
    donation_raw,
):
    api, transport = make_api()

    transport._get.side_effect = [
        [donation_raw(id=f"a{i}") for i in range(100)],
        [donation_raw(id=f"b{i}") for i in range(20)],
    ]

    result = await api.get_donations(
        offset=0,
        limit=150,
        query=None,
        hide_test=None,
        period=None,
        custom_period=None,
        sort_order=None,
        auto_paginate=True,
    )

    assert transport._get.await_count == 2
    assert len(result) == 120

    first_call_params = transport._get.call_args_list[0].kwargs["params"]
    second_call_params = transport._get.call_args_list[1].kwargs["params"]
    assert first_call_params["skip"] == 0
    assert first_call_params["take"] == 100
    assert second_call_params["skip"] == 100
    assert second_call_params["take"] == 50


async def test_get_current_goal_requests_correct_endpoint(goal_raw):
    api, transport = make_api()
    transport._get.return_value = goal_raw

    result = await api.get_current_goal()

    called_url = transport._get.call_args.args[0]
    assert called_url.endswith("/v1/goals/current")
    assert isinstance(result, types.GoalState)
    assert result.id == "goal-1"


async def test_get_current_goal_returns_none_on_404():
    api, transport = make_api()
    transport._get.side_effect = errors.ApiError("not found", status_code=404)

    result = await api.get_current_goal()

    assert result is None


async def test_get_current_goal_reraises_non_404_errors():
    api, transport = make_api()
    transport._get.side_effect = errors.ApiError("server error", status_code=500)

    with pytest.raises(errors.ApiError):
        await api.get_current_goal()


async def test_get_current_track_requests_correct_endpoint(track_raw):
    api, transport = make_api()
    transport._get.return_value = track_raw

    result = await api.get_current_track()

    called_url = transport._get.call_args.args[0]
    assert called_url.endswith("/v1/music/current")
    assert isinstance(result, types.TrackState)
    assert result.is_playing is True


async def test_get_donators_top_omits_count_when_not_given(top_donator_raw):
    api, transport = make_api()
    transport._get.return_value = [top_donator_raw]

    result = await api.get_donators_top(period="Day", count=None)

    called_params = transport._get.call_args.kwargs["params"]
    assert called_params == {"period": "Day"}
    assert isinstance(result[0], types.TopDonator)


async def test_get_donators_top_includes_count_when_given(top_donator_raw):
    api, transport = make_api()
    transport._get.return_value = [top_donator_raw]

    result = await api.get_donators_top(period="Day", count=5)

    called_params = transport._get.call_args.kwargs["params"]
    assert called_params == {"period": "Day", "count": 5}
    assert isinstance(result[0], types.TopDonator)


async def test_get_characters_requests_correct_endpoint(character_raw):
    api, transport = make_api()
    transport._get.return_value = [character_raw]

    result = await api.get_characters()

    called_url = transport._get.call_args.args[0]
    assert called_url.endswith("/v1/ai/characters")
    assert isinstance(result[0], types.AICharacter)


async def test_get_character_requests_correct_endpoint(character_raw):
    api, transport = make_api()
    transport._get.return_value = character_raw

    result = await api.get_character("char-1")

    called_url = transport._get.call_args.args[0]
    assert called_url.endswith("/v1/ai/characters/char-1")
    assert isinstance(result, types.AICharacter)
    assert result.id == "char-1"


async def test_get_character_raises_not_found_on_404():
    api, transport = make_api()
    transport._get.side_effect = errors.ApiError("not found", status_code=404)

    with pytest.raises(errors.NotFoundError):
        await api.get_character("missing")


async def test_get_character_reraises_non_404_errors():
    api, transport = make_api()
    transport._get.side_effect = errors.ApiError("server error", status_code=500)

    with pytest.raises(errors.ApiError) as exc_info:
        await api.get_character("id")

    assert not isinstance(exc_info.value, errors.NotFoundError)


async def test_get_subscriptions_requests_correct_endpoint():
    api, transport = make_api()
    transport._get.return_value = []

    await api.get_subscriptions()

    called_url = transport._get.call_args.args[0]
    assert called_url.endswith("/v1/webhooks/subscriptions")


async def test_send_test_donation_omits_optional_fields_when_not_given():
    api, transport = make_api()
    transport._post.return_value = None

    await api.send_test_donation(
        username="zgo", amount=100.0, currency="RUB", message=None, ai_response=None
    )

    called_json = transport._post.call_args.kwargs["json"]
    assert called_json == {"username": "zgo", "amount": 100.0, "currency": "RUB"}


async def test_send_test_donation_includes_optional_fields_when_given():
    api, transport = make_api()
    transport._post.return_value = None

    await api.send_test_donation(
        username="zgo", amount=100.0, currency="RUB", message="hi", ai_response=True
    )

    called_json = transport._post.call_args.kwargs["json"]
    assert called_json == {
        "username": "zgo",
        "amount": 100.0,
        "currency": "RUB",
        "message": "hi",
        "withAIResponse": True,
    }


async def test_skip_donation_posts_to_correct_endpoint():
    api, transport = make_api()
    transport._post.return_value = None

    await api.skip_donation("d1")

    called_url = transport._post.call_args.args[0]
    assert called_url.endswith("/v1/donations/d1/skip")


async def test_skip_current_track_posts_to_correct_endpoint(track_skip_raw):
    api, transport = make_api()
    transport._post.return_value = track_skip_raw

    result = await api.skip_current_track()

    called_url = transport._post.call_args.args[0]
    assert called_url.endswith("/v1/music/skip-current")
    assert isinstance(result, types.TrackSkipResult)


async def test_skip_current_donation_posts_to_correct_endpoint():
    api, transport = make_api()
    transport._post.return_value = {"skipped": True, "skippedDonationId": "d1"}

    result = await api.skip_current_donation()

    called_url = transport._post.call_args.args[0]
    assert called_url.endswith("/v1/donations/skip-current")
    assert isinstance(result, types.DonationSkipResult)
    assert result.skipped_donation_id == "d1"


async def test_create_subscription_rejects_non_https_url():
    api, _ = make_api()

    with pytest.raises(errors.ArgumentsConflictError):
        await api.create_subscription(
            url="http://example.com/hook",
            event_type="DonationCreated",
            client_id=None,
            secret=None,
        )


async def test_create_subscription_generates_secret_when_not_given(subscription_raw):
    api, transport = make_api()
    transport._post.return_value = subscription_raw

    result = await api.create_subscription(
        url="https://example.com/hook",
        event_type="DonationCreated",
        client_id=None,
        secret=None,
    )

    called_json = transport._post.call_args.kwargs["json"]
    assert called_json["secret"]
    assert isinstance(result, types.SubscriptionCreated)
    assert result.secret == called_json["secret"]


async def test_create_subscription_returns_subscription_and_secret(subscription_raw):
    api, transport = make_api()
    transport._post.return_value = subscription_raw

    sub, secret = await api.create_subscription(
        url="https://example.com/hook",
        event_type="DonationCreated",
        client_id=None,
        secret=None,
    )

    assert isinstance(sub, types.WebhookSubscription)
    assert secret == transport._post.call_args.kwargs["json"]["secret"]


async def test_create_subscription_keeps_given_secret(subscription_raw):
    api, transport = make_api()
    transport._post.return_value = subscription_raw

    await api.create_subscription(
        url="https://example.com/hook",
        event_type="DonationCreated",
        client_id=None,
        secret="my-secret",
    )

    called_json = transport._post.call_args.kwargs["json"]
    assert called_json["secret"] == "my-secret"


@pytest.mark.parametrize(
    "client_id, expect_present",
    [(None, False), ("my-app", True)],
)
async def test_create_subscription_client_id_included_only_when_given(
    client_id, expect_present, subscription_raw
):
    api, transport = make_api()
    transport._post.return_value = subscription_raw

    await api.create_subscription(
        url="https://example.com/hook",
        event_type="DonationCreated",
        client_id=client_id,
        secret="my-secret",
    )

    called_json = transport._post.call_args.kwargs["json"]
    assert ("clientId" in called_json) == expect_present


async def test_delete_subscription_sends_delete_to_correct_endpoint():
    api, transport = make_api()
    transport._delete.return_value = None

    await api.delete_subscription("sub-1")

    called_url = transport._delete.call_args.args[0]
    assert called_url.endswith("/v1/webhooks/subscriptions/sub-1")


async def test_activate_subscription_posts_to_correct_endpoint():
    api, transport = make_api()
    transport._post.return_value = None

    await api.activate_subscription("sub-1")

    called_url = transport._post.call_args.args[0]
    assert called_url.endswith("/v1/webhooks/subscriptions/sub-1/activate")


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
