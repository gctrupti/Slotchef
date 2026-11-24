"""URL routing for Households domain."""

from __future__ import annotations

from django.urls import path

from apps.households.views import (
    AdminHouseholdVerificationDetailView,
    HouseholdDetailView,
    HouseholdListCreateView,
    HouseholdVerificationSelfView,
)

urlpatterns = [
    path("households", HouseholdListCreateView.as_view(), name="household-list-create"),
    path("households/<uuid:pk>", HouseholdDetailView.as_view(), name="household-detail"),
    path("households/<uuid:pk>/verification", HouseholdVerificationSelfView.as_view(), name="household-verification-self"),
    path("admin/households/<uuid:pk>/verification", AdminHouseholdVerificationDetailView.as_view(), name="admin-household-verification"),
]
