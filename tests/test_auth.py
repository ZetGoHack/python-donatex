from unittest.mock import AsyncMock

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
    auth._expired = AsyncMock(return_value=False)
    auth.refresh = AsyncMock()

    token = await auth.get_access_token()

    auth._expired.assert_awaited_once()
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
    auth._expired = AsyncMock(return_value=True)
    auth.refresh = AsyncMock()

    await auth.get_access_token()

    auth.refresh.assert_awaited_once()
