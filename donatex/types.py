import datetime
import typing

from dataclasses import dataclass, field

if typing.TYPE_CHECKING:
    from .client import Client

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

CurrencyScope = typing.Literal[
    "RUB",
    "USD",
    "KZT",
    "EUR",
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
class DonationAmount:
    value: float
    value_in_rub: float
    currency: CurrencyScope


@dataclass
class AIResponse:
    enabled: bool
    text: str | None
    voice_file_path: str | None
    paid_voice: str | None


@dataclass
class DonationFlags:
    was_shown: bool
    is_test: bool
    is_potentially_unsafe: bool
    is_fee_paid_by_user: bool


@dataclass
class Donation:
    id: str
    username: str
    message: str
    music_link: str | None
    voice_file_path: str
    timestamp: datetime.datetime
    amount: DonationAmount
    ai: AIResponse
    flags: DonationFlags
    raw: dict
    _client: "Client | None" = field(default=None, repr=False, compare=False)

    @staticmethod
    def _parse(raw: dict, client: "Client | None" = None) -> "Donation":
        return Donation(
            id=raw["id"],
            username=raw["username"],
            message=raw["message"],
            music_link=raw.get("musicLink", None),
            voice_file_path=raw["voiceFilePath"],
            timestamp=datetime.datetime.fromisoformat(raw["timestamp"]),
            amount=DonationAmount(
                value=raw["amount"],
                value_in_rub=raw["amountInRub"],
                currency=raw["currency"],
            ),
            ai=AIResponse(
                enabled=raw["withAIResponse"],
                text=raw["aiResponse"],
                voice_file_path=raw["aiResponseVoiceFilePath"],
                paid_voice=raw["paidVoice"],
            ),
            flags=DonationFlags(
                was_shown=raw["wasShown"],
                is_test=raw["isTest"],
                is_potentially_unsafe=raw["isPotentiallyUnsafe"],
                is_fee_paid_by_user=raw["isFeePaidByUser"],
            ),
            raw=raw,
            _client=client,
        )

    def _bind(self, client: "Client") -> None:
        self._client = client

    def _require_client(self) -> "Client":
        if self._client is None:
            raise RuntimeError(
                f"{self.__class__.__name__} не привязан к Client, "
                "действие недоступно"
            )
        return self._client

    # region Shortcuts

    async def skip(self):
        """Пропускает конкретный донат по его ID — независимо от того, является ли он текущим в очереди. Помечает донат как показанный."""
        self._require_client()
        # TODO
        raise NotImplementedError("метод для скипа доната пока не реализован...")

    # endregion Shortcuts
