from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("moods.urls")),
    path("api/", include("moods.api_urls")),
]
