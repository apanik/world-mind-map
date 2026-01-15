from django.urls import path

from moods import consumers

websocket_urlpatterns = [
    path("ws/moods/", consumers.MoodUpdatesConsumer.as_asgi()),
]
