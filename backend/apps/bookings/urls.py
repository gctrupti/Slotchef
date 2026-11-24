"""URL routing for Booking domain."""

from __future__ import annotations

from django.urls import path

from apps.bookings.views import (
    BookingCancelView,
    BookingDetailView,
    BookingRescheduleView,
    HouseholdBookingCreateView,
    HouseholdPackageSubscribeView,
    HouseholdPackageSubscriptionListView,
    PackagePlanListCreateView,
    PackageSubscriptionCancelView,
    PackageSubscriptionDetailView,
    PackageSubscriptionPauseView,
    PackageSubscriptionResumeView,
    PackageVisitRescheduleView,
)

urlpatterns = [
    # Bookings
    path("households/<uuid:pk>/bookings", HouseholdBookingCreateView.as_view(), name="household-booking-create"),
    path("bookings/<uuid:pk>", BookingDetailView.as_view(), name="booking-detail"),
    path("bookings/<uuid:pk>/cancel", BookingCancelView.as_view(), name="booking-cancel"),
    path("bookings/<uuid:pk>/reschedule", BookingRescheduleView.as_view(), name="booking-reschedule"),

    # Packages & Subscriptions
    path("packages/plans", PackagePlanListCreateView.as_view(), name="package-plan-list-create"),
    path("households/<uuid:household_id>/packages/subscribe", HouseholdPackageSubscribeView.as_view(), name="household-package-subscribe"),
    path("households/<uuid:household_id>/packages", HouseholdPackageSubscriptionListView.as_view(), name="household-package-list"),
    path("packages/subscriptions/<uuid:subscription_id>", PackageSubscriptionDetailView.as_view(), name="package-subscription-detail"),
    path("packages/subscriptions/<uuid:subscription_id>/pause", PackageSubscriptionPauseView.as_view(), name="package-subscription-pause"),
    path("packages/subscriptions/<uuid:subscription_id>/resume", PackageSubscriptionResumeView.as_view(), name="package-subscription-resume"),
    path("packages/subscriptions/<uuid:subscription_id>/cancel", PackageSubscriptionCancelView.as_view(), name="package-subscription-cancel"),
    path("packages/bookings/<uuid:booking_id>/reschedule", PackageVisitRescheduleView.as_view(), name="package-visit-reschedule"),
]
