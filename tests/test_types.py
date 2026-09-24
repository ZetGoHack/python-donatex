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
        (
            datetime.datetime(
                2026,
                3,
                5,
                2,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(hours=5)),
            ),
            "2026-03-04",
        ),
        (
            datetime.datetime(
                2026,
                3,
                5,
                23,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(hours=-5)),
            ),
            "2026-03-06",
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
    assert donation._client is None


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
    assert donation.music_link == "https://x/track.mp3"
    assert donation.voice.file_path == "voice.mp3"
    assert donation.timestamp == datetime.datetime(
        2026, 3, 5, 12, 0, tzinfo=datetime.timezone.utc
    )

    assert donation.amount.value == 100.0
    assert donation.amount.value_in_rub == 100.0
    assert donation.amount.currency == "RUB"

    assert donation.ai.enabled is True
    assert donation.ai.text == "hey"
    assert donation.ai.voice_file_path == "v.mp3"
    assert donation.voice.paid_voice == "Канеки"

    assert donation.flags.was_shown is True
    assert donation.flags.is_test is False
    assert donation.flags.is_potentially_unsafe is True
    assert donation.flags.is_fee_paid_by_user is True


def test_donation_parse_binds_client_when_given(donation_raw):
    raw = donation_raw()
    client = object()

    donation = types.Donation._parse(raw, client=client)

    assert donation._client is client


async def test_donation_skip_requires_bound_client(donation_raw):
    donation = types.Donation._parse(donation_raw())

    with pytest.raises(RuntimeError):
        await donation.skip()


async def test_donation_skip_calls_client_and_marks_shown(donation_raw):
    raw = donation_raw(wasShown=False)
    calls = []

    class FakeClient:
        async def skip_donation(self, id):
            calls.append(id)

    donation = types.Donation._parse(raw, client=FakeClient())

    await donation.skip()

    assert calls == [donation.id]
    assert donation.flags.was_shown is True


def test_goal_state_parse_maps_camel_case_fields(goal_raw):
    goal = types.GoalState._parse(goal_raw)

    assert goal.current_amount == 12450.0
    assert goal.goal_amount == 20000.0
    assert goal.progress_percent == 62.25
    assert goal.is_completed is False
    assert goal.raw is goal_raw


def test_track_state_parse_handles_missing_optional_fields():
    raw = {
        "isPlaying": False,
        "hasTrack": False,
        "widgetConnected": False,
        "isPaused": False,
    }

    track = types.TrackState._parse(raw)

    assert track.widget_id is None
    assert track.donation_id is None
    assert track.music_link is None


def test_track_skip_result_parse_maps_fields(track_skip_raw):
    result = types.TrackSkipResult._parse(track_skip_raw)

    assert result.skipped is True
    assert result.donation_id == "d1"
    assert result.marked_as_played is True


def test_donation_skip_result_parse_handles_empty_queue():
    result = types.DonationSkipResult._parse(
        {"skipped": False, "skippedDonationId": None}
    )

    assert result.skipped is False
    assert result.skipped_donation_id is None


def test_top_donator_parse_converts_last_donation_date(top_donator_raw):
    top = types.TopDonator._parse(top_donator_raw)

    assert top.rank == 1
    assert top.total_amount_in_rub == 15400.0
    assert top.last_donation_date == datetime.datetime(
        2025, 12, 15, 8, 57, 24, tzinfo=datetime.timezone.utc
    )


def test_ai_character_parse_keeps_nullable_fields(character_raw):
    character = types.AICharacter._parse(character_raw)

    assert character.prompt is None
    assert character.system_prompt == "Отвечай по-русски."
    assert character.avatar_url is None
    assert character.color == "#B69CFF"


def test_webhook_subscription_parse_maps_fields(subscription_raw):
    sub = types.WebhookSubscription._parse(subscription_raw)

    assert sub.event_type == "DonationCreated"
    assert sub.client_id == "my-app-id"
    assert sub.is_active is True
    assert sub.failure_count == 0


async def test_webhook_subscription_shortcuts_call_client(subscription_raw):
    calls = []

    class FakeClient:
        async def delete_subscription(self, id):
            calls.append(("delete", id))

        async def activate_subscription(self, id):
            calls.append(("activate", id))

    sub = types.WebhookSubscription._parse(
        {**subscription_raw, "failureCount": 3}, client=FakeClient()
    )

    await sub.delete()
    assert sub.is_active is False

    await sub.activate()
    assert sub.is_active is True
    assert sub.failure_count == 0

    assert calls == [("delete", "sub-1"), ("activate", "sub-1")]


async def test_webhook_subscription_activate_without_prior_delete_keeps_failure_count(
    subscription_raw,
):
    class FakeClient:
        async def activate_subscription(self, id):
            pass

    sub = types.WebhookSubscription._parse(
        {**subscription_raw, "failureCount": 1}, client=FakeClient()
    )

    await sub.activate()

    assert sub.is_active is True
    assert sub.failure_count == 1


def test_donation_parse_accepts_signalr_payload_without_optional_fields(donation_raw):
    raw = donation_raw()
    for key in ("wasShown", "paidVoice", "musicLink"):
        del raw[key]

    donation = types.Donation._parse(raw)

    assert donation.flags.was_shown is None
    assert donation.voice.paid_voice is None
    assert donation.music_link is None


@pytest.mark.parametrize(
    "enabled, text, expected",
    [(True, None, True), (True, "ok", False), (False, None, False)],
)
def test_ai_response_is_pending(enabled, text, expected):
    ai = types.AIResponse(enabled=enabled, text=text, voice_file_path=None)

    assert ai.is_pending is expected


def test_donation_parse_normalizes_empty_strings_to_none(donation_raw):
    donation = types.Donation._parse(donation_raw(musicLink="", paidVoice=""))

    assert donation.music_link is None
    assert donation.voice.paid_voice is None


def test_donation_parse_without_voice_message(donation_raw):
    raw = donation_raw(voiceMessagePath=None, voiceMessageDurationMs=None)

    assert types.Donation._parse(raw).voice_message is None
    assert types.Donation._parse(donation_raw()).voice_message is None


def test_donation_parse_with_voice_message(donation_raw):
    raw = donation_raw(voiceMessagePath="https://x/v.ogg", voiceMessageDurationMs=4500)

    message = types.Donation._parse(raw).voice_message

    assert message.file_path == "https://x/v.ogg"
    assert message.duration == datetime.timedelta(seconds=4.5)


def test_donation_parse_real_webhook_payload():
    raw = {
        "id": "f7873ad6-bbd0-41fe-9a03-83ccd55020a5",
        "username": "Кроляя",
        "message": "ласт додеп",
        "withAIResponse": False,
        "musicLink": "",
        "currency": "RUB",
        "amount": 0.67,
        "amountInRub": 0.67,
        "timestamp": "2026-09-24T22:28:59.5259443Z",
        "aiResponse": None,
        "aiResponseVoiceFilePath": None,
        "wasShown": False,
        "isTest": True,
        "isPotentiallyUnsafe": False,
        "isFeePaidByUser": False,
        "voiceFilePath": "https://cdn.donatex.gg/default-donation-voices/f7873ad6-bbd0-41fe-9a03-83ccd55020a5.mp3",
        "paidVoice": "",
        "voiceMessagePath": None,
        "voiceMessageDurationMs": None,
    }

    donation = types.Donation._parse(raw)

    assert donation.timestamp == datetime.datetime(
        2026, 9, 24, 22, 28, 59, 525944, tzinfo=datetime.timezone.utc
    )
    assert donation.music_link is None
    assert donation.voice.paid_voice is None
    assert donation.voice_message is None
    assert donation.flags.is_test is True
