from __future__ import annotations

from celery import shared_task

from moods.models import Country
from moods.services import refresh_all, refresh_country


@shared_task
def refresh_country_mood(country_code: str, window_minutes: int) -> None:
    country = Country.objects.get(code=country_code)
    refresh_country(country, window_minutes=window_minutes)


@shared_task
def refresh_all_moods() -> int:
    snapshots = refresh_all()
    return len(snapshots)
