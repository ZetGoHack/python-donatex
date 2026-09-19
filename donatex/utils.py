import typing

from . import errors
from . import types


def validate_scopes(scopes: set) -> bool:
    """Сверяет указанные scopes с актуальным списком.

    Возвращает True при успешной валидации

    При ошибке валидации возвращает ``InvalidScopeError`` с неверными scopes"""
    valid_scopes = set(typing.get_args(types.TokenScope))
    invalid_scopes = scopes - valid_scopes

    if invalid_scopes:
        raise errors.InvalidScopeError(
            f"Указаны неверные scopes: {', '.join(sorted(invalid_scopes))}"
        )

    return True
