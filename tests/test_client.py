import pytest

from donatex import Client, errors
from donatex.auth import ExternalTokenAuth, OAuthConfidentialAuth, OAuthPublicAuth


def test_client_with_api_token_uses_external_auth():
    client = Client(api_token="TEST")

    assert isinstance(client._auth, ExternalTokenAuth)


def test_client_with_client_id_and_secret_uses_confidential_auth():
    client = Client(client_id="id", client_secret="secret")

    assert isinstance(client._auth, OAuthConfidentialAuth)


def test_client_with_client_id_only_uses_public_auth():
    client = Client(client_id="id")

    assert isinstance(client._auth, OAuthPublicAuth)


def test_client_without_any_credentials_raises_auth_config_error():
    with pytest.raises(errors.AuthConfigError):
        Client()


def test_client_with_api_token_ignores_invalid_scopes():
    client = Client(api_token="TEST", token_scopes={"donations.read", "not_a_scope"})

    assert isinstance(client._auth, ExternalTokenAuth)


def test_client_confidential_oauth_rejects_invalid_scopes():
    with pytest.raises(errors.InvalidScopeError):
        Client(
            client_id="id",
            client_secret="secret",
            token_scopes={"donations.read", "not_a_scope"},
        )


def test_client_public_oauth_rejects_invalid_scopes():
    with pytest.raises(errors.InvalidScopeError):
        Client(client_id="id", token_scopes={"donations.read", "not_a_scope"})


def test_client_confidential_oauth_rejects_empty_scopes():
    with pytest.raises(errors.AuthConfigError):
        Client(client_id="id", client_secret="secret", token_scopes=set())


def test_client_public_oauth_rejects_empty_scopes():
    with pytest.raises(errors.AuthConfigError):
        Client(client_id="id", token_scopes=set())


async def test_client_start_stop_lifecycle():
    client = Client(api_token="TEST")

    assert await client.connect() is True

    await client.disconnect()


async def test_client_context_manager_starts_and_stops():
    async with Client(api_token="TEST") as client:
        assert client._connected is True

    assert client._connected is False


async def test_client_stop_without_start_raises_connection_error():
    client = Client(api_token="TEST")

    with pytest.raises(ConnectionError):
        await client.stop()
