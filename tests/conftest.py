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
