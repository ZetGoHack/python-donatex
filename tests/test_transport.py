import httpx
import pytest

from donatex.auth import ExternalTokenAuth
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
