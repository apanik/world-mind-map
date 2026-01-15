import json
from pathlib import Path

from django.core.management.base import BaseCommand

from moods.models import Country
from moods.services import refresh_country


class Command(BaseCommand):
    help = "Seed countries and initial mock snapshots"

    def handle(self, *args, **options):
        data_path = Path(__file__).resolve().parent.parent.parent / "data" / "countries.json"
        with data_path.open() as handle:
            countries = json.load(handle)

        for entry in countries:
            country, _ = Country.objects.update_or_create(
                code=entry["code"],
                defaults={
                    "name": entry["name"],
                    "has_trends": entry.get("has_trends", False),
                    "woeid": entry.get("woeid"),
                    "centroid_lat": entry["centroid_lat"],
                    "centroid_lng": entry["centroid_lng"],
                },
            )
            refresh_country(country)

        self.stdout.write(self.style.SUCCESS("Seeded countries and snapshots."))
