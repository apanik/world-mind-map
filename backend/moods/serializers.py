from rest_framework import serializers

from moods.models import Country, MoodDriver, MoodSnapshot, TextSample


class MoodSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoodSnapshot
        fields = [
            "window_start",
            "window_minutes",
            "mood_score",
            "energy",
            "emoji",
            "label",
            "confidence",
            "n_items",
            "emotion_probs",
        ]


class CountryListSerializer(serializers.ModelSerializer):
    latest_snapshot = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = ["code", "name", "centroid_lat", "centroid_lng", "latest_snapshot"]

    def get_latest_snapshot(self, obj):
        snapshot = obj.snapshots.first()
        if not snapshot:
            return None
        return MoodSnapshotSerializer(snapshot).data


class MoodDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoodDriver
        fields = ["topic", "weight", "sentiment_avg", "emotion_probs", "n_items", "rank"]


class TextSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextSample
        fields = ["source", "text", "created_at"]


class CountryDetailSerializer(serializers.ModelSerializer):
    latest_snapshot = serializers.SerializerMethodField()
    drivers = serializers.SerializerMethodField()
    samples = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = [
            "code",
            "name",
            "centroid_lat",
            "centroid_lng",
            "latest_snapshot",
            "drivers",
            "samples",
        ]

    def get_latest_snapshot(self, obj):
        snapshot = obj.snapshots.first()
        if not snapshot:
            return None
        return MoodSnapshotSerializer(snapshot).data

    def get_drivers(self, obj):
        snapshot = obj.snapshots.first()
        if not snapshot:
            return []
        return MoodDriverSerializer(snapshot.drivers.all(), many=True).data

    def get_samples(self, obj):
        snapshot = obj.snapshots.first()
        if not snapshot:
            return []
        return TextSampleSerializer(snapshot.samples.all(), many=True).data
