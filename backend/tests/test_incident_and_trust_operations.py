"""Test suite for Phase 13: Incident Management, Appeals, Restrictions, and Reciprocal Reviews."""

from __future__ import annotations

from datetime import date, datetime, time

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.bookings.models import Booking
from apps.communities.models import Building, Society
from apps.cooks.models import CookProfile
from apps.households.models import Household, HouseholdMember
from apps.scheduling.models import CookAssignment, SchedulePlan
from apps.visits.models import (
    AccountRestriction,
    IncidentAppeal,
    IncidentReport,
    TwoSidedReview,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        email="trustdirector@slotchef.test",
        password="SuperAdminPassword123!",
        first_name="Trust",
        last_name="Director",
    )


@pytest.fixture
def society():
    return Society.objects.create(name="Jaypee Greens", address="Noida Expressway")


@pytest.fixture
def building(society):
    return Building.objects.create(society=society, name="Pavilion Court")


@pytest.fixture
def household(building):
    return Household.objects.create(
        society=building.society,
        building=building,
        apartment_label="Unit 502",
    )


@pytest.fixture
def resident_user(household):
    u = User.objects.create_user(
        email="resident.jaypee@test.com",
        password="Password123!",
        phone="+919811133344",
        first_name="Deepak",
        last_name="Verma",
        is_email_verified=True,
        is_mobile_verified=True,
    )
    HouseholdMember.objects.create(
        household=household,
        user=u,
        role=HouseholdMember.ROLE_PRIMARY,
    )
    return u


@pytest.fixture
def cook_user():
    return User.objects.create_user(
        email="chef.ranveer@test.com",
        password="Password123!",
        phone="+919876511111",
        first_name="Ranveer",
        last_name="Brar",
        is_email_verified=True,
        is_mobile_verified=True,
    )


@pytest.fixture
def cook_profile(cook_user):
    return CookProfile.objects.create(
        user=cook_user,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
    )


@pytest.fixture
def visit_assignment(society, household, cook_profile):
    service_date = date.today()
    plan = SchedulePlan.objects.create(
        society=society,
        service_date=service_date,
        version=1,
    )
    booking = Booking.objects.create(
        household=household,
        requested_by=cook_profile.user,
        service_date=service_date,
        earliest_start_minute=1140,
        latest_finish_minute=1200,
        duration_minutes=60,
        meal_type="dinner",
        status=Booking.STATUS_CONFIRMED,
    )
    start_dt = timezone.make_aware(datetime.combine(service_date, time(19, 0)))
    end_dt = timezone.make_aware(datetime.combine(service_date, time(20, 0)))

    return CookAssignment.objects.create(
        schedule_plan=plan,
        booking=booking,
        cook=cook_profile,
        start_minute=1140,
        end_minute=1200,
        start_at=start_dt,
        end_at=end_dt,
        status=CookAssignment.STATUS_COMPLETED,
    )


@pytest.mark.django_db
def test_two_sided_incident_reporting_with_evidence(api_client, visit_assignment, resident_user, cook_user):
    """Resident reports an incident with photo evidence against assigned cook."""
    api_client.force_authenticate(user=resident_user)

    report_resp = api_client.post(
        f"/api/v1/assignments/{visit_assignment.id}/report-incident",
        data={
            "category": IncidentReport.CAT_HYGIENE,
            "severity": IncidentReport.SEV_MEDIUM,
            "description": "Cook did not use hairnet and left kitchen counter untidy.",
            "evidence_urls": ["https://storage.slotchef.test/evidence/counter_mess.jpg"],
        },
        format="json",
    )
    assert report_resp.status_code == 201
    incident = IncidentReport.objects.get(pk=report_resp.data["id"])
    assert incident.target_user == cook_user
    assert incident.status == IncidentReport.STATUS_REPORTED
    assert len(incident.evidence_urls) == 1


@pytest.mark.django_db
def test_admin_confidential_investigation_and_resolution(api_client, visit_assignment, resident_user, superuser):
    """Admin reviews confidential notes and resolves incident."""
    api_client.force_authenticate(user=resident_user)
    report_resp = api_client.post(
        f"/api/v1/assignments/{visit_assignment.id}/report-incident",
        data={
            "category": IncidentReport.CAT_BEHAVIOR,
            "severity": IncidentReport.SEV_LOW,
            "description": "Minor scheduling miscommunication",
        },
    )
    incident_id = report_resp.data["id"]

    # Admin conducts confidential investigation
    api_client.force_authenticate(user=superuser)
    investigate_resp = api_client.post(
        f"/api/v1/admin/incidents/{incident_id}/investigate",
        data={
            "notes": "Spoke to both resident and cook. Both agreed it was a misunderstanding.",
            "status": IncidentReport.STATUS_UNDER_INVESTIGATION,
        },
    )
    assert investigate_resp.status_code == 200
    assert investigate_resp.data["status"] == "under_investigation"

    # Admin resolves incident
    resolve_resp = api_client.post(
        f"/api/v1/admin/incidents/{incident_id}/resolve",
        data={
            "resolution_summary": "Mutual understanding reached. No sanctions required.",
            "status": IncidentReport.STATUS_RESOLVED,
        },
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.data["status"] == "resolved"


@pytest.mark.django_db
def test_incident_appeal_workflow(api_client, visit_assignment, resident_user, cook_user, superuser):
    """Respondent appeals adverse resolution; Senior admin decides appeal."""
    # Create resolved incident
    incident = IncidentReport.objects.create(
        assignment=visit_assignment,
        reported_by=resident_user,
        target_user=cook_user,
        category=IncidentReport.CAT_PROPERTY_DAMAGE,
        severity=IncidentReport.SEV_HIGH,
        description="Broken blender",
        status=IncidentReport.STATUS_ACTION_REQUIRED,
    )

    # Cook submits appeal
    api_client.force_authenticate(user=cook_user)
    appeal_resp = api_client.post(
        f"/api/v1/incidents/{incident.id}/appeal",
        data={
            "reason": "The blender was already damaged prior to visit; photo taken at check-in confirms this.",
            "additional_evidence": ["https://storage.slotchef.test/evidence/pre_existing_damage.jpg"],
        },
    )
    assert appeal_resp.status_code == 201
    appeal_id = appeal_resp.data["id"]

    incident.refresh_from_db()
    assert incident.status == IncidentReport.STATUS_APPEALED

    # Admin adjudicates appeal and overturns sanction
    api_client.force_authenticate(user=superuser)
    decide_resp = api_client.post(
        f"/api/v1/admin/incidents/appeals/{appeal_id}/decide",
        data={
            "status": IncidentAppeal.STATUS_OVERTURNED,
            "decision_notes": "Pre-visit check-in photos substantiate cook's claim. Sanctions removed.",
        },
    )
    assert decide_resp.status_code == 200

    incident.refresh_from_db()
    assert incident.status == IncidentReport.STATUS_DISMISSED


@pytest.mark.django_db
def test_account_restriction_lifecycle_and_due_process(api_client, cook_user, cook_profile, superuser):
    """Account restrictions require human admin action and cannot auto-ban on complaint alone."""
    assert cook_user.is_active is True
    assert cook_profile.active_status is True

    api_client.force_authenticate(user=superuser)

    # Admin imposes temporary suspension
    restrict_resp = api_client.post(
        "/api/v1/admin/trust/restrictions",
        data={
            "user": str(cook_user.id),
            "restriction_type": AccountRestriction.RESTRICTION_TEMPORARY_SUSPENSION,
            "reason": "Suspended pending investigation of multiple safety complaints.",
        },
    )
    assert restrict_resp.status_code == 201
    restriction_id = restrict_resp.data["id"]

    cook_user.refresh_from_db()
    cook_profile.refresh_from_db()
    assert cook_user.is_active is False
    assert cook_profile.active_status is False

    # Admin lifts restriction
    lift_resp = api_client.post(
        f"/api/v1/admin/trust/restrictions/{restriction_id}/lift",
        data={"lift_reason": "Cleared of safety concerns after investigation."},
    )
    assert lift_resp.status_code == 200

    cook_user.refresh_from_db()
    cook_profile.refresh_from_db()
    assert cook_user.is_active is True
    assert cook_profile.active_status is True


@pytest.mark.django_db
def test_reciprocal_reviews_and_admin_moderation(api_client, visit_assignment, resident_user, cook_user, superuser):
    """Household reviews Cook; Cook reviews Household; Admin moderates inappropriate content."""
    # 1. Resident reviews Cook
    api_client.force_authenticate(user=resident_user)
    r1_resp = api_client.post(
        f"/api/v1/assignments/{visit_assignment.id}/reviews",
        data={
            "rating": 5,
            "comment": "Outstanding paneer butter masala and rotis!",
            "feedback_tags": ["punctual", "delicious", "clean"],
        },
    )
    assert r1_resp.status_code == 201
    review_id = r1_resp.data["id"]

    # Duplicate review prevented
    dup_resp = api_client.post(
        f"/api/v1/assignments/{visit_assignment.id}/reviews",
        data={"rating": 4, "comment": "Another review"},
    )
    assert dup_resp.status_code == 400

    # 2. Cook reviews Household
    api_client.force_authenticate(user=cook_user)
    r2_resp = api_client.post(
        f"/api/v1/assignments/{visit_assignment.id}/reviews",
        data={
            "rating": 5,
            "comment": "Very courteous household with well-organized kitchen utensils.",
            "feedback_tags": ["polite", "well_equipped"],
        },
    )
    assert r2_resp.status_code == 201

    # 3. Admin moderates review
    api_client.force_authenticate(user=superuser)
    mod_resp = api_client.post(
        f"/api/v1/admin/reviews/{review_id}/moderate",
        data={
            "moderation_status": TwoSidedReview.MOD_FLAGGED,
            "moderation_notes": "Flagged for manual verification of review authenticity",
        },
    )
    assert mod_resp.status_code == 200
    assert mod_resp.data["moderation_status"] == "flagged"
