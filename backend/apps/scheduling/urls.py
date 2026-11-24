"""URL routing for Scheduling domain."""

from __future__ import annotations

from django.urls import path

from apps.scheduling.views import (
    AdminDailyScheduleView,
    AdminReoptimizeScheduleView,
    CookScheduleMeView,
)

urlpatterns = [
    path("cooks/me/schedule", CookScheduleMeView.as_view(), name="cook-schedule-me"),
    path("admin/schedules/<str:date>", AdminDailyScheduleView.as_view(), name="admin-schedule-daily"),
    path("admin/schedules/<str:date>/reoptimize", AdminReoptimizeScheduleView.as_view(), name="admin-schedule-reoptimize"),
]
