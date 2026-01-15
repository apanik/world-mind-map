from django.conf import settings
from django.contrib import admin, messages
from django.db.models import Prefetch

from moods.models import Country, MoodDriver, MoodSnapshot, TextSample
from moods.tasks import (
    refresh_all_moods,
    refresh_all_moods_reddit,
    refresh_all_moods_x,
    refresh_country_mood,
)


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
    actions = (
        "queue_refresh_selected",
        "queue_refresh_all_composite",
        "queue_refresh_all_x",
        "queue_refresh_all_reddit",
    )

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

    @admin.action(description="Queue refresh for selected countries")
    def queue_refresh_selected(self, request, queryset):
        for country in queryset:
            refresh_country_mood.delay(country.code, settings.WINDOW_MINUTES)
        self.message_user(
            request,
            f"Queued refresh for {queryset.count()} countries.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Queue composite refresh (all countries)")
    def queue_refresh_all_composite(self, request, queryset):
        refresh_all_moods.delay()
        self.message_user(request, "Queued composite refresh for all countries.", level=messages.SUCCESS)

    @admin.action(description="Queue X-only refresh (all countries)")
    def queue_refresh_all_x(self, request, queryset):
        refresh_all_moods_x.delay()
        self.message_user(request, "Queued X refresh for all countries.", level=messages.SUCCESS)

    @admin.action(description="Queue Reddit-only refresh (all countries)")
    def queue_refresh_all_reddit(self, request, queryset):
        refresh_all_moods_reddit.delay()
        self.message_user(request, "Queued Reddit refresh for all countries.", level=messages.SUCCESS)


admin.site.register(MoodDriver)
admin.site.register(TextSample)
