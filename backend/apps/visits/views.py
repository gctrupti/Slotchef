"""Views for Visit lifecycle events, safety checks, SOS emergency handling, incident reporting, and trust operations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.bookings.models import Booking
from apps.cooks.models import CookAvailability
from apps.identity.models import Role, User
from apps.operations.models import OutboxEvent
from apps.scheduling.models import CookAssignment
from apps.scheduling.services.orchestrator import SchedulingOrchestrator
from apps.visits.models import (
    AccountRestriction,
    BackupProposal,
    EmergencyContact,
    IncidentAppeal,
    IncidentReport,
    SOSIncident,
    TwoSidedReview,
    VisitEvent,
)
from apps.visits.serializers import (
    AccountRestrictionSerializer,
    EmergencyContactSerializer,
    IncidentAppealSerializer,
    IncidentReportSerializer,
    SOSIncidentSerializer,
    TwoSidedReviewSerializer,
    VisitEventSerializer,
    VisitSafetyCheckSerializer,
)
from apps.visits.services.safety_service import SafetyService
from apps.visits.services.trust_service import TrustService
from config.exceptions import SlotChefAPIError


class VisitCheckInView(APIView):
    """Record cook physical arrival / check-in at the household."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses={200: VisitEventSerializer}, summary="Cook check-in at household")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        assignment = get_object_or_404(CookAssignment, pk=pk)

        lat = Decimal(str(request.data["latitude"])) if "latitude" in request.data else None
        lon = Decimal(str(request.data["longitude"])) if "longitude" in request.data else None
        notes = request.data.get("notes", "")

        try:
            SafetyService.record_cook_check_in(
                assignment=assignment,
                cook_user=request.user,
                latitude=lat,
                longitude=lon,
                notes=notes,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_403_FORBIDDEN)

        event = assignment.events.filter(event_type=VisitEvent.TYPE_CHECK_IN).last()
        return Response(VisitEventSerializer(event).data, status=status.HTTP_200_OK)


class VisitStartView(APIView):
    """Mark visit as started and cooking in progress."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses={200: VisitEventSerializer}, summary="Start cooking visit")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        assignment = get_object_or_404(CookAssignment, pk=pk)

        if not (request.user.is_superuser or request.user == assignment.cook.user or request.user.has_role("platform_admin")):
            raise SlotChefAPIError(
                detail="Forbidden: Only the assigned cook can start this visit.",
                code="FORBIDDEN",
                status_code=403,
            )

        with transaction.atomic():
            assignment.status = CookAssignment.STATUS_STARTED
            assignment.save(update_fields=["status", "updated_at"])

            booking = assignment.booking
            booking.status = Booking.STATUS_IN_PROGRESS
            booking.save(update_fields=["status", "updated_at"])

            event = VisitEvent.objects.create(
                assignment=assignment,
                event_type=VisitEvent.TYPE_STARTED,
                notes=request.data.get("notes", ""),
            )

            AuditLog.objects.create(
                actor=request.user,
                action="visit.started",
                entity_type="CookAssignment",
                entity_id=str(assignment.id),
                after_state={"assignment_status": assignment.status, "booking_status": booking.status},
            )

        return Response(VisitEventSerializer(event).data, status=status.HTTP_200_OK)


class VisitCompleteView(APIView):
    """Mark visit completed and meal prepared."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses={200: VisitEventSerializer}, summary="Complete cooking visit")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        assignment = get_object_or_404(CookAssignment, pk=pk)

        if not (request.user.is_superuser or request.user == assignment.cook.user or request.user.has_role("platform_admin")):
            raise SlotChefAPIError(
                detail="Forbidden: Only the assigned cook can complete this visit.",
                code="FORBIDDEN",
                status_code=403,
            )

        with transaction.atomic():
            assignment.status = CookAssignment.STATUS_COMPLETED
            assignment.save(update_fields=["status", "updated_at"])

            booking = assignment.booking
            booking.status = Booking.STATUS_COMPLETED
            booking.save(update_fields=["status", "updated_at"])

            event = VisitEvent.objects.create(
                assignment=assignment,
                event_type=VisitEvent.TYPE_COMPLETED,
                notes=request.data.get("notes", ""),
            )

            AuditLog.objects.create(
                actor=request.user,
                action="visit.completed",
                entity_type="CookAssignment",
                entity_id=str(assignment.id),
                after_state={"assignment_status": assignment.status, "booking_status": booking.status},
            )

            OutboxEvent.objects.create(
                event_type="visit.completed",
                aggregate_type="CookAssignment",
                aggregate_id=str(assignment.id),
                payload={"booking_id": str(booking.id), "cook_id": str(assignment.cook_id)},
            )

        return Response(VisitEventSerializer(event).data, status=status.HTTP_200_OK)


class VisitCheckOutView(APIView):
    """Record cook departure / check-out from household premises."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses={200: VisitSafetyCheckSerializer}, summary="Cook check-out from household")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        assignment = get_object_or_404(CookAssignment, pk=pk)

        lat = Decimal(str(request.data["latitude"])) if "latitude" in request.data else None
        lon = Decimal(str(request.data["longitude"])) if "longitude" in request.data else None
        notes = request.data.get("notes", "")

        try:
            safety_check = SafetyService.record_cook_check_out(
                assignment=assignment,
                cook_user=request.user,
                latitude=lat,
                longitude=lon,
                notes=notes,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_403_FORBIDDEN)

        return Response(VisitSafetyCheckSerializer(safety_check).data, status=status.HTTP_200_OK)


class VisitConfirmArrivalView(APIView):
    """Household resident confirms cook arrival."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses={200: VisitSafetyCheckSerializer}, summary="Household confirms cook arrival")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        assignment = get_object_or_404(CookAssignment, pk=pk)
        notes = request.data.get("notes", "")

        try:
            safety_check = SafetyService.confirm_household_arrival(
                assignment=assignment,
                resident_user=request.user,
                notes=notes,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_403_FORBIDDEN)

        return Response(VisitSafetyCheckSerializer(safety_check).data, status=status.HTTP_200_OK)


class VisitLocationPingView(APIView):
    """Record consent-based GPS coordinate ping during active visit."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=dict, responses={200: VisitSafetyCheckSerializer}, summary="Consent-based location ping")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        assignment = get_object_or_404(CookAssignment, pk=pk)
        lat = Decimal(str(request.data.get("latitude", 0)))
        lon = Decimal(str(request.data.get("longitude", 0)))

        try:
            safety_check = SafetyService.update_consent_location_ping(
                assignment=assignment,
                user=request.user,
                latitude=lat,
                longitude=lon,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(VisitSafetyCheckSerializer(safety_check).data, status=status.HTTP_200_OK)


class VisitSOSView(APIView):
    """Trigger emergency SOS alarm with immediate contact dispatch and India 112 metadata."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=dict, responses={201: SOSIncidentSerializer}, summary="Trigger emergency SOS alarm")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        assignment = get_object_or_404(CookAssignment, pk=pk)

        lat = Decimal(str(request.data["latitude"])) if "latitude" in request.data else None
        lon = Decimal(str(request.data["longitude"])) if "longitude" in request.data else None
        notes = request.data.get("notes", "Urgent help requested")
        source = request.data.get("trigger_source", SOSIncident.SRC_COOK if request.user == assignment.cook.user else SOSIncident.SRC_HOUSEHOLD)

        sos = SafetyService.trigger_sos(
            triggered_by=request.user,
            assignment=assignment,
            trigger_source=source,
            latitude=lat,
            longitude=lon,
            notes=notes,
        )
        return Response(SOSIncidentSerializer(sos).data, status=status.HTTP_201_CREATED)


class EmergencyContactListCreateView(generics.ListCreateAPIView):
    """Manage trusted emergency contacts."""

    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)

    def perform_create(self, serializer: EmergencyContactSerializer) -> None:
        serializer.save(user=self.request.user)


class EmergencyContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or remove a trusted emergency contact."""

    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)


class AdminOverdueVisitsView(APIView):
    """Detect and list overdue visits past start or completion grace thresholds."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses={200: dict}, summary="Audit and detect overdue visits")
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if not (request.user.is_superuser or request.user.has_role(Role.PLATFORM_ADMIN)):
            return Response({"detail": "Forbidden: Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        overdue_list = SafetyService.detect_overdue_visits()
        return Response(
            {
                "overdue_count": len(overdue_list),
                "overdue_assignment_ids": [str(a.id) for a in overdue_list],
            },
            status=status.HTTP_200_OK,
        )


class AdminSOSIncidentListView(generics.ListAPIView):
    """List active and historical SOS emergency incidents."""

    serializer_class = SOSIncidentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not (user.is_superuser or user.has_role(Role.PLATFORM_ADMIN)):
            return SOSIncident.objects.none()
        return SOSIncident.objects.select_related("triggered_by", "assignment").prefetch_related("notification_logs").all()


class AdminSOSIncidentDetailView(APIView):
    """Acknowledge or resolve an SOS emergency incident."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=dict, responses={200: SOSIncidentSerializer}, summary="Acknowledge or resolve SOS")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        if not (request.user.is_superuser or request.user.has_role(Role.PLATFORM_ADMIN)):
            return Response({"detail": "Forbidden: Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        sos = get_object_or_404(SOSIncident, pk=pk)
        new_status = request.data.get("status", SOSIncident.STATUS_RESOLVED)
        notes = request.data.get("notes", "")

        sos.status = new_status
        sos.notes = f"{sos.notes}\nAdmin resolution: {notes}".strip()
        if new_status == SOSIncident.STATUS_RESOLVED:
            sos.resolved_at = timezone.now()
            sos.resolved_by = request.user
        sos.save()

        AuditLog.objects.create(
            actor=request.user,
            action="safety.sos_updated",
            entity_type="SOSIncident",
            entity_id=str(sos.id),
            after_state={"status": sos.status},
        )
        return Response(SOSIncidentSerializer(sos).data, status=status.HTTP_200_OK)


# -------------------------------------------------------------
# PHASE 13: INCIDENT MANAGEMENT AND TRUST OPERATIONS VIEWS
# -------------------------------------------------------------

class IncidentReportView(APIView):
    """Report an operational incident and trigger backup cook re-optimization on absence."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=IncidentReportSerializer,
        responses={201: IncidentReportSerializer},
        summary="Report visit incident (delay/absence) and trigger backup workflow",
    )
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        assignment = get_object_or_404(CookAssignment, pk=pk)
        user = request.user

        is_cook = hasattr(user, "cook_profile") and user.cook_profile == assignment.cook
        is_resident = assignment.booking.household.members.filter(user=user, is_active=True).exists()
        if not (user.is_superuser or user.has_role("platform_admin") or is_cook or is_resident):
            raise SlotChefAPIError(
                detail="Forbidden: You cannot report an incident for this visit.",
                code="FORBIDDEN",
                status_code=403,
            )

        category = request.data.get("category", IncidentReport.CAT_OTHER)
        severity = request.data.get("severity", IncidentReport.SEV_MEDIUM)
        description = request.data.get("description", "").strip()
        evidence_urls = request.data.get("evidence_urls", [])
        if isinstance(evidence_urls, str):
            evidence_urls = [evidence_urls]
        if not description:
            raise SlotChefAPIError(
                detail="Description is required for incident reporting.",
                code="VALIDATION_ERROR",
                status_code=400,
            )

        with transaction.atomic():
            incident = TrustService.file_incident_report(
                reported_by=user,
                assignment=assignment,
                category=category,
                severity=severity,
                description=description,
                evidence_urls=evidence_urls,
            )

            VisitEvent.objects.create(
                assignment=assignment,
                event_type=VisitEvent.TYPE_INCIDENT,
                notes=f"[{category.upper()}] {description}",
            )

            # If absence/unavailability, initiate backup re-optimization
            if category == IncidentReport.CAT_ABSENCE:
                service_date = assignment.schedule_plan.service_date
                society = assignment.schedule_plan.society
                booking = assignment.booking

                assignment.status = CookAssignment.STATUS_REPLACED
                assignment.replacement_reason = f"Cook absence reported: {description}"
                assignment.save(update_fields=["status", "replacement_reason", "updated_at"])

                CookAvailability.objects.update_or_create(
                    cook=assignment.cook,
                    specific_date=service_date,
                    defaults={
                        "start_minute": 0,
                        "end_minute": 1,
                        "availability_type": CookAvailability.TYPE_OVERRIDE,
                    },
                )

                booking.status = Booking.STATUS_PENDING
                booking.save(update_fields=["status", "updated_at"])

        if category == IncidentReport.CAT_ABSENCE:
            orchestrator = SchedulingOrchestrator()
            new_plan, _ = orchestrator.run_and_commit(
                society=society,
                service_date=service_date,
                actor=user,
                correlation_id=f"backup-incident-{incident.id}",
            )

            new_assignment = CookAssignment.objects.filter(
                schedule_plan=new_plan,
                booking=booking,
                status=CookAssignment.STATUS_CONFIRMED,
            ).first()

            if new_assignment:
                assignment.replaced_by = new_assignment
                assignment.save(update_fields=["replaced_by", "updated_at"])

                BackupProposal.objects.create(
                    original_assignment=assignment,
                    proposed_cook=new_assignment.cook,
                    status=BackupProposal.STATUS_ACCEPTED,
                    reason=f"Automated backup assigned for absence on {service_date}",
                )
            else:
                booking.status = Booking.STATUS_NEEDS_REVIEW
                booking.save(update_fields=["status", "updated_at"])

                BackupProposal.objects.create(
                    original_assignment=assignment,
                    proposed_cook=assignment.cook,
                    status=BackupProposal.STATUS_REJECTED,
                    reason="No feasible backup cook available with matching skills and open capacity.",
                )

        return Response(IncidentReportSerializer(incident).data, status=status.HTTP_201_CREATED)


class IncidentReportListCreateView(generics.ListCreateAPIView):
    """File and list two-sided complaints with evidence."""

    serializer_class = IncidentReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.has_role(Role.PLATFORM_ADMIN):
            return IncidentReport.objects.all()
        return IncidentReport.objects.filter(reported_by=user)

    def perform_create(self, serializer: IncidentReportSerializer) -> None:
        TrustService.file_incident_report(
            reported_by=self.request.user,
            assignment=serializer.validated_data.get("assignment"),
            category=serializer.validated_data.get("category", IncidentReport.CAT_OTHER),
            severity=serializer.validated_data.get("severity", IncidentReport.SEV_MEDIUM),
            description=serializer.validated_data["description"],
            evidence_urls=serializer.validated_data.get("evidence_urls", []),
            target_user=serializer.validated_data.get("target_user"),
        )


class AdminIncidentInvestigateView(APIView):
    """Admin records confidential investigation findings."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=dict, responses={200: IncidentReportSerializer}, summary="Update investigation notes")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        incident = get_object_or_404(IncidentReport, pk=pk)
        notes = request.data.get("notes", "")
        new_status = request.data.get("status", IncidentReport.STATUS_UNDER_INVESTIGATION)

        try:
            updated = TrustService.investigate_incident(
                incident=incident,
                admin_user=request.user,
                notes=notes,
                new_status=new_status,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_403_FORBIDDEN)

        return Response(IncidentReportSerializer(updated).data, status=status.HTTP_200_OK)


class AdminIncidentResolveView(APIView):
    """Admin resolves or dismisses an incident complaint."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=dict, responses={200: IncidentReportSerializer}, summary="Resolve incident")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        incident = get_object_or_404(IncidentReport, pk=pk)
        summary = request.data.get("resolution_summary", "")
        outcome = request.data.get("status", IncidentReport.STATUS_RESOLVED)

        try:
            resolved = TrustService.resolve_incident(
                incident=incident,
                admin_user=request.user,
                resolution_summary=summary,
                outcome_status=outcome,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_403_FORBIDDEN)

        return Response(IncidentReportSerializer(resolved).data, status=status.HTTP_200_OK)


class IncidentAppealCreateView(APIView):
    """Submit appeal against an adverse incident resolution."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=IncidentAppealSerializer, responses={201: IncidentAppealSerializer}, summary="File incident appeal")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        incident = get_object_or_404(IncidentReport, pk=pk)
        reason = request.data.get("reason", "").strip()
        if not reason:
            return Response({"detail": "Reason is required to submit an appeal."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            appeal = TrustService.file_appeal(
                incident=incident,
                appellant=request.user,
                reason=reason,
                additional_evidence=request.data.get("additional_evidence", []),
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(IncidentAppealSerializer(appeal).data, status=status.HTTP_201_CREATED)


class AdminIncidentAppealDecideView(APIView):
    """Senior administrator adjudicates appeal."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=dict, responses={200: IncidentAppealSerializer}, summary="Adjudicate appeal")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        appeal = get_object_or_404(IncidentAppeal, pk=pk)
        decision = request.data.get("status", IncidentAppeal.STATUS_UPHELD)
        decision_notes = request.data.get("decision_notes", "")

        try:
            decided = TrustService.decide_appeal(
                appeal=appeal,
                admin_user=request.user,
                decision_status=decision,
                decision_notes=decision_notes,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_403_FORBIDDEN)

        return Response(IncidentAppealSerializer(decided).data, status=status.HTTP_200_OK)


class AdminAccountRestrictionCreateView(APIView):
    """Impose administrative account restrictions."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=AccountRestrictionSerializer, responses={201: AccountRestrictionSerializer}, summary="Impose restriction")
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user_id = request.data.get("user")
        target_user = get_object_or_404(User, pk=user_id)
        restriction_type = request.data.get("restriction_type", AccountRestriction.RESTRICTION_WARNING)
        reason = request.data.get("reason", "").strip()
        incident_id = request.data.get("incident")
        incident = IncidentReport.objects.filter(pk=incident_id).first() if incident_id else None

        if not reason:
            return Response({"detail": "Reason is required to impose account restriction."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            restriction = TrustService.impose_restriction(
                user=target_user,
                admin_user=request.user,
                restriction_type=restriction_type,
                reason=reason,
                incident=incident,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_403_FORBIDDEN)

        return Response(AccountRestrictionSerializer(restriction).data, status=status.HTTP_201_CREATED)


class AdminAccountRestrictionLiftView(APIView):
    """Lift an active account restriction."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=dict, responses={200: AccountRestrictionSerializer}, summary="Lift restriction")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        restriction = get_object_or_404(AccountRestriction, pk=pk)
        lift_reason = request.data.get("lift_reason", "Completed compliance review")

        try:
            lifted = TrustService.lift_restriction(
                restriction=restriction,
                admin_user=request.user,
                lift_reason=lift_reason,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_403_FORBIDDEN)

        return Response(AccountRestrictionSerializer(lifted).data, status=status.HTTP_200_OK)


class TwoSidedReviewCreateView(APIView):
    """Submit reciprocal rating and review for visit."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=TwoSidedReviewSerializer, responses={201: TwoSidedReviewSerializer}, summary="Submit visit review")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        assignment = get_object_or_404(CookAssignment, pk=pk)
        rating = int(request.data.get("rating", 5))
        comment = request.data.get("comment", "")
        feedback_tags = request.data.get("feedback_tags", [])

        try:
            review = TrustService.submit_review(
                assignment=assignment,
                reviewer=request.user,
                rating=rating,
                comment=comment,
                feedback_tags=feedback_tags,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(TwoSidedReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class AdminReviewModerateView(APIView):
    """Moderate published review."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=dict, responses={200: TwoSidedReviewSerializer}, summary="Moderate review")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        review = get_object_or_404(TwoSidedReview, pk=pk)
        mod_status = request.data.get("moderation_status", TwoSidedReview.MOD_PUBLISHED)
        notes = request.data.get("moderation_notes", "")

        try:
            moderated = TrustService.moderate_review(
                review=review,
                admin_user=request.user,
                moderation_status=mod_status,
                moderation_notes=notes,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_403_FORBIDDEN)

        return Response(TwoSidedReviewSerializer(moderated).data, status=status.HTTP_200_OK)
