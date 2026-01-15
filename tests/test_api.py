import pytest
from django.urls import reverse
from django.utils import timezone

from moods.models import Country, MoodSnapshot


@pytest.fixture
def country(db):
    return Country.objects.create(
        code="US",
        name="United States",
        has_trends=True,
        woeid=23424977,
        centroid_lat=39.8,
        centroid_lng=-98.5,
    )


@pytest.fixture
def snapshot(country):
    return MoodSnapshot.objects.create(
        country=country,
        window_start=timezone.now(),
        window_minutes=15,
        mood_score=0.2,
        energy=0.3,
        emoji="😀",
        label="Joyful",
        confidence="LOW",
        n_items=10,
        emotion_probs={"joy": 0.5, "neutral": 0.2, "anger": 0.1, "sadness": 0.1, "fear": 0.1},
    )


@pytest.mark.django_db
def test_country_list_api(client, snapshot):
    response = client.get("/api/countries/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["code"] == "US"
    assert "latest_snapshot" in data[0]


@pytest.mark.django_db
def test_country_detail_api(client, snapshot):
    response = client.get("/api/countries/US/")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "US"
    assert data["latest_snapshot"]["emoji"] == "😀"


@pytest.mark.django_db
def test_latest_snapshots_api(client, snapshot):
    response = client.get("/api/snapshots/latest/?minutes=15")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.django_db
def test_snapshot_history_api(client, snapshot):
    response = client.get("/api/snapshots/US/history/?hours=24")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
