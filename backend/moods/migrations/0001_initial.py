from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Country",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=2, unique=True)),
                ("name", models.CharField(max_length=128)),
                ("has_trends", models.BooleanField(default=False)),
                ("woeid", models.IntegerField(blank=True, null=True)),
                ("centroid_lat", models.FloatField()),
                ("centroid_lng", models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name="MoodSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("window_start", models.DateTimeField()),
                ("window_minutes", models.PositiveIntegerField()),
                ("mood_score", models.FloatField()),
                ("energy", models.FloatField()),
                ("emoji", models.CharField(max_length=4)),
                ("label", models.CharField(max_length=64)),
                (
                    "confidence",
                    models.CharField(
                        choices=[("LOW", "Low"), ("MED", "Medium"), ("HIGH", "High")],
                        max_length=4,
                    ),
                ),
                ("n_items", models.PositiveIntegerField()),
                ("emotion_probs", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "country",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="snapshots", to="moods.country"),
                ),
            ],
            options={
                "ordering": ["-window_start"],
                "unique_together": {("country", "window_start", "window_minutes")},
            },
        ),
        migrations.CreateModel(
            name="MoodDriver",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("topic", models.CharField(max_length=128)),
                ("weight", models.FloatField()),
                ("sentiment_avg", models.FloatField()),
                ("emotion_probs", models.JSONField(default=dict)),
                ("n_items", models.PositiveIntegerField()),
                ("rank", models.PositiveIntegerField()),
                (
                    "snapshot",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="drivers", to="moods.moodsnapshot"),
                ),
            ],
            options={"ordering": ["rank"]},
        ),
        migrations.CreateModel(
            name="TextSample",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "source",
                    models.CharField(choices=[("x", "X"), ("reddit", "Reddit")], max_length=10),
                ),
                ("text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "snapshot",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="samples", to="moods.moodsnapshot"),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
