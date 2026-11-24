"""URL routing for Cooks domain."""

from __future__ import annotations

from django.urls import path

from apps.cooks.views import (
    AdminCookVerificationDetailView,
    CookAvailabilityView,
    CookDetailView,
    CookLeaveCreateView,
    CookListCreateView,
    CookVerificationSelfView,
)

urlpatterns = [
    path("cooks", CookListCreateView.as_view(), name="cook-list-create"),
    path("cooks/me/verification", CookVerificationSelfView.as_view(), name="cook-verification-me"),
    path("cooks/<uuid:pk>", CookDetailView.as_view(), name="cook-detail"),
    path("cooks/<uuid:pk>/availability", CookAvailabilityView.as_view(), name="cook-availability"),
    path("cooks/<uuid:pk>/leave", CookLeaveCreateView.as_view(), name="cook-leave"),
    path("admin/cooks/<uuid:pk>/verification", AdminCookVerificationDetailView.as_view(), name="admin-cook-verification"),
]
