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

EventTypeScope = typing.Literal["DonationCreated"]


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


@dataclass(kw_only=True)
class DonateXObject:
    raw: dict = field(repr=False, compare=False)
    _client: "Client | None" = field(default=None, repr=False, compare=False)

    def _bind(self, client: "Client") -> typing.Self:
        self._client = client
        return self

    def _require_client(self) -> "Client":
        if self._client is None:
            raise RuntimeError(
                f"{self.__class__.__name__} не привязан к Client, "
                "действие недоступно"
            )
        return self._client


@dataclass
class User(DonateXObject):
    id: str
    username: str
    avatar_url: str

    @classmethod
    def _parse(cls, raw: dict, client: "Client | None" = None) -> "User":
        return cls(
            id=raw["id"],
            username=raw["username"],
            avatar_url=raw["avatarUrl"],
            raw=raw,
            _client=client,
        )


@dataclass
class DonationAmount:
    value: float
    value_in_rub: float
    currency: CurrencyScope


@dataclass
class DonationVoice:
    file_path: str
    paid_voice: str | None
    """Название платного голоса. ``None`` - использовался стандартный голос"""


@dataclass
class VoiceMessage:
    """Голосовое сообщение, записанное донатером"""

    file_path: str
    duration: datetime.timedelta | None

    @classmethod
    def _parse(cls, raw: dict) -> "VoiceMessage | None":
        if not raw.get("voiceMessagePath"):
            return None
        duration_ms = raw.get("voiceMessageDurationMs")
        return cls(
            file_path=raw["voiceMessagePath"],
            duration=(
                datetime.timedelta(milliseconds=duration_ms)
                if duration_ms is not None
                else None
            ),
        )


@dataclass
class AIResponse:
    enabled: bool
    text: str | None
    voice_file_path: str | None

    @property
    def is_pending(self) -> bool:
        """Ответ ИИ включён, но ещё не готов"""
        return self.enabled and self.text is None


@dataclass
class DonationFlags:
    was_shown: bool | None
    is_test: bool
    is_potentially_unsafe: bool
    is_fee_paid_by_user: bool


@dataclass
class Donation(DonateXObject):
    id: str
    username: str
    message: str
    music_link: str | None
    timestamp: datetime.datetime
    amount: DonationAmount
    voice: DonationVoice
    voice_message: VoiceMessage | None
    ai: AIResponse
    flags: DonationFlags

    @classmethod
    def _parse(cls, raw: dict, client: "Client | None" = None) -> "Donation":
        return cls(
            id=raw["id"],
            username=raw["username"],
            message=raw["message"],
            music_link=raw.get("musicLink") or None,
            timestamp=datetime.datetime.fromisoformat(raw["timestamp"]),
            amount=DonationAmount(
                value=raw["amount"],
                value_in_rub=raw["amountInRub"],
                currency=raw["currency"],
            ),
            voice=DonationVoice(
                file_path=raw["voiceFilePath"],
                paid_voice=raw.get("paidVoice") or None,
            ),
            voice_message=VoiceMessage._parse(raw),
            ai=AIResponse(
                enabled=raw["withAIResponse"],
                text=raw["aiResponse"],
                voice_file_path=raw["aiResponseVoiceFilePath"],
            ),
            flags=DonationFlags(
                was_shown=raw.get("wasShown"),
                is_test=raw["isTest"],
                is_potentially_unsafe=raw["isPotentiallyUnsafe"],
                is_fee_paid_by_user=raw["isFeePaidByUser"],
            ),
            raw=raw,
            _client=client,
        )

    # region Shortcuts

    async def skip(self):
        """Пропускает конкретный донат по его ID — независимо от того, является ли он текущим в очереди. Помечает донат как показанный."""
        client = self._require_client()
        await client.skip_donation(self.id)
        self.flags.was_shown = True

    # endregion Shortcuts


@dataclass
class TrackState(DonateXObject):
    is_playing: bool
    has_track: bool
    widget_connected: bool
    is_paused: bool
    widget_id: str | None = None
    donation_id: str | None = None
    music_link: str | None = None

    @classmethod
    def _parse(cls, raw: dict, client: "Client | None" = None) -> "TrackState":
        return cls(
            is_playing=raw["isPlaying"],
            has_track=raw["hasTrack"],
            widget_connected=raw["widgetConnected"],
            is_paused=raw["isPaused"],
            widget_id=raw.get("widgetId"),
            donation_id=raw.get("donationId"),
            music_link=raw.get("musicLink") or None,
            raw=raw,
            _client=client,
        )


@dataclass
class GoalState(DonateXObject):
    id: str
    name: str
    current_amount: float
    goal_amount: float
    currency: typing.Literal["RUB"]
    progress_percent: float
    is_completed: bool

    @classmethod
    def _parse(cls, raw: dict, client: "Client | None" = None) -> "GoalState":
        return cls(
            id=raw["id"],
            name=raw["name"],
            current_amount=raw["currentAmount"],
            goal_amount=raw["goalAmount"],
            currency=raw["currency"],
            progress_percent=raw["progressPercent"],
            is_completed=raw["isCompleted"],
            raw=raw,
            _client=client,
        )


@dataclass
class TrackSkipResult(DonateXObject):
    skipped: bool
    has_track: bool
    widget_id: str | None = None
    donation_id: str | None = None
    music_link: str | None = None
    marked_as_played: bool | None = None

    @classmethod
    def _parse(cls, raw: dict, client: "Client | None" = None) -> "TrackSkipResult":
        return cls(
            skipped=raw["skipped"],
            has_track=raw["hasTrack"],
            widget_id=raw.get("widgetId"),
            donation_id=raw.get("donationId"),
            music_link=raw.get("musicLink") or None,
            marked_as_played=raw.get("markedAsPlayed"),
            raw=raw,
            _client=client,
        )


@dataclass
class DonationSkipResult(DonateXObject):
    skipped: bool
    skipped_donation_id: str | None = None

    @classmethod
    def _parse(cls, raw: dict, client: "Client | None" = None) -> "DonationSkipResult":
        return cls(
            skipped=raw["skipped"],
            skipped_donation_id=raw.get("skippedDonationId"),
            raw=raw,
            _client=client,
        )


@dataclass
class TopDonator(DonateXObject):
    rank: int
    username: str
    total_amount_in_rub: float
    currency: typing.Literal["RUB"]
    last_donation_date: datetime.datetime

    @classmethod
    def _parse(cls, raw: dict, client: "Client | None" = None) -> "TopDonator":
        return cls(
            rank=raw["rank"],
            username=raw["username"],
            total_amount_in_rub=raw["totalAmountInRub"],
            currency=raw["currency"],
            last_donation_date=datetime.datetime.fromisoformat(raw["lastDonationDate"]),
            raw=raw,
            _client=client,
        )


@dataclass
class AICharacter(DonateXObject):
    id: str
    name: str
    prompt: str | None
    system_prompt: str | None
    avatar_url: str | None
    color: str

    @classmethod
    def _parse(cls, raw: dict, client: "Client | None" = None) -> "AICharacter":
        return cls(
            id=raw["id"],
            name=raw["name"],
            prompt=raw["prompt"],
            system_prompt=raw["systemPrompt"],
            avatar_url=raw["avatarUrl"],
            color=raw["color"],
            raw=raw,
            _client=client,
        )


@dataclass
class WebhookSubscription(DonateXObject):
    id: str
    url: str
    event_type: EventTypeScope
    is_active: bool
    failure_count: int
    client_id: str | None

    @classmethod
    def _parse(cls, raw: dict, client: "Client | None" = None) -> "WebhookSubscription":
        return cls(
            id=raw["id"],
            url=raw["url"],
            event_type=raw["eventType"],
            is_active=raw["isActive"],
            failure_count=raw["failureCount"],
            client_id=raw["clientId"],
            raw=raw,
            _client=client,
        )

    # region Shortcuts

    async def delete(self):
        """Мягкое удаление подписки. Доставки прекращаются, подписку можно снова активировать"""
        client = self._require_client()
        await client.delete_subscription(self.id)
        self.is_active = False

    async def activate(self):
        """Повторно включает ранее отключенную подписку и сбрасывает счетчик ошибок"""
        client = self._require_client()
        was_inactive = not self.is_active
        await client.activate_subscription(self.id)
        self.is_active = True
        if was_inactive:
            self.failure_count = 0

    # endregion Shortcuts


class AuthorizeUrl(typing.NamedTuple):
    url: str
    code_verifier: str


class SubscriptionCreated(typing.NamedTuple):
    subscription: WebhookSubscription
    secret: str
