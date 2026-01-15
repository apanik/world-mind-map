from __future__ import annotations

import datetime
import logging
from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from moods.models import Country, MoodDriver, MoodSnapshot, TextSample
from moods.providers import TrendProvider, TrendTopic, provider_from_settings
from moods.scoring import aggregate_scores, confidence_from_samples, score_text, select_emoji_label, variance

logger = logging.getLogger(__name__)


def _window_start(window_minutes: int) -> datetime.datetime:
    now = timezone.now()
    minutes = (now.minute // window_minutes) * window_minutes
    return now.replace(minute=minutes, second=0, microsecond=0)


def refresh_country(country: Country, provider: TrendProvider | None = None, window_minutes: int | None = None) -> MoodSnapshot | None:
    provider = provider or provider_from_settings()
    window_minutes = window_minutes or settings.WINDOW_MINUTES
    window_start = _window_start(window_minutes)

    try:
        trends = provider.get_trends(country.code)
    except Exception as exc:
        logger.exception("Provider get_trends failed: %s", exc)
        return None

    if not trends:
        trends = [TrendTopic(topic="general mood", weight=1.0)]

    scored_items = []
    driver_map: dict[str, list[float]] = defaultdict(list)
    driver_emotions: dict[str, list[dict[str, float]]] = defaultdict(list)
    text_samples: list[tuple[str, str]] = []

    for trend in trends:
        try:
            posts = provider.sample_posts(country.code, trend.topic, limit=20)
        except Exception as exc:
            logger.exception("Provider sample_posts failed: %s", exc)
            posts = []
        for post in posts:
            scored = score_text(post)
            scored_items.append(scored)
            driver_map[trend.topic].append(scored.polarity)
            driver_emotions[trend.topic].append(scored.emotions)
            if len(text_samples) < 5:
                source = "x" if settings.PROVIDER in {"x", "composite"} else "reddit"
                text_samples.append((source, post[:240]))

    aggregated = aggregate_scores(scored_items)
    emoji, label = select_emoji_label(aggregated.emotions)
    var = variance([item.polarity for item in scored_items])
    confidence = confidence_from_samples(len(scored_items), var)
    if not country.has_trends and confidence == "HIGH":
        confidence = "MED"
    if not country.has_trends and confidence == "MED":
        confidence = "LOW"

    with transaction.atomic():
        snapshot, _ = MoodSnapshot.objects.update_or_create(
            country=country,
            window_start=window_start,
            window_minutes=window_minutes,
            defaults={
                "mood_score": aggregated.mood_score,
                "energy": aggregated.energy,
                "emoji": emoji,
                "label": label,
                "confidence": confidence,
                "n_items": len(scored_items),
                "emotion_probs": aggregated.emotions,
            },
        )
        snapshot.drivers.all().delete()
        snapshot.samples.all().delete()

        driver_items = sorted(driver_map.items(), key=lambda item: len(item[1]), reverse=True)[:8]
        for rank, (topic, polarities) in enumerate(driver_items, start=1):
            emotion_avg = _average_emotions(driver_emotions[topic])
            MoodDriver.objects.create(
                snapshot=snapshot,
                topic=topic,
                weight=len(polarities),
                sentiment_avg=sum(polarities) / max(len(polarities), 1),
                emotion_probs=emotion_avg,
                n_items=len(polarities),
                rank=rank,
            )

        for source, text in text_samples:
            TextSample.objects.create(snapshot=snapshot, source=source, text=text)

    return snapshot


def _average_emotions(emotions_list: list[dict[str, float]]) -> dict[str, float]:
    if not emotions_list:
        return {"joy": 0.2, "neutral": 0.2, "anger": 0.2, "sadness": 0.2, "fear": 0.2}
    totals: dict[str, float] = defaultdict(float)
    for emotions in emotions_list:
        for key, value in emotions.items():
            totals[key] += value
    total = sum(totals.values()) or 1.0
    return {key: value / total for key, value in totals.items()}


def refresh_all(provider: TrendProvider | None = None, window_minutes: int | None = None) -> list[MoodSnapshot]:
    provider = provider or provider_from_settings()
    window_minutes = window_minutes or settings.WINDOW_MINUTES
    snapshots = []
    for country in Country.objects.filter(code__in=settings.TOP_COUNTRIES):
        snapshot = refresh_country(country, provider=provider, window_minutes=window_minutes)
        if snapshot:
            snapshots.append(snapshot)
    return snapshots
