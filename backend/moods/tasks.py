from __future__ import annotations

from celery import shared_task
from django.conf import settings

from moods.models import Country
from moods.providers import (
    PublicRedditProvider,
    RedditProvider,
    ScrapeXProvider,
    XProvider,
)
from moods.services import refresh_all, refresh_country


@shared_task
def refresh_country_mood(country_code: str, window_minutes: int) -> None:
    country = Country.objects.get(code=country_code)
    refresh_country(country, window_minutes=window_minutes)


@shared_task
def refresh_all_moods() -> int:
    snapshots = refresh_all()
    return len(snapshots)


@shared_task
def refresh_all_moods_x() -> int:
    provider = XProvider(settings.X_BEARER_TOKEN) if settings.X_BEARER_TOKEN else ScrapeXProvider()
    snapshots = refresh_all(provider=provider)
    return len(snapshots)


@shared_task
def refresh_all_moods_reddit() -> int:
    provider = (
        RedditProvider(settings.REDDIT_CLIENT_ID, settings.REDDIT_CLIENT_SECRET, settings.REDDIT_USER_AGENT)
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET
        else PublicRedditProvider(settings.REDDIT_USER_AGENT)
    )
    snapshots = refresh_all(provider=provider)
    return len(snapshots)
