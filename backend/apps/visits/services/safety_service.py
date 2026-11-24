"""Visit safety, arrival confirmation, overdue detection, location tracking, and SOS management."""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.identity.models import Role, User
from apps.scheduling.models import CookAssignment
from apps.visits.models import (
    EmergencyContact,
    SafetyNotificationLog,
    SOSIncident,
    VisitEvent,
    VisitSafetyCheck,
)
from apps.visits.providers.notification_provider import get_notification_provider

logger = logging.getLogger(__name__)


class SafetyService:
    """Manages visit execution safety checks, arrival confirmations, overdue monitoring, and SOS escalation."""

    @classmethod
    def get_or_create_safety_check(cls, assignment: CookAssignment) -> VisitSafetyCheck:
        safety_check, _ = VisitSafetyCheck.objects.get_or_create(assignment=assignment)
        return safety_check

    @classmethod
    def record_cook_check_in(
        cls,
        assignment: CookAssignment,
        cook_user: User,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        notes: str = "",
    ) -> VisitSafetyCheck:
        """Cook checks in upon physical arrival at household premises."""
        if not (cook_user.is_superuser or assignment.cook.user == cook_user or cook_user.has_role(Role.PLATFORM_ADMIN)):
            raise ValidationError("Forbidden: Only the assigned cook can check in.")

        now = timezone.now()
        with transaction.atomic():
            safety_check = cls.get_or_create_safety_check(assignment)
            safety_check.check_in_at = now
            if latitude and longitude:
                safety_check.last_latitude = latitude
                safety_check.last_longitude = longitude
                safety_check.last_location_at = now
            safety_check.save()

            VisitEvent.objects.create(
                assignment=assignment,
                event_type=VisitEvent.TYPE_CHECK_IN,
                recorded_at=now,
                notes=notes,
                metadata={"lat": float(latitude) if latitude else None, "lon": float(longitude) if longitude else None},
            )

        return safety_check

    @classmethod
    def confirm_household_arrival(
        cls,
        assignment: CookAssignment,
        resident_user: User,
        notes: str = "",
    ) -> VisitSafetyCheck:
        """Household confirms that cook has arrived inside their residence."""
        household = assignment.booking.household
        is_member = household.members.filter(user=resident_user, is_active=True).exists()
        if not (resident_user.is_superuser or is_member or resident_user.has_role(Role.PLATFORM_ADMIN)):
            raise ValidationError("Forbidden: Only a resident of this household can confirm arrival.")

        now = timezone.now()
        with transaction.atomic():
            safety_check = cls.get_or_create_safety_check(assignment)
            safety_check.arrival_confirmed_at = now
            safety_check.arrival_confirmed_by = resident_user
            safety_check.save()

            VisitEvent.objects.create(
                assignment=assignment,
                event_type=VisitEvent.TYPE_ARRIVAL_CONFIRMED,
                recorded_at=now,
                notes=notes,
            )

        return safety_check

    @classmethod
    def record_cook_check_out(
        cls,
        assignment: CookAssignment,
        cook_user: User,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        notes: str = "",
    ) -> VisitSafetyCheck:
        """Cook checks out upon completing work and departing premises."""
        if not (cook_user.is_superuser or assignment.cook.user == cook_user or cook_user.has_role(Role.PLATFORM_ADMIN)):
            raise ValidationError("Forbidden: Only the assigned cook can check out.")

        now = timezone.now()
        with transaction.atomic():
            safety_check = cls.get_or_create_safety_check(assignment)
            safety_check.check_out_at = now
            if latitude and longitude:
                safety_check.last_latitude = latitude
                safety_check.last_longitude = longitude
                safety_check.last_location_at = now
            safety_check.save()

            VisitEvent.objects.create(
                assignment=assignment,
                event_type=VisitEvent.TYPE_CHECK_OUT,
                recorded_at=now,
                notes=notes,
                metadata={"lat": float(latitude) if latitude else None, "lon": float(longitude) if longitude else None},
            )

        return safety_check

    @classmethod
    def update_consent_location_ping(
        cls,
        assignment: CookAssignment,
        user: User,
        latitude: Decimal,
        longitude: Decimal,
    ) -> VisitSafetyCheck:
        """Optional consent-based location sharing during active visit."""
        is_cook = assignment.cook.user == user
        is_resident = assignment.booking.household.members.filter(user=user, is_active=True).exists()

        if not (user.is_superuser or is_cook or is_resident):
            raise ValidationError("Forbidden: Only active visit participants can share location.")

        now = timezone.now()
        safety_check = cls.get_or_create_safety_check(assignment)
        safety_check.location_sharing_consented = True
        safety_check.last_latitude = latitude
        safety_check.last_longitude = longitude
        safety_check.last_location_at = now
        safety_check.save()

        VisitEvent.objects.create(
            assignment=assignment,
            event_type=VisitEvent.TYPE_LOCATION_PING,
            recorded_at=now,
            metadata={"lat": float(latitude), "lon": float(longitude)},
        )

        return safety_check

    @classmethod
    def detect_overdue_visits(
        cls,
        check_in_grace_minutes: int = 20,
        check_out_grace_minutes: int = 30,
    ) -> list[CookAssignment]:
        """Detect visits where cook is overdue for arrival check-in or completion check-out."""
        now = timezone.now()
        overdue_assignments: list[CookAssignment] = []

        # 1. Overdue for Check-in: start_at passed by grace minutes and no check-in recorded
        overdue_start_threshold = now - timedelta(minutes=check_in_grace_minutes)
        unstarted = CookAssignment.objects.filter(
            status=CookAssignment.STATUS_CONFIRMED,
            start_at__lt=overdue_start_threshold,
        ).select_related("safety_check")

        for assignment in unstarted:
            safety = cls.get_or_create_safety_check(assignment)
            if not safety.check_in_at:
                safety.is_overdue = True
                safety.overdue_reason = f"Cook has not checked in {check_in_grace_minutes} minutes past scheduled start."
                safety.save(update_fields=["is_overdue", "overdue_reason", "updated_at"])
                overdue_assignments.append(assignment)

        # 2. Overdue for Check-out: end_at passed by grace minutes and no check-out recorded
        overdue_end_threshold = now - timedelta(minutes=check_out_grace_minutes)
        uncompleted = CookAssignment.objects.filter(
            status__in=[CookAssignment.STATUS_CONFIRMED, CookAssignment.STATUS_STARTED],
            end_at__lt=overdue_end_threshold,
        ).select_related("safety_check")

        for assignment in uncompleted:
            safety = cls.get_or_create_safety_check(assignment)
            if not safety.check_out_at and not safety.is_overdue:
                safety.is_overdue = True
                safety.overdue_reason = f"Visit still marked open {check_out_grace_minutes} minutes past scheduled departure."
                safety.save(update_fields=["is_overdue", "overdue_reason", "updated_at"])
                overdue_assignments.append(assignment)

        return overdue_assignments

    @classmethod
    def trigger_sos(
        cls,
        triggered_by: User,
        assignment: CookAssignment | None = None,
        trigger_source: str = SOSIncident.SRC_COOK,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        notes: str = "",
    ) -> SOSIncident:
        """Trigger urgent SOS safety alert with emergency contact broadcast and India 112 metadata."""
        now = timezone.now()
        notifier = get_notification_provider()

        # Build India 112 standardized metadata packet
        india_112_metadata: dict[str, Any] = {
            "emergency_helpline": "112",
            "jurisdiction_country": "IN",
            "incident_timestamp": now.isoformat(),
            "trigger_source": trigger_source,
            "coordinates": {
                "latitude": float(latitude) if latitude else None,
                "longitude": float(longitude) if longitude else None,
            },
            "dispatch_status": "standby_for_local_psap_handshake",
            "instructions": "Call 112 immediately if life safety is threatened. Relay the society address and unit details below.",
        }

        if assignment:
            household = assignment.booking.household
            society = household.society
            india_112_metadata.update({
                "society_name": society.name,
                "society_address": society.address,
                "apartment_unit": household.apartment_label,
                "building": household.building.name,
                "cook_name": f"{assignment.cook.user.first_name} {assignment.cook.user.last_name}".strip() or assignment.cook.user.legal_name,
                "cook_phone": assignment.cook.user.phone,
                "booking_reference": str(assignment.booking_id),
            })

        with transaction.atomic():
            sos = SOSIncident.objects.create(
                assignment=assignment,
                triggered_by=triggered_by,
                trigger_source=trigger_source,
                latitude=latitude,
                longitude=longitude,
                notes=notes,
                india_112_metadata=india_112_metadata,
                status=SOSIncident.STATUS_TRIGGERED,
                external_dispatch_confirmed=False,  # strictly false until confirmed
            )

            if assignment:
                VisitEvent.objects.create(
                    assignment=assignment,
                    event_type=VisitEvent.TYPE_SOS,
                    recorded_at=now,
                    notes=f"Urgent SOS Triggered: {notes}",
                )

            # Broadcast to user's registered emergency contacts
            contacts = EmergencyContact.objects.filter(user=triggered_by)
            for contact in contacts:
                delivered = notifier.send_alert(
                    recipient_name=contact.name,
                    recipient_target=contact.phone,
                    channel="sms",
                    title="URGENT: SlotChef Emergency Alert",
                    message=(
                        f"EMERGENCY: {triggered_by.first_name or 'A SlotChef user'} triggered an SOS alarm. "
                        f"Call 112 or local authorities immediately. Ref: {sos.id}"
                    ),
                    payload=india_112_metadata,
                )
                SafetyNotificationLog.objects.create(
                    sos_incident=sos,
                    recipient_name=contact.name,
                    recipient_target=contact.phone,
                    channel="sms",
                    status="sent" if delivered else "failed",
                    payload=india_112_metadata,
                )

            # Alert platform admins
            admins = User.objects.filter(is_superuser=True) | User.objects.filter(user_roles__role__code=Role.PLATFORM_ADMIN)
            for admin in admins.distinct():
                delivered = notifier.send_alert(
                    recipient_name=admin.first_name or "Admin",
                    recipient_target=admin.email,
                    channel="email",
                    title="[CRITICAL ALARM] SlotChef Active SOS Triggered",
                    message=f"SOS Incident {sos.id} requires immediate operational intervention.",
                    payload=india_112_metadata,
                )
                SafetyNotificationLog.objects.create(
                    sos_incident=sos,
                    recipient_name=admin.first_name or "Admin",
                    recipient_target=admin.email,
                    channel="email",
                    status="sent" if delivered else "failed",
                    payload=india_112_metadata,
                )

            AuditLog.objects.create(
                actor=triggered_by,
                action="safety.sos_triggered",
                entity_type="SOSIncident",
                entity_id=str(sos.id),
                after_state={"status": sos.status, "trigger_source": trigger_source},
            )

        return sos
