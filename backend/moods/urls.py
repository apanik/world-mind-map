from django.urls import path

from moods import views

urlpatterns = [
    path("", views.index, name="index"),
    path("country/<str:code>/panel/", views.country_panel, name="country-panel"),
    path("healthz", views.healthz, name="healthz"),
]
