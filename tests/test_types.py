import datetime

import pytest

from donatex import types


def test_custom_period_valid_range():
    period = types.CustomPeriod(
        start_date=datetime.datetime(2026, 1, 1),
        end_date=datetime.datetime(2026, 1, 2),
    )
    assert period.to_params() == {
        "startDate": "2026-01-01",
        "endDate": "2026-01-02",
    }


def test_custom_period_rejects_start_after_end():
    with pytest.raises(ValueError):
        types.CustomPeriod(
            start_date=datetime.datetime(2026, 1, 2),
            end_date=datetime.datetime(2026, 1, 1),
        )


def test_custom_period_rejects_equal_dates():
    with pytest.raises(ValueError):
        types.CustomPeriod(
            start_date=datetime.datetime(2026, 1, 1),
            end_date=datetime.datetime(2026, 1, 1),
        )


def test_custom_period_rejects_mixed_aware_and_naive():
    aware = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    naive = datetime.datetime(2026, 1, 2)

    with pytest.raises(ValueError):
        types.CustomPeriod(start_date=aware, end_date=naive)


@pytest.mark.parametrize(
    "dt, expected",
    [
        (datetime.datetime(2026, 3, 5), "2026-03-05"),
        (
            datetime.datetime(2026, 3, 5, 23, 0, tzinfo=datetime.timezone.utc),
            "2026-03-05",
        ),
        (
            datetime.datetime(
                2026,
                3,
                5,
                23,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(hours=5)),
            ),
            "2026-03-05",
        ),
    ],
)
def test_custom_period_fmt_converts_to_utc_date(dt, expected):
    assert types.CustomPeriod.fmt(dt) == expected


def test_user_parse_maps_camel_case_fields():
    raw = {"id": "u1", "username": "zgo", "avatarUrl": "https://x/a.png"}

    user = types.User._parse(raw)

    assert user.id == "u1"
    assert user.username == "zgo"
    assert user.avatar_url == "https://x/a.png"
    assert user.raw is raw


def test_donation_parse_handles_missing_optional_music_link(donation_raw):
    raw = donation_raw()
    del raw["musicLink"]

    donation = types.Donation._parse(raw)

    assert donation.music_link is None


def test_donation_parse_maps_every_field(donation_raw):
    raw = donation_raw(
        id="d1",
        username="zgo",
        message="hi",
        withAIResponse=True,
        musicLink="https://x/track.mp3",
        currency="RUB",
        amount=100.0,
        amountInRub=100.0,
        timestamp="2026-03-05T12:00:00+00:00",
        aiResponse="hey",
        aiResponseVoiceFilePath="v.mp3",
        wasShown=True,
        isTest=False,
        isPotentiallyUnsafe=True,
        isFeePaidByUser=True,
        voiceFilePath="voice.mp3",
        paidVoice="Канеки",
    )

    donation = types.Donation._parse(raw)

    assert donation.id == "d1"
    assert donation.username == "zgo"
    assert donation.message == "hi"
    assert donation.with_AI_response is True
    assert donation.music_link == "https://x/track.mp3"
    assert donation.currency == "RUB"
    assert donation.amount == 100.0
    assert donation.amount_in_rub == 100.0
    assert donation.timestamp == datetime.datetime(
        2026, 3, 5, 12, 0, tzinfo=datetime.timezone.utc
    )
    assert donation.ai_response == "hey"
    assert donation.ai_response_voice_file_path == "v.mp3"
    assert donation.was_shown is True
    assert donation.is_test is False
    assert donation.is_potentially_unsafe is True
    assert donation.is_fee_paid_by_user is True
    assert donation.voice_file_path == "voice.mp3"
    assert donation.paid_voice == "Канеки"
