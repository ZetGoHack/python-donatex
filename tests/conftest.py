import pytest


@pytest.fixture
def donation_raw():
    def _make(**overrides) -> dict:
        raw = {
            "id": "d1",
            "username": "u",
            "message": "m",
            "withAIResponse": False,
            "musicLink": None,
            "currency": "RUB",
            "amount": 1.0,
            "amountInRub": 1.0,
            "timestamp": "2026-01-01T00:00:00+00:00",
            "aiResponse": None,
            "aiResponseVoiceFilePath": None,
            "wasShown": True,
            "isTest": False,
            "isPotentiallyUnsafe": False,
            "isFeePaidByUser": False,
            "voiceFilePath": "",
            "paidVoice": "",
        }
        raw.update(overrides)
        return raw

    return _make


@pytest.fixture
def goal_raw():
    return {
        "id": "goal-1",
        "name": "Новый микрофон",
        "currentAmount": 12450.0,
        "goalAmount": 20000.0,
        "currency": "RUB",
        "progressPercent": 62.25,
        "isCompleted": False,
    }


@pytest.fixture
def track_raw():
    return {
        "isPlaying": True,
        "hasTrack": True,
        "widgetConnected": True,
        "isPaused": False,
        "widgetId": "w1",
        "donationId": "d1",
        "musicLink": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }


@pytest.fixture
def track_skip_raw():
    return {
        "skipped": True,
        "hasTrack": True,
        "widgetId": "w1",
        "donationId": "d1",
        "musicLink": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "markedAsPlayed": True,
    }


@pytest.fixture
def top_donator_raw():
    return {
        "rank": 1,
        "username": "NeDrugLegenda1377",
        "totalAmountInRub": 15400.0,
        "currency": "RUB",
        "lastDonationDate": "2025-12-15T08:57:24Z",
    }


@pytest.fixture
def character_raw():
    return {
        "id": "char-1",
        "name": "Капитан",
        "prompt": None,
        "systemPrompt": "Отвечай по-русски.",
        "avatarUrl": None,
        "color": "#B69CFF",
    }


@pytest.fixture
def subscription_raw():
    return {
        "id": "sub-1",
        "url": "https://example.com/webhooks/donations",
        "clientId": "my-app-id",
        "eventType": "DonationCreated",
        "isActive": True,
        "failureCount": 0,
    }
