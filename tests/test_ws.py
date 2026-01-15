import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import override_settings
from django.utils import timezone

from moodclock.asgi import application
from moods.models import Country, MoodSnapshot


@pytest.mark.asyncio
@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
async def test_websocket_smoke(db):
    country = await sync_to_async(Country.objects.create)(
        code="US",
        name="United States",
        has_trends=True,
        woeid=23424977,
        centroid_lat=39.8,
        centroid_lng=-98.5,
    )

    communicator = WebsocketCommunicator(application, "/ws/moods/")
    connected, _ = await communicator.connect()
    assert connected

    await sync_to_async(MoodSnapshot.objects.create)(
        country=country,
        window_start=timezone.now(),
        window_minutes=15,
        mood_score=0.1,
        energy=0.2,
        emoji="😐",
        label="Neutral",
        confidence="LOW",
        n_items=5,
        emotion_probs={"joy": 0.2, "neutral": 0.2, "anger": 0.2, "sadness": 0.2, "fear": 0.2},
    )

    message = await communicator.receive_json_from()
    assert message["country"] == "US"
    await communicator.disconnect()
