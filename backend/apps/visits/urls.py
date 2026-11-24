"""URL routing for Visit operations, safety, SOS, and trust & safety domains."""

from __future__ import annotations

from django.urls import path

from apps.visits.views import (
    AdminAccountRestrictionCreateView,
    AdminAccountRestrictionLiftView,
    AdminIncidentAppealDecideView,
    AdminIncidentInvestigateView,
    AdminIncidentResolveView,
    AdminOverdueVisitsView,
    AdminReviewModerateView,
    AdminSOSIncidentDetailView,
    AdminSOSIncidentListView,
    EmergencyContactDetailView,
    EmergencyContactListCreateView,
    IncidentAppealCreateView,
    IncidentReportListCreateView,
    IncidentReportView,
    TwoSidedReviewCreateView,
    VisitCheckInView,
    VisitCheckOutView,
    VisitCompleteView,
    VisitConfirmArrivalView,
    VisitLocationPingView,
    VisitSOSView,
    VisitStartView,
)

urlpatterns = [
    # Visit Lifecycle & Safety Operations (Phase 12)
    path("assignments/<uuid:pk>/check-in", VisitCheckInView.as_view(), name="visit-check-in"),
    path("assignments/<uuid:pk>/start", VisitStartView.as_view(), name="visit-start"),
    path("assignments/<uuid:pk>/complete", VisitCompleteView.as_view(), name="visit-complete"),
    path("assignments/<uuid:pk>/check-out", VisitCheckOutView.as_view(), name="visit-check-out"),
    path("assignments/<uuid:pk>/confirm-arrival", VisitConfirmArrivalView.as_view(), name="visit-confirm-arrival"),
    path("assignments/<uuid:pk>/location-ping", VisitLocationPingView.as_view(), name="visit-location-ping"),
    path("assignments/<uuid:pk>/sos", VisitSOSView.as_view(), name="visit-sos"),
    path("assignments/<uuid:pk>/report-incident", IncidentReportView.as_view(), name="visit-report-incident"),

    # Emergency Contacts & Admin Safety Operations
    path("safety/emergency-contacts", EmergencyContactListCreateView.as_view(), name="safety-emergency-contacts"),
    path("safety/emergency-contacts/<uuid:pk>", EmergencyContactDetailView.as_view(), name="safety-emergency-contact-detail"),
    path("admin/safety/overdue-visits", AdminOverdueVisitsView.as_view(), name="admin-overdue-visits"),
    path("admin/safety/sos-incidents", AdminSOSIncidentListView.as_view(), name="admin-sos-incidents"),
    path("admin/safety/sos-incidents/<uuid:pk>", AdminSOSIncidentDetailView.as_view(), name="admin-sos-incident-detail"),

    # Trust & Safety, Incidents, Appeals, Restrictions & Moderation (Phase 13)
    path("incidents", IncidentReportListCreateView.as_view(), name="incidents-list-create"),
    path("admin/incidents/<uuid:pk>/investigate", AdminIncidentInvestigateView.as_view(), name="admin-incident-investigate"),
    path("admin/incidents/<uuid:pk>/resolve", AdminIncidentResolveView.as_view(), name="admin-incident-resolve"),
    path("incidents/<uuid:pk>/appeal", IncidentAppealCreateView.as_view(), name="incident-appeal-create"),
    path("admin/incidents/appeals/<uuid:pk>/decide", AdminIncidentAppealDecideView.as_view(), name="admin-incident-appeal-decide"),
    path("admin/trust/restrictions", AdminAccountRestrictionCreateView.as_view(), name="admin-restriction-create"),
    path("admin/trust/restrictions/<uuid:pk>/lift", AdminAccountRestrictionLiftView.as_view(), name="admin-restriction-lift"),
    path("assignments/<uuid:pk>/reviews", TwoSidedReviewCreateView.as_view(), name="assignment-review-create"),
    path("admin/reviews/<uuid:pk>/moderate", AdminReviewModerateView.as_view(), name="admin-review-moderate"),
]
