import datetime
import typing

from dataclasses import dataclass

TokenScope = typing.Literal[
    "donations.read",       # Чтение истории донатов, топа донатеров и активной цели авторизованного стримера.
    "donations.write",      # Отправка тестовых донатов на свой канал через /v1/test-donation.
    "user.read",            # Доступ к данным профиля стримера через /v1/user/me и своим ИИ-персонажам через /v1/ai/characters
    "donations.subscribe",  # Управление подписками на вебхуки и получение событий через публичный SignalR-хаб.
    "offline_access",       # Запрос refresh_token (PKCE + consent).
    "openid",               # OIDC идентификатор пользователя.
    "profile",              # Имя пользователя и аватарка.
]

PeriodScope = typing.Literal[
    "Day",
    "Week",
    "Month",
    "AllTime",
    "CurrentStream",
    "Last24Hours",
    "Last7Days",
    "Last30Days",
    "CurrentYear",
    "Last365Days",
]

SortScope = typing.Literal[
    "NewestFirst",
    "OldestFirst",
]


@dataclass
class CustomPeriod:
    start_date: datetime.datetime
    end_date: datetime.datetime

    @staticmethod
    def fmt(dt: datetime.datetime) -> str:
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_params(self) -> dict:
        return {
            "startDate": self.fmt(self.start_date),
            "endDate": self.fmt(self.end_date),
        }


@dataclass
class User:
    id: str
    username: str
    avatar_url: str
    raw: dict

    @staticmethod
    def _parse(raw: dict):
        return User(
            id=raw["id"],
            username=raw["username"],
            avatar_url=raw["avatarUrl"],
            raw=raw,
        )