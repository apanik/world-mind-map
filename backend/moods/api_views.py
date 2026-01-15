from __future__ import annotations

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from moods.models import Country, MoodSnapshot
from moods.serializers import CountryDetailSerializer, CountryListSerializer, MoodSnapshotSerializer


class CountryListView(APIView):
    def get(self, request):
        countries = Country.objects.all().prefetch_related("snapshots")
        return Response(CountryListSerializer(countries, many=True).data)


class CountryDetailView(APIView):
    def get(self, request, code: str):
        country = Country.objects.prefetch_related("snapshots__drivers", "snapshots__samples").get(code=code.upper())
        return Response(CountryDetailSerializer(country).data)


class LatestSnapshotsView(APIView):
    def get(self, request):
        minutes = int(request.query_params.get("minutes", "15"))
        cutoff = timezone.now() - timezone.timedelta(minutes=minutes)
        snapshots = MoodSnapshot.objects.filter(window_start__gte=cutoff, window_minutes=minutes)
        return Response(MoodSnapshotSerializer(snapshots, many=True).data)


class SnapshotHistoryView(APIView):
    def get(self, request, code: str):
        hours = int(request.query_params.get("hours", "24"))
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        snapshots = MoodSnapshot.objects.filter(country__code=code.upper(), window_start__gte=cutoff)
        return Response(MoodSnapshotSerializer(snapshots, many=True).data)
