from django.urls import path
from . import views

urlpatterns = [
    path("overview/", views.overview, name="analytics-overview"),
    path("trends/", views.trends, name="analytics-trends"),
    path(
        "outreach-effectiveness/",
        views.outreach_effectiveness,
        name="analytics-outreach-effectiveness",
    ),
    path(
        "coordinator-performance/",
        views.coordinator_performance,
        name="analytics-coordinator-performance",
    ),
]
