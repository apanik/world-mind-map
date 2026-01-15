from django.contrib import admin
from django.db.models import Prefetch

from moods.models import Country, MoodDriver, MoodSnapshot, TextSample


class MoodDriverInline(admin.TabularInline):
    model = MoodDriver
    extra = 0
    readonly_fields = ("topic", "weight", "sentiment_avg", "emotion_probs", "n_items", "rank")


class TextSampleInline(admin.TabularInline):
    model = TextSample
    extra = 0
    readonly_fields = ("source", "text", "created_at")


@admin.register(MoodSnapshot)
class MoodSnapshotAdmin(admin.ModelAdmin):
    list_display = ("country", "window_start", "window_minutes", "emoji", "mood_score", "energy", "confidence", "n_items")
    list_filter = ("confidence", "window_minutes")
    inlines = [MoodDriverInline, TextSampleInline]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "has_trends", "latest_refresh", "latest_items")
    search_fields = ("code", "name")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            Prefetch("snapshots", queryset=MoodSnapshot.objects.order_by("-window_start"))
        )

    def latest_refresh(self, obj):
        latest = obj.snapshots.first()
        return latest.window_start if latest else None

    def latest_items(self, obj):
        latest = obj.snapshots.first()
        return latest.n_items if latest else 0


admin.site.register(MoodDriver)
admin.site.register(TextSample)
