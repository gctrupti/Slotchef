"""URL routing for Communities domain."""

from __future__ import annotations

from django.urls import path

from apps.communities.views import SocietyDetailView, SocietyListCreateView

urlpatterns = [
    path("societies", SocietyListCreateView.as_view(), name="society-list-create"),
    path("societies/<uuid:pk>", SocietyDetailView.as_view(), name="society-detail"),
]
