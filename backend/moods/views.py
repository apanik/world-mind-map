from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from moods.models import Country, MoodSnapshot


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")


def country_panel(request: HttpRequest, code: str) -> HttpResponse:
    country = get_object_or_404(Country, code=code.upper())
    snapshot = country.snapshots.first()
    drivers = snapshot.drivers.all() if snapshot else []
    samples = snapshot.samples.all() if snapshot else []
    context = {
        "country": country,
        "snapshot": snapshot,
        "drivers": drivers,
        "samples": samples,
    }
    return render(request, "partials/country_panel.html", context)


def healthz(request: HttpRequest) -> JsonResponse:
    try:
        db_ok = Country.objects.exists()
    except Exception:
        db_ok = False
    try:
        from django.core.cache import cache

        cache.set("healthz", timezone.now(), 10)
        redis_ok = cache.get("healthz") is not None
    except Exception:
        redis_ok = False
    return JsonResponse({"db": db_ok, "redis": redis_ok})
