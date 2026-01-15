from __future__ import annotations

from django.db import models


class Country(models.Model):
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=128)
    has_trends = models.BooleanField(default=False)
    woeid = models.IntegerField(null=True, blank=True)
    centroid_lat = models.FloatField()
    centroid_lng = models.FloatField()

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class MoodSnapshot(models.Model):
    class Confidence(models.TextChoices):
        LOW = "LOW", "Low"
        MED = "MED", "Medium"
        HIGH = "HIGH", "High"

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="snapshots")
    window_start = models.DateTimeField()
    window_minutes = models.PositiveIntegerField()
    mood_score = models.FloatField()
    energy = models.FloatField()
    emoji = models.CharField(max_length=4)
    label = models.CharField(max_length=64)
    confidence = models.CharField(max_length=4, choices=Confidence.choices)
    n_items = models.PositiveIntegerField()
    emotion_probs = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("country", "window_start", "window_minutes")
        ordering = ["-window_start"]

    def __str__(self) -> str:
        return f"{self.country.code} {self.window_start.isoformat()}"


class MoodDriver(models.Model):
    snapshot = models.ForeignKey(MoodSnapshot, on_delete=models.CASCADE, related_name="drivers")
    topic = models.CharField(max_length=128)
    weight = models.FloatField()
    sentiment_avg = models.FloatField()
    emotion_probs = models.JSONField(default=dict)
    n_items = models.PositiveIntegerField()
    rank = models.PositiveIntegerField()

    class Meta:
        ordering = ["rank"]

    def __str__(self) -> str:
        return f"{self.snapshot.country.code} {self.topic}"


class TextSample(models.Model):
    class Source(models.TextChoices):
        X = "x", "X"
        REDDIT = "reddit", "Reddit"

    snapshot = models.ForeignKey(MoodSnapshot, on_delete=models.CASCADE, related_name="samples")
    source = models.CharField(max_length=10, choices=Source.choices)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.snapshot.country.code} {self.source}"
