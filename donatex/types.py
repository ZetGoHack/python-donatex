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

    def __post_init__(self):
        if bool(self.start_date.tzinfo) != bool(self.end_date.tzinfo):
            raise ValueError(
                "start_date и end_date должны быть одновременно "
                "либо aware, либо naive datetime"
            )
        if self.start_date >= self.end_date:
            raise ValueError("start_date должен не быть позже end_date")

    @staticmethod
    def fmt(dt: datetime.datetime) -> str:
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.timezone.utc)
        return dt.strftime("%Y-%m-%d")

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


@dataclass
class Donation: # TODO: Переработка атрибутов
    id: str
    username: str
    message: str
    with_AI_response: bool
    music_link: str | None
    currency: str
    amount: float
    amount_in_rub: float
    timestamp: datetime.datetime
    ai_response: str | None
    ai_response_voice_file_path: str | None
    was_shown: bool
    is_test: bool
    is_potentially_unsafe: bool
    is_fee_paid_by_user: bool
    voice_file_path: str
    paid_voice: str

    @staticmethod
    def _parse(raw: dict) -> Donation:
        return Donation(
            id=raw["id"],
            username=raw["username"],
            message=raw["message"],
            with_AI_response=raw["withAIResponse"],
            music_link=raw.get("musicLink", None),
            currency=raw["currency"],
            amount=raw["amount"],
            amount_in_rub=raw["amountInRub"],
            timestamp=datetime.datetime.fromisoformat(raw["timestamp"]),
            ai_response=raw["aiResponse"],
            ai_response_voice_file_path=raw["aiResponseVoiceFilePath"],
            was_shown=raw["wasShown"],
            is_test=raw["isTest"],
            is_potentially_unsafe=raw["isPotentiallyUnsafe"],
            is_fee_paid_by_user=raw["isFeePaidByUser"],
            voice_file_path=raw["voiceFilePath"],
            paid_voice=raw["paidVoice"],
        )
