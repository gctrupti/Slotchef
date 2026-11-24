"""Trust & Safety service managing incident investigations, appeals, account restrictions, and two-sided reviews."""

from __future__ import annotations

import logging
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.identity.models import Role, User
from apps.scheduling.models import CookAssignment
from apps.visits.models import (
    AccountRestriction,
    IncidentAppeal,
    IncidentReport,
    TwoSidedReview,
)

logger = logging.getLogger(__name__)


class TrustService:
    """Enterprise Trust & Safety operations."""

    @classmethod
    def file_incident_report(
        cls,
        reported_by: User,
        assignment: CookAssignment | None,
        category: str,
        severity: str,
        description: str,
        evidence_urls: list[str] | None = None,
        target_user: User | None = None,
    ) -> IncidentReport:
        """File a two-sided complaint with supporting evidence references."""
        # Auto-infer target user if assignment provided and target_user omitted
        if assignment and not target_user:
            cook_user = assignment.cook.user
            if reported_by == cook_user:
                # Target is primary resident of the household
                primary = assignment.booking.household.members.filter(role="primary").first()
                target_user = primary.user if primary else None
            else:
                target_user = cook_user

        with transaction.atomic():
            incident = IncidentReport.objects.create(
                assignment=assignment,
                reported_by=reported_by,
                target_user=target_user,
                category=category,
                severity=severity,
                description=description,
                evidence_urls=evidence_urls or [],
                status=IncidentReport.STATUS_REPORTED,
            )

            AuditLog.objects.create(
                actor=reported_by,
                action="incident.reported",
                entity_type="IncidentReport",
                entity_id=str(incident.id),
                after_state={
                    "category": category,
                    "severity": severity,
                    "target_user_id": str(target_user.id) if target_user else None,
                },
            )

        return incident

    @classmethod
    def investigate_incident(
        cls,
        incident: IncidentReport,
        admin_user: User,
        notes: str,
        new_status: str = IncidentReport.STATUS_UNDER_INVESTIGATION,
        investigator: User | None = None,
    ) -> IncidentReport:
        """Confidential admin investigation update."""
        if not (admin_user.is_superuser or admin_user.has_role(Role.PLATFORM_ADMIN)):
            raise ValidationError("Forbidden: Only administrators can conduct incident investigations.")

        incident.investigation_notes = f"{incident.investigation_notes}\n[{timezone.now().isoformat()}] {admin_user.email}: {notes}".strip()
        incident.status = new_status
        if investigator:
            incident.assigned_investigator = investigator
        incident.save()

        AuditLog.objects.create(
            actor=admin_user,
            action="incident.investigation_updated",
            entity_type="IncidentReport",
            entity_id=str(incident.id),
            after_state={"status": incident.status},
        )
        return incident

    @classmethod
    def resolve_incident(
        cls,
        incident: IncidentReport,
        admin_user: User,
        resolution_summary: str,
        outcome_status: str = IncidentReport.STATUS_RESOLVED,
    ) -> IncidentReport:
        """Resolve or dismiss an incident investigation."""
        if not (admin_user.is_superuser or admin_user.has_role(Role.PLATFORM_ADMIN)):
            raise ValidationError("Forbidden: Only administrators can resolve incidents.")

        incident.status = outcome_status
        incident.resolution_summary = resolution_summary
        incident.resolved_at = timezone.now()
        incident.save()

        AuditLog.objects.create(
            actor=admin_user,
            action="incident.resolved",
            entity_type="IncidentReport",
            entity_id=str(incident.id),
            after_state={"status": outcome_status, "resolution": resolution_summary},
        )
        return incident

    @classmethod
    def file_appeal(
        cls,
        incident: IncidentReport,
        appellant: User,
        reason: str,
        additional_evidence: list[str] | None = None,
    ) -> IncidentAppeal:
        """Submit an appeal against an adverse incident resolution."""
        if incident.status not in (IncidentReport.STATUS_RESOLVED, IncidentReport.STATUS_ACTION_REQUIRED):
            raise ValidationError("Appeals can only be submitted against resolved incidents or required actions.")

        with transaction.atomic():
            appeal = IncidentAppeal.objects.create(
                incident=incident,
                appellant=appellant,
                reason=reason,
                additional_evidence=additional_evidence or [],
                status=IncidentAppeal.STATUS_SUBMITTED,
            )
            incident.status = IncidentReport.STATUS_APPEALED
            incident.save(update_fields=["status"])

            AuditLog.objects.create(
                actor=appellant,
                action="incident.appeal_submitted",
                entity_type="IncidentAppeal",
                entity_id=str(appeal.id),
                after_state={"incident_id": str(incident.id)},
            )

        return appeal

    @classmethod
    def decide_appeal(
        cls,
        appeal: IncidentAppeal,
        admin_user: User,
        decision_status: str,
        decision_notes: str,
    ) -> IncidentAppeal:
        """Senior admin adjudication of incident appeal."""
        if not (admin_user.is_superuser or admin_user.has_role(Role.PLATFORM_ADMIN)):
            raise ValidationError("Forbidden: Only administrators can adjudicate appeals.")

        now = timezone.now()
        with transaction.atomic():
            appeal.status = decision_status
            appeal.decision_notes = decision_notes
            appeal.decided_by = admin_user
            appeal.decided_at = now
            appeal.save()

            incident = appeal.incident
            if decision_status == IncidentAppeal.STATUS_OVERTURNED:
                incident.status = IncidentReport.STATUS_DISMISSED
            else:
                incident.status = IncidentReport.STATUS_RESOLVED
            incident.save(update_fields=["status"])

            AuditLog.objects.create(
                actor=admin_user,
                action="incident.appeal_decided",
                entity_type="IncidentAppeal",
                entity_id=str(appeal.id),
                after_state={"decision": decision_status},
            )

        return appeal

    @classmethod
    def impose_restriction(
        cls,
        user: User,
        admin_user: User,
        restriction_type: str,
        reason: str,
        incident: IncidentReport | None = None,
        expires_at: datetime | None = None,
    ) -> AccountRestriction:
        """Impose an administrative restriction.

        Strict rule: A user complaint alone must NEVER result in automatic permanent account banning.
        Permanent bans require human administrator review and recorded audit reason.
        """
        if not (admin_user.is_superuser or admin_user.has_role(Role.PLATFORM_ADMIN)):
            raise ValidationError("Forbidden: Only authorized administrators can impose account restrictions.")

        with transaction.atomic():
            restriction = AccountRestriction.objects.create(
                user=user,
                incident=incident,
                restriction_type=restriction_type,
                reason=reason,
                is_active=True,
                imposed_by=admin_user,
                expires_at=expires_at,
            )

            # Apply state effects if temporary suspension or permanent ban
            if restriction_type in (AccountRestriction.RESTRICTION_TEMPORARY_SUSPENSION, AccountRestriction.RESTRICTION_PERMANENT_BAN):
                user.is_active = False
                user.save(update_fields=["is_active"])
                if hasattr(user, "cook_profile"):
                    user.cook_profile.active_status = False
                    user.cook_profile.save(update_fields=["active_status"])

            AuditLog.objects.create(
                actor=admin_user,
                action="account.restriction_imposed",
                entity_type="AccountRestriction",
                entity_id=str(restriction.id),
                after_state={
                    "user_id": str(user.id),
                    "type": restriction_type,
                    "reason": reason,
                },
            )

        return restriction

    @classmethod
    def lift_restriction(
        cls,
        restriction: AccountRestriction,
        admin_user: User,
        lift_reason: str,
    ) -> AccountRestriction:
        """Lift an imposed restriction and restore user privileges."""
        if not (admin_user.is_superuser or admin_user.has_role(Role.PLATFORM_ADMIN)):
            raise ValidationError("Forbidden: Only administrators can lift account restrictions.")

        with transaction.atomic():
            restriction.is_active = False
            restriction.lifted_by = admin_user
            restriction.lift_reason = lift_reason
            restriction.save(update_fields=["is_active", "lifted_by", "lift_reason"])

            user = restriction.user
            # Reactivate user account if no other active suspensions remain
            other_active = AccountRestriction.objects.filter(
                user=user,
                is_active=True,
                restriction_type__in=[
                    AccountRestriction.RESTRICTION_TEMPORARY_SUSPENSION,
                    AccountRestriction.RESTRICTION_PERMANENT_BAN,
                ],
            ).exists()
            if not other_active:
                user.is_active = True
                user.save(update_fields=["is_active"])
                if hasattr(user, "cook_profile"):
                    user.cook_profile.active_status = True
                    user.cook_profile.save(update_fields=["active_status"])

            AuditLog.objects.create(
                actor=admin_user,
                action="account.restriction_lifted",
                entity_type="AccountRestriction",
                entity_id=str(restriction.id),
                after_state={"is_active": False, "lift_reason": lift_reason},
            )

        return restriction

    @classmethod
    def submit_review(
        cls,
        assignment: CookAssignment,
        reviewer: User,
        rating: int,
        comment: str = "",
        feedback_tags: list[str] | None = None,
    ) -> TwoSidedReview:
        """Submit reciprocal verified review between household resident and cook."""
        if rating < 1 or rating > 5:
            raise ValidationError("Rating must be between 1 and 5 stars.")

        cook_user = assignment.cook.user
        household = assignment.booking.household
        is_cook = reviewer == cook_user
        is_resident = household.members.filter(user=reviewer, is_active=True).exists()

        if not (is_cook or is_resident):
            raise ValidationError("Forbidden: Only the cook or household resident of this visit can submit a review.")

        reviewee = None
        if is_cook:
            primary = household.members.filter(role="primary").first()
            reviewee = primary.user if primary else household.members.first().user
        else:
            reviewee = cook_user

        if TwoSidedReview.objects.filter(assignment=assignment, reviewer=reviewer).exists():
            raise ValidationError("You have already submitted a review for this visit.")

        review = TwoSidedReview.objects.create(
            assignment=assignment,
            reviewer=reviewer,
            reviewee=reviewee,
            rating=rating,
            comment=comment,
            feedback_tags=feedback_tags or [],
            moderation_status=TwoSidedReview.MOD_PUBLISHED,
        )
        return review

    @classmethod
    def moderate_review(
        cls,
        review: TwoSidedReview,
        admin_user: User,
        moderation_status: str,
        moderation_notes: str,
    ) -> TwoSidedReview:
        """Moderation of reviews flagged for profanity, defamation, or policy violations."""
        if not (admin_user.is_superuser or admin_user.has_role(Role.PLATFORM_ADMIN)):
            raise ValidationError("Forbidden: Only administrators can moderate reviews.")

        review.moderation_status = moderation_status
        review.moderation_notes = moderation_notes
        review.moderated_by = admin_user
        review.save(update_fields=["moderation_status", "moderation_notes", "moderated_by"])

        AuditLog.objects.create(
            actor=admin_user,
            action="review.moderated",
            entity_type="TwoSidedReview",
            entity_id=str(review.id),
            after_state={"moderation_status": moderation_status},
        )
        return review
