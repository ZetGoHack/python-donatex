import pytest

from donatex import errors
from donatex.utils import validate_scopes


def test_validate_scopes_accepts_known_scopes():
    scopes = {"donations.read", "openid"}

    result = validate_scopes(scopes)

    assert result is True


def test_validate_scopes_accepts_empty_set():
    assert validate_scopes(set()) is True


def test_validate_scopes_rejects_unknown_scope():
    scopes = {"donations.read", "not_a_real_scope"}

    with pytest.raises(errors.InvalidScopeError):
        validate_scopes(scopes)


def test_validate_scopes_error_message_lists_bad_scopes():
    with pytest.raises(errors.InvalidScopeError) as exc_info:
        validate_scopes({"donations.read", "bad_one", "bad_two"})

    message = str(exc_info.value)
    assert "bad_one" in message
    assert "bad_two" in message
