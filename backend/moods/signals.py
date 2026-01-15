from __future__ import annotations

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from moods.models import MoodSnapshot


@receiver(post_save, sender=MoodSnapshot)
def broadcast_mood_update(sender, instance: MoodSnapshot, created: bool, **kwargs):
    channel_layer = get_channel_layer()
    payload = {
        "country": instance.country.code,
        "emoji": instance.emoji,
        "mood_score": instance.mood_score,
        "energy": instance.energy,
    }
    async_to_sync(channel_layer.group_send)(
        "mood_updates",
        {
            "type": "mood.update",
            "payload": payload,
        },
    )
