"""API integration tests for Visit lifecycle (check-in, start, complete) and backup workflows."""

from __future__ import annotations

import datetime

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.bookings.models import Booking
from apps.communities.models import Building, Society
from apps.cooks.models import (
    CookAvailability,
    CookProfile,
    CookSkill,
    CookWorkPolicy,
    Skill,
)
from apps.households.models import Household, HouseholdMember
from apps.identity.models import Role, User
from apps.scheduling.models import CookAssignment
from apps.visits.models import BackupProposal, IncidentReport, VisitEvent


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def visit_setup():
    society = Society.objects.create(name="Palm Heights", address="123 Palm Ave", timezone="UTC")
    building = Building.objects.create(society=society, name="Tower A")

    user_a = User.objects.create_user(email="resident.a@example.com", password="PassWord123!")
    hh_a = Household.objects.create(society=society, building=building, apartment_label="A-101")
    HouseholdMember.objects.create(household=hh_a, user=user_a, role=HouseholdMember.ROLE_PRIMARY, is_active=True)

    skill = Skill.objects.create(code="basic_breakfast", name="Basic Breakfast")

    # Cook 1: Alexa
    cook_user_1 = User.objects.create_user(email="alexa.cook@example.com", password="PassWord123!", first_name="Alexa")
    role_cook, _ = Role.objects.get_or_create(code=Role.COOK)
    cook_user_1.user_roles.create(role=role_cook)
    alexa = CookProfile.objects.create(
        user=cook_user_1,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
        active_status=True,
    )
    alexa.societies.add(society)
    CookSkill.objects.create(cook=alexa, skill=skill, proficiency_level="expert")
    CookWorkPolicy.objects.create(cook=alexa)

    # Cook 2: Bob (Backup cook)
    cook_user_2 = User.objects.create_user(email="bob.backup@example.com", password="PassWord123!", first_name="Bob")
    cook_user_2.user_roles.create(role=role_cook)
    bob = CookProfile.objects.create(
        user=cook_user_2,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
        active_status=True,
    )
    bob.societies.add(society)
    CookSkill.objects.create(cook=bob, skill=skill, proficiency_level="intermediate")
    CookWorkPolicy.objects.create(cook=bob)

    service_date = datetime.date(2027, 2, 15)  # Monday

    # Both cooks available Monday mornings
    CookAvailability.objects.create(cook=alexa, weekday=0, start_minute=420, end_minute=660)
    CookAvailability.objects.create(cook=bob, weekday=0, start_minute=420, end_minute=660)

    return {
        "society": society,
        "hh_a": hh_a,
        "user_a": user_a,
        "alexa": alexa,
        "bob": bob,
        "cook_user_1": cook_user_1,
        "cook_user_2": cook_user_2,
        "service_date": service_date,
    }


@pytest.mark.django_db
def test_visit_lifecycle_checkin_start_complete(
    visit_setup: dict,
) -> None:
    """Full lifecycle: check-in -> start -> complete with status updates and audit events."""
    hh_a = visit_setup["hh_a"]
    user_a = visit_setup["user_a"]
    service_date = visit_setup["service_date"]

    # 1. Household books visit
    client_res = APIClient()
    client_res.force_authenticate(user=user_a)
    payload = {
        "service_date": str(service_date),
        "earliest_start": "07:30",
        "latest_finish": "08:30",
        "estimated_duration_minutes": 45,
        "required_skills": ["basic_breakfast"],
    }
    resp = client_res.post(f"/api/v1/households/{hh_a.id}/bookings", payload, format="json")
    assert resp.status_code == status.HTTP_201_CREATED
    booking_id = resp.json()["id"]

    assignment = CookAssignment.objects.get(booking_id=booking_id)
    assert assignment.status == CookAssignment.STATUS_CONFIRMED

    # 2. Cook checks in
    client_cook = APIClient()
    client_cook.force_authenticate(user=assignment.cook.user)

    checkin_resp = client_cook.post(f"/api/v1/assignments/{assignment.id}/check-in")
    assert checkin_resp.status_code == status.HTTP_200_OK
    assert VisitEvent.objects.filter(assignment=assignment, event_type=VisitEvent.TYPE_CHECK_IN).exists()

    # 3. Cook starts visit
    start_resp = client_cook.post(f"/api/v1/assignments/{assignment.id}/start")
    assert start_resp.status_code == status.HTTP_200_OK
    assignment.refresh_from_db()
    assert assignment.status == CookAssignment.STATUS_STARTED
    booking = Booking.objects.get(id=booking_id)
    assert booking.status == Booking.STATUS_IN_PROGRESS

    # 4. Cook completes visit
    complete_resp = client_cook.post(f"/api/v1/assignments/{assignment.id}/complete")
    assert complete_resp.status_code == status.HTTP_200_OK
    assignment.refresh_from_db()
    assert assignment.status == CookAssignment.STATUS_COMPLETED
    booking.refresh_from_db()
    assert booking.status == Booking.STATUS_COMPLETED


@pytest.mark.django_db
def test_cook_absence_incident_triggers_backup_cook_reoptimization(
    visit_setup: dict,
) -> None:
    """When assigned cook reports absence, original assignment is preserved as REPLACED,
    re-optimization runs, and backup cook Bob is automatically proposed and confirmed.
    """
    hh_a = visit_setup["hh_a"]
    user_a = visit_setup["user_a"]
    service_date = visit_setup["service_date"]

    # 1. Booking assigned to Alexa
    client_res = APIClient()
    client_res.force_authenticate(user=user_a)
    payload = {
        "service_date": str(service_date),
        "earliest_start": "07:30",
        "latest_finish": "08:30",
        "estimated_duration_minutes": 45,
        "required_skills": ["basic_breakfast"],
    }
    resp = client_res.post(f"/api/v1/households/{hh_a.id}/bookings", payload, format="json")
    booking_id = resp.json()["id"]

    orig_assignment = CookAssignment.objects.get(booking_id=booking_id)
    assert orig_assignment.status == CookAssignment.STATUS_CONFIRMED

    assigned_cook = orig_assignment.cook
    backup_cook = visit_setup["bob"] if assigned_cook == visit_setup["alexa"] else visit_setup["alexa"]

    # 2. Assigned cook reports absence
    client_cook = APIClient()
    client_cook.force_authenticate(user=assigned_cook.user)
    incident_resp = client_cook.post(
        f"/api/v1/assignments/{orig_assignment.id}/report-incident",
        {
            "category": IncidentReport.CAT_ABSENCE,
            "severity": IncidentReport.SEV_HIGH,
            "description": "Vehicle breakdown, unable to reach Palm Heights this morning.",
        },
        format="json",
    )
    assert incident_resp.status_code == status.HTTP_201_CREATED

    # 3. Verify original assignment is preserved as REPLACED
    orig_assignment.refresh_from_db()
    assert orig_assignment.status == CookAssignment.STATUS_REPLACED
    assert "Vehicle breakdown" in orig_assignment.replacement_reason
    assert orig_assignment.replaced_by is not None

    # 4. Verify backup proposal created and accepted with backup cook
    backup_proposal = BackupProposal.objects.get(original_assignment=orig_assignment)
    assert backup_proposal.status == BackupProposal.STATUS_ACCEPTED
    assert backup_proposal.proposed_cook == backup_cook

    # 5. Verify replacement assignment is confirmed with backup cook
    new_assignment = orig_assignment.replaced_by
    assert new_assignment.cook == backup_cook
    assert new_assignment.status == CookAssignment.STATUS_CONFIRMED
    assert new_assignment.schedule_plan.version > orig_assignment.schedule_plan.version
