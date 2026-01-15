from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable

POSITIVE_WORDS = {"good", "great", "love", "happy", "joy", "win", "relief", "hope", "peace"}
NEGATIVE_WORDS = {"bad", "sad", "angry", "fear", "loss", "hate", "crisis", "panic", "pain"}

EMOTION_KEYWORDS = {
    "joy": {"happy", "joy", "delight", "celebrate", "win"},
    "neutral": {"update", "report", "statement", "analysis", "news"},
    "anger": {"angry", "furious", "rage", "protest"},
    "sadness": {"sad", "loss", "grief", "mourning"},
    "fear": {"fear", "panic", "worry", "alert"},
}


@dataclass
class ScoredItem:
    polarity: float
    energy: float
    emotions: dict[str, float]


@dataclass
class AggregatedScore:
    mood_score: float
    energy: float
    emotions: dict[str, float]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def score_text(text: str) -> ScoredItem:
    tokens = _tokenize(text)
    pos = sum(1 for token in tokens if token in POSITIVE_WORDS)
    neg = sum(1 for token in tokens if token in NEGATIVE_WORDS)
    total = max(pos + neg, 1)
    polarity = max(min((pos - neg) / total, 1.0), -1.0)

    exclamations = text.count("!")
    question = text.count("?")
    caps = sum(1 for ch in text if ch.isupper())
    emoji_density = sum(1 for ch in text if ch in "😀😐😡😢😨")
    energy = min((exclamations + question + caps / 10 + emoji_density) / 5, 1.0)

    emotions: dict[str, float] = {key: 0.0 for key in EMOTION_KEYWORDS}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        emotions[emotion] = sum(1 for token in tokens if token in keywords)

    total_emotions = sum(emotions.values()) or 1.0
    normalized = {key: value / total_emotions for key, value in emotions.items()}

    return ScoredItem(polarity=polarity, energy=energy, emotions=normalized)


def aggregate_scores(items: Iterable[ScoredItem]) -> AggregatedScore:
    items_list = list(items)
    if not items_list:
        return AggregatedScore(mood_score=0.0, energy=0.0, emotions={key: 0.2 for key in EMOTION_KEYWORDS})

    mood_score = sum(item.polarity for item in items_list) / len(items_list)
    energy = sum(item.energy for item in items_list) / len(items_list)

    emotions = {key: 0.0 for key in EMOTION_KEYWORDS}
    for item in items_list:
        for key, value in item.emotions.items():
            emotions[key] += value
    total = sum(emotions.values()) or 1.0
    emotions = {key: value / total for key, value in emotions.items()}

    return AggregatedScore(mood_score=max(min(mood_score, 1.0), -1.0), energy=energy, emotions=emotions)


def select_emoji_label(emotions: dict[str, float]) -> tuple[str, str]:
    dominant = max(emotions.items(), key=lambda item: item[1])[0]
    mapping = {
        "joy": ("😀", "Joyful"),
        "anger": ("😡", "Angry"),
        "sadness": ("😢", "Sad"),
        "fear": ("😨", "Tense"),
    }
    return mapping.get(dominant, ("😐", "Neutral"))


def confidence_from_samples(n_items: int, variance: float) -> str:
    if n_items >= 1000 and variance < 0.2:
        return "HIGH"
    if 200 <= n_items < 1000:
        return "MED"
    return "LOW"


def variance(values: Iterable[float]) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    mean = sum(values_list) / len(values_list)
    return sum((value - mean) ** 2 for value in values_list) / len(values_list)
