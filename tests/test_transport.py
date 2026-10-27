import httpx
import pytest

from donatex.auth import ExternalTokenAuth
from donatex import errors
from donatex.errors import ApiError, TransportNotReadyError
from donatex._transport import Transport


def make_transport(handler) -> Transport:
    transport = Transport(ExternalTokenAuth("test-token"))
    transport._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport.is_ready = True
    return transport


async def test_get_raises_when_transport_not_ready():
    transport = Transport(ExternalTokenAuth("test-token"))

    with pytest.raises(TransportNotReadyError):
        await transport._get("https://donatex.gg/api/v1/user/me")


async def test_get_returns_parsed_json_on_200():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(200, json={"id": "u1"})

    transport = make_transport(handler)

    result = await transport._get("https://donatex.gg/api/v1/user/me")

    assert result == {"id": "u1"}


async def test_get_raises_api_error_on_non_200():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="bad request")

    transport = make_transport(handler)

    with pytest.raises(ApiError):
        await transport._get("https://donatex.gg/api/v1/user/me")


async def test_post_returns_none_on_204():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    transport = make_transport(handler)

    result = await transport._post("https://donatex.gg/api/v1/test-donation")

    assert result is None


async def test_delete_raises_api_error_when_not_204():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="cannot delete")

    transport = make_transport(handler)

    with pytest.raises(ApiError):
        await transport._delete("https://donatex.gg/api/v1/webhooks/1")


async def test_stop_closes_underlying_httpx_client():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    transport = make_transport(handler)
    httpx_client = transport._client

    await transport.stop()

    assert httpx_client.is_closed is True
    assert transport._client is None
    assert transport.is_ready is False


@pytest.mark.parametrize(
    "status, exc",
    [
        (400, errors.BadRequestError),
        (401, errors.UnauthorizedError),
        (403, errors.ForbiddenError),
        (404, errors.NotFoundError),
        (405, errors.MethodNotAllowedError),
        (409, errors.ConflictError),
        (415, errors.UnsupportedMediaTypeError),
        (500, errors.ServerError),
        (503, errors.ServerError),
        (418, errors.ApiError),
    ],
)
async def test_status_maps_to_exception(status, exc):
    transport = make_transport(lambda _: httpx.Response(status, text="boom"))

    with pytest.raises(exc) as info:
        await transport._get("https://donatex.gg/api/v1/x")

    assert type(info.value) is exc
    assert info.value.status_code == status


async def test_empty_body_gets_default_message():
    transport = make_transport(lambda _: httpx.Response(401))

    with pytest.raises(errors.UnauthorizedError) as info:
        await transport._get("https://donatex.gg/api/v1/x")

    assert str(info.value)


async def test_problem_details_populates_errors_and_trace_id():
    body = {
        "title": "One or more validation errors occurred.",
        "status": 400,
        "errors": {"take": ["The value 'abc' is not valid."]},
        "traceId": "00-abc",
    }
    transport = make_transport(lambda _: httpx.Response(400, json=body))

    with pytest.raises(errors.BadRequestError) as info:
        await transport._get("https://donatex.gg/api/v1/x")

    assert info.value.errors == {"take": ["The value 'abc' is not valid."]}
    assert info.value.trace_id == "00-abc"
    assert "take" in str(info.value)


async def test_429_carries_retry_after_and_error_message():
    transport = make_transport(
        lambda _: httpx.Response(429, json={"error": "slow down"}, headers={"Retry-After": "7"})
    )

    with pytest.raises(errors.FloodWaitError) as info:
        await transport._post("https://donatex.gg/api/v1/x")

    assert info.value.retry_after == 7
    assert str(info.value) == "slow down"
    assert info.value.status_code == 429


async def test_429_without_retry_after_defaults_to_one_second():
    transport = make_transport(lambda _: httpx.Response(429, json={"error": "x"}))

    with pytest.raises(errors.FloodWaitError) as info:
        await transport._delete("https://donatex.gg/api/v1/x")

    assert info.value.retry_after == 1.0
