from unittest.mock import AsyncMock, MagicMock

import pytest

from donatex.auth import OAuthConfidentialAuth, OAuthPublicAuth


@pytest.mark.parametrize(
    "auth_cls, make_kwargs",
    [
        (OAuthConfidentialAuth, {"client_id": "id", "client_secret": "secret"}),
        (OAuthPublicAuth, {"client_id": "id"}),
    ],
)
async def test_get_access_token_does_not_refresh_when_not_expired(
    auth_cls, make_kwargs
):
    auth = auth_cls(**make_kwargs, scopes={"donations.read"})
    auth._access_token = "current-token"
    auth._expired = MagicMock(return_value=False)
    auth.refresh = AsyncMock()

    token = await auth.get_access_token()

    auth._expired.assert_called_once()
    auth.refresh.assert_not_awaited()
    assert token == "current-token"


@pytest.mark.parametrize(
    "auth_cls, make_kwargs",
    [
        (OAuthConfidentialAuth, {"client_id": "id", "client_secret": "secret"}),
        (OAuthPublicAuth, {"client_id": "id"}),
    ],
)
async def test_get_access_token_refreshes_when_expired(auth_cls, make_kwargs):
    auth = auth_cls(**make_kwargs, scopes={"donations.read"})
    auth._expired = MagicMock(return_value=True)
    auth.refresh = AsyncMock()

    await auth.get_access_token()

    auth.refresh.assert_awaited_once()


@pytest.mark.parametrize(
    "auth_cls, make_kwargs",
    [
        (OAuthConfidentialAuth, {"client_id": "id", "client_secret": "secret"}),
        (OAuthPublicAuth, {"client_id": "id"}),
    ],
)
def test_authorize_url_includes_pkce_challenge(auth_cls, make_kwargs):
    auth = auth_cls(**make_kwargs, scopes={"donations.read"})

    url = auth.get_authorize_url("https://example.com/callback")

    assert "code_challenge=" in url
    assert "code_challenge_method=S256" in url
    assert "client_id=id" in url
    assert auth._code_verifier is not None


@pytest.mark.parametrize(
    "auth_cls, make_kwargs",
    [
        (OAuthConfidentialAuth, {"client_id": "id", "client_secret": "secret"}),
        (OAuthPublicAuth, {"client_id": "id"}),
    ],
)
def test_token_payload_includes_code_verifier(auth_cls, make_kwargs):
    auth = auth_cls(**make_kwargs, scopes={"donations.read"})
    auth.get_authorize_url("https://example.com/callback")

    payload = auth._build_token_payload("the-code")

    assert payload["code_verifier"] == auth._code_verifier


@pytest.mark.parametrize(
    "auth_cls, make_kwargs",
    [
        (OAuthConfidentialAuth, {"client_id": "id", "client_secret": "secret"}),
        (OAuthPublicAuth, {"client_id": "id"}),
    ],
)
async def test_authorize_exchanges_code_and_stores_tokens(auth_cls, make_kwargs):
    auth = auth_cls(**make_kwargs, scopes={"donations.read"})
    auth.get_authorize_url("https://example.com/callback")
    auth._bind_transport(
        AsyncMock(
            return_value={
                "access_token": "new-token",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
            }
        )
    )

    await auth.authorize("the-code")

    assert auth.is_authorized()
    assert auth._access_token == "new-token"
    assert auth._refresh_token == "new-refresh"
    assert auth._expired() is False


async def test_refresh_without_refresh_token_raises():
    from donatex import errors

    auth = OAuthConfidentialAuth("id", "secret", scopes={"donations.read"})
    auth._bind_transport(AsyncMock())

    with pytest.raises(errors.AuthRequiredError):
        await auth.refresh()
