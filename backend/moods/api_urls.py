from django.urls import path

from moods import api_views

urlpatterns = [
    path("countries/", api_views.CountryListView.as_view()),
    path("countries/<str:code>/", api_views.CountryDetailView.as_view()),
    path("snapshots/latest/", api_views.LatestSnapshotsView.as_view()),
    path("snapshots/<str:code>/history/", api_views.SnapshotHistoryView.as_view()),
]
