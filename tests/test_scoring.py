from moods.scoring import aggregate_scores, score_text, select_emoji_label


def test_score_text_deterministic():
    text = "Happy news! Great win!"
    first = score_text(text)
    second = score_text(text)
    assert first.polarity == second.polarity
    assert first.energy == second.energy
    assert first.emotions == second.emotions


def test_select_emoji_label():
    emoji, label = select_emoji_label({"joy": 0.9, "neutral": 0.1, "anger": 0, "sadness": 0, "fear": 0})
    assert emoji == "😀"
    assert label == "Joyful"


def test_aggregate_scores():
    items = [score_text("good"), score_text("bad")]
    aggregated = aggregate_scores(items)
    assert -1 <= aggregated.mood_score <= 1
    assert 0 <= aggregated.energy <= 1
    assert abs(sum(aggregated.emotions.values()) - 1.0) < 1e-6
