# Global Mood Clock

Global Mood Clock is a production-ready Django + Django REST Framework application that visualizes the world’s current emotional “mood” using public discussion data. The UI uses Google Maps, HTMX, and WebSockets for real-time updates.

## Features

- Google Maps world map with emoji overlays by country.
- HTMX-powered country detail panel.
- Real-time WebSocket updates via Django Channels.
- Celery + Redis ingestion pipeline with configurable providers.
- REST API for country mood data and history.
- Seed command for country metadata.

## Quick Start (Docker)

1. Export environment variables (or create a `.env` file):

```bash
export GOOGLE_MAPS_API_KEY=your_key
export PROVIDER=mock
```

2. Start the stack:

```bash
docker-compose up --build
```

3. Visit: http://localhost:8000

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py seed_countries
python manage.py runserver 0.0.0.0:8000
```

## Static Files in Production

The production stack runs `collectstatic` on startup so built assets (like `frontend/static/css/styles.css`) are available under `STATIC_ROOT` at `/static/`. If you use a reverse proxy (Nginx, etc.), configure it to serve `/static/` from the built static directory (`frontend/static`) or from `STATIC_ROOT` when `DEBUG=false`.

## Environment Variables

- `DJANGO_SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `REDIS_URL`
- `GOOGLE_MAPS_API_KEY`
- `PROVIDER` (composite | x | reddit | mock)
- `X_BEARER_TOKEN`
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT`
- `TOP_COUNTRIES`
- `WINDOW_MINUTES`
- `ENABLE_THREEJS`

## API Endpoints

- `GET /api/countries/`
- `GET /api/countries/{code}/`
- `GET /api/snapshots/latest/?minutes=15`
- `GET /api/snapshots/{code}/history/?hours=24`

## Tasks

- `refresh_country_mood(country_code, window_minutes)`
- `refresh_all_moods()`

## Health Check

- `GET /healthz`

## Tests

```bash
pytest
```
