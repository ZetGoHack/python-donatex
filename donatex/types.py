import typing

TokenScope = typing.Literal[
    "donations.read",       # Чтение истории донатов, топа донатеров и активной цели авторизованного стримера.
    "donations.write",      # Отправка тестовых донатов на свой канал через /v1/test-donation.
    "user.read",            # Доступ к данным профиля стримера через /v1/user/me и своим ИИ-персонажам через /v1/ai/characters
    "donations.subscribe",  # Управление подписками на вебхуки и получение событий через публичный SignalR-хаб.
    "offline_access",       # Запрос refresh_token (PKCE + consent).
    "openid",               # OIDC идентификатор пользователя.
    "profile",              # Имя пользователя и аватарка.
]
