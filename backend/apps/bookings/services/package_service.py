"""Package management, subscription lifecycle, and optimizer-integrated visit scheduling."""

from __future__ import annotations

import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.bookings.models import (
    Booking,
    HouseholdPackageSubscription,
    PackageBookingLink,
    PackagePlan,
)
from apps.cooks.models import CookProfile
from apps.finance.services.pricing_calculator import PricingCalculatorService
from apps.households.models import Household
from apps.identity.models import User
from apps.scheduling.services.orchestrator import SchedulingOrchestrator


class PackageService:
    """Orchestrates household package enrollment, booking generation, pause/cancel, and scheduling."""

    @classmethod
    def subscribe_household(
        cls,
        household: Household,
        package_plan: PackagePlan,
        start_date: datetime.date,
        preferred_weekdays: list[int] | None = None,
        preferred_start_minute: int = 450,
        preferred_end_minute: int = 540,
        preferred_cook_id: str | None = None,
        auto_renew: bool = False,
        actor: User | None = None,
    ) -> tuple[HouseholdPackageSubscription, list[Booking]]:
        """Enroll household in a package and generate schedule through CP-SAT engine."""
        if not package_plan.is_active:
            raise ValidationError(f"Package plan '{package_plan.name}' is inactive.")

        end_date = start_date + datetime.timedelta(days=package_plan.validity_days)

        # Default weekdays (e.g. Mon-Fri: 0..4) if unspecified
        weekdays = preferred_weekdays or list(range(min(7, package_plan.visit_frequency_per_week)))

        pref_cook = None
        if preferred_cook_id:
            pref_cook = CookProfile.objects.filter(id=preferred_cook_id).first()

        with transaction.atomic():
            subscription = HouseholdPackageSubscription.objects.create(
                household=household,
                package_plan=package_plan,
                status=HouseholdPackageSubscription.STATUS_ACTIVE,
                total_entitled_visits=package_plan.total_visits,
                preferred_weekdays=weekdays,
                preferred_start_minute=preferred_start_minute,
                preferred_end_minute=preferred_end_minute,
                preferred_cook=pref_cook,
                start_date=start_date,
                end_date=end_date,
                auto_renew=auto_renew,
            )

            # Generate target dates matching preferred weekdays up to total_visits
            target_dates: list[datetime.date] = []
            cur_date = start_date
            while cur_date <= end_date and len(target_dates) < package_plan.total_visits:
                if cur_date.weekday() in weekdays:
                    target_dates.append(cur_date)
                cur_date += datetime.timedelta(days=1)

            # If not enough weekday matches within window, fill remaining valid days
            cur_date = start_date
            while cur_date <= end_date and len(target_dates) < package_plan.total_visits:
                if cur_date not in target_dates:
                    target_dates.append(cur_date)
                cur_date += datetime.timedelta(days=1)

            target_dates.sort()

            # Create individual Booking requests
            created_bookings: list[Booking] = []
            for s_date in target_dates:
                b = Booking.objects.create(
                    household=household,
                    requested_by=actor or household.members.first().user,
                    service_date=s_date,
                    earliest_start_minute=preferred_start_minute,
                    latest_finish_minute=preferred_end_minute,
                    duration_minutes=package_plan.default_duration_minutes,
                    meal_type=package_plan.meal_type,
                    preferred_cook_id=pref_cook.id if pref_cook else None,
                    status=Booking.STATUS_PENDING,
                    notes=f"Auto-generated for package '{package_plan.name}'",
                )
                PricingCalculatorService.calculate_price_breakdown(booking=b, persist=True)
                PackageBookingLink.objects.create(subscription=subscription, booking=b)
                created_bookings.append(b)

            AuditLog.objects.create(
                actor=actor,
                action="PACKAGE_SUBSCRIBE",
                entity_type="HouseholdPackageSubscription",
                entity_id=str(subscription.id),
                after_state={
                    "plan": package_plan.code,
                    "total_visits": package_plan.total_visits,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                },
            )

        # Execute scheduling optimization for each service date without bypassing constraints
        orchestrator = SchedulingOrchestrator()
        for s_date in set(target_dates):
            orchestrator.run_and_commit(
                society=household.society,
                service_date=s_date,
                actor=actor,
                correlation_id=f"pkg-sub-{subscription.id}-{s_date}",
            )

        # Refresh bookings with finalized optimizer statuses
        refreshed_bookings = list(Booking.objects.filter(id__in=[b.id for b in created_bookings]))
        return subscription, refreshed_bookings

    @classmethod
    def pause_subscription(
        cls,
        subscription: HouseholdPackageSubscription,
        pause_days: int,
        actor: User | None = None,
    ) -> HouseholdPackageSubscription:
        """Pause subscription, extending validity end date by paused duration."""
        if subscription.status != HouseholdPackageSubscription.STATUS_ACTIVE:
            raise ValidationError(f"Cannot pause subscription with status '{subscription.status}'.")

        max_pause = subscription.package_plan.max_pause_days
        if pause_days > max_pause or pause_days <= 0:
            raise ValidationError(f"Pause duration must be between 1 and {max_pause} days.")

        with transaction.atomic():
            now = timezone.now()
            resume_date = now.date() + datetime.timedelta(days=pause_days)
            new_end_date = subscription.end_date + datetime.timedelta(days=pause_days)

            # Cancel or postpone pending bookings falling strictly inside the pause window
            pause_start = now.date()
            pause_end = resume_date
            affected_links = PackageBookingLink.objects.filter(
                subscription=subscription,
                booking__service_date__gte=pause_start,
                booking__service_date__lte=pause_end,
                booking__status=Booking.STATUS_PENDING,
            ).select_related("booking")

            for link in affected_links:
                link.booking.status = Booking.STATUS_CANCELLED
                link.booking.notes += f" [Cancelled due to subscription pause until {resume_date}]"
                link.booking.save(update_fields=["status", "notes", "updated_at"])

            subscription.status = HouseholdPackageSubscription.STATUS_PAUSED
            subscription.paused_at = now
            subscription.pause_resumes_at = resume_date
            subscription.end_date = new_end_date
            subscription.save(update_fields=["status", "paused_at", "pause_resumes_at", "end_date", "updated_at"])

            AuditLog.objects.create(
                actor=actor,
                action="PACKAGE_PAUSE",
                entity_type="HouseholdPackageSubscription",
                entity_id=str(subscription.id),
                after_state={
                    "status": subscription.status,
                    "pause_resumes_at": str(resume_date),
                    "new_end_date": str(new_end_date),
                },
            )

        return subscription

    @classmethod
    def resume_subscription(
        cls,
        subscription: HouseholdPackageSubscription,
        actor: User | None = None,
    ) -> HouseholdPackageSubscription:
        """Resume an active paused subscription."""
        if subscription.status != HouseholdPackageSubscription.STATUS_PAUSED:
            raise ValidationError(f"Cannot resume subscription with status '{subscription.status}'.")

        with transaction.atomic():
            subscription.status = HouseholdPackageSubscription.STATUS_ACTIVE
            subscription.paused_at = None
            subscription.pause_resumes_at = None
            subscription.save(update_fields=["status", "paused_at", "pause_resumes_at", "updated_at"])

            AuditLog.objects.create(
                actor=actor,
                action="PACKAGE_RESUME",
                entity_type="HouseholdPackageSubscription",
                entity_id=str(subscription.id),
                after_state={"status": subscription.status},
            )

        return subscription

    @classmethod
    def cancel_subscription(
        cls,
        subscription: HouseholdPackageSubscription,
        reason: str = "",
        actor: User | None = None,
    ) -> HouseholdPackageSubscription:
        """Cancel subscription and cancel any future unstarted bookings."""
        with transaction.atomic():
            subscription.status = HouseholdPackageSubscription.STATUS_CANCELLED
            subscription.save(update_fields=["status", "updated_at"])

            # Cancel remaining future unstarted bookings
            today = timezone.now().date()
            future_links = PackageBookingLink.objects.filter(
                subscription=subscription,
                booking__service_date__gte=today,
                booking__status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
            ).select_related("booking")

            cancelled_count = 0
            for link in future_links:
                link.booking.status = Booking.STATUS_CANCELLED
                link.booking.notes += f" [Cancelled with subscription: {reason}]"
                link.booking.save(update_fields=["status", "notes", "updated_at"])
                cancelled_count += 1

            subscription.cancelled_visits += cancelled_count
            subscription.save(update_fields=["cancelled_visits", "updated_at"])

            AuditLog.objects.create(
                actor=actor,
                action="PACKAGE_CANCEL",
                entity_type="HouseholdPackageSubscription",
                entity_id=str(subscription.id),
                reason=reason,
                after_state={"status": subscription.status, "cancelled_visits": subscription.cancelled_visits},
            )

        return subscription

    @classmethod
    def reschedule_package_visit(
        cls,
        booking: Booking,
        new_date: datetime.date,
        new_start_minute: int,
        new_finish_minute: int,
        actor: User | None = None,
    ) -> Booking:
        """Reschedule a package visit within the package's active validity window."""
        if not hasattr(booking, "package_link"):
            raise ValidationError("Booking is not part of a package subscription.")

        link = booking.package_link
        sub = link.subscription

        if sub.status != HouseholdPackageSubscription.STATUS_ACTIVE:
            raise ValidationError(f"Cannot reschedule visit under inactive subscription [{sub.status}].")

        if not (sub.start_date <= new_date <= sub.end_date):
            raise ValidationError(
                f"New service date {new_date} is outside subscription validity window ({sub.start_date} to {sub.end_date})."
            )

        with transaction.atomic():
            orig_date = booking.service_date
            booking.service_date = new_date
            booking.earliest_start_minute = new_start_minute
            booking.latest_finish_minute = new_finish_minute
            booking.status = Booking.STATUS_PENDING
            booking.save(update_fields=["service_date", "earliest_start_minute", "latest_finish_minute", "status", "updated_at"])

            link.is_rescheduled = True
            link.original_service_date = orig_date
            link.save(update_fields=["is_rescheduled", "original_service_date"])

        # Re-run CP-SAT optimization for the new date
        orchestrator = SchedulingOrchestrator()
        orchestrator.run_and_commit(
            society=booking.household.society,
            service_date=new_date,
            actor=actor,
            correlation_id=f"pkg-reschedule-{booking.id}-{new_date}",
        )
        booking.refresh_from_db()
        return booking
