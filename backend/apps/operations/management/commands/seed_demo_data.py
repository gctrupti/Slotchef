"""Management command to populate rich seed demo data for SlotChef."""

from __future__ import annotations

import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.identity.models import User, Role, UserRole
from apps.communities.models import Society, Building
from apps.households.models import Household, HouseholdMember, HouseholdVerificationProfile
from apps.cooks.models import CookProfile, Skill, CookSkill, CookAvailability
from apps.bookings.models import PackagePlan, HouseholdPackageSubscription
from apps.audit.models import AuditLog


class Command(BaseCommand):
    help = "Seed database with realistic demo societies, cooks, households, packages, and audit logs."

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")

        # 1. Roles
        roles = {
            Role.PLATFORM_ADMIN: "Platform Administrator",
            Role.SOCIETY_ADMIN: "Society Administrator",
            Role.COOK: "Cook",
            Role.HOUSEHOLD_MEMBER: "Household Member",
        }
        role_objs = {}
        for code, name in roles.items():
            r, _ = Role.objects.get_or_create(code=code, defaults={"name": name})
            role_objs[code] = r

        # 2. Society & Buildings
        society, _ = Society.objects.get_or_create(
            name="Green Meadows Residency",
            defaults={
                "address": "Outer Ring Road, Bellandur, Bengaluru",
                "timezone": "Asia/Kolkata",
            },
        )
        towers = ["Tower A", "Tower B", "Tower C", "Tower D"]
        building_objs = {}
        for t in towers:
            b, _ = Building.objects.get_or_create(society=society, name=t)
            building_objs[t] = b

        # 3. Platform Admin User
        admin_email = "admin@greenmeadows.ops"
        admin_user = User.objects.filter(email=admin_email).first()
        if not admin_user:
            admin_user = User.objects.create_user(
                email=admin_email,
                password="Admin1234!",
                first_name="Platform",
                last_name="Commander",
                is_staff=True,
                is_superuser=True,
                is_email_verified=True,
                is_mobile_verified=True,
            )
        UserRole.objects.get_or_create(user=admin_user, role=role_objs[Role.PLATFORM_ADMIN])
        UserRole.objects.get_or_create(user=admin_user, role=role_objs[Role.SOCIETY_ADMIN])

        # 4. Resident User & Household
        resident_email = "priya.sharma@example.com"
        resident_user = User.objects.filter(email=resident_email).first()
        if not resident_user:
            resident_user = User.objects.create_user(
                email=resident_email,
                password="Resident1234!",
                first_name="Priya",
                last_name="Sharma",
                phone="+919876543210",
                is_email_verified=True,
                is_mobile_verified=True,
            )
        UserRole.objects.get_or_create(user=resident_user, role=role_objs[Role.HOUSEHOLD_MEMBER])

        household, _ = Household.objects.get_or_create(
            society=society,
            building=building_objs["Tower B"],
            apartment_label="402",
            defaults={"status": Household.STATUS_ACTIVE},
        )
        HouseholdMember.objects.get_or_create(
            household=household,
            user=resident_user,
            defaults={"role": HouseholdMember.ROLE_PRIMARY, "is_active": True},
        )
        HouseholdVerificationProfile.objects.get_or_create(
            household=household,
            defaults={
                "status": HouseholdVerificationProfile.STATUS_VERIFIED,
                "society_noc_verified": True,
                "possession_proof_type": HouseholdVerificationProfile.PROOF_RENTAL_AGREEMENT,
                "possession_proof_reference": "https://docs.slotchef.test/proofs/hh-402-noc.pdf",
            },
        )

        # 5. Skills
        skill_catalog = [
            ("south_indian", "South Indian Specialization"),
            ("north_indian", "North Indian Homestyle"),
            ("gujarati_thali", "Gujarati Thali"),
            ("punjabi_specialty", "Punjabi Dhaba Specialties"),
            ("basic_breakfast", "Quick Morning Tiffin"),
        ]
        skill_objs = {}
        for code, name in skill_catalog:
            s, _ = Skill.objects.get_or_create(code=code, defaults={"name": name})
            skill_objs[code] = s

        # 6. Cook Fleet
        cook_data = [
            ("meenakshi@cook.test", "Meenakshi", "Iyer", "+919876543201", ["south_indian", "basic_breakfast"]),
            ("ramesh@cook.test", "Rameshwar", "Prasad", "+919876543202", ["north_indian", "gujarati_thali", "basic_breakfast"]),
            ("sunita@cook.test", "Sunita", "Devi", "+919876543203", ["north_indian", "punjabi_specialty"]),
        ]

        for email, fn, ln, ph, skills in cook_data:
            c_user = User.objects.filter(email=email).first()
            if not c_user:
                c_user = User.objects.create_user(
                    email=email,
                    password="Chef1234!",
                    first_name=fn,
                    last_name=ln,
                    phone=ph,
                    is_email_verified=True,
                    is_mobile_verified=True,
                )
            UserRole.objects.get_or_create(user=c_user, role=role_objs[Role.COOK])

            cp, _ = CookProfile.objects.get_or_create(
                user=c_user,
                defaults={
                    "verification_status": CookProfile.VERIFICATION_VERIFIED,
                    "active_status": True,
                    "max_daily_minutes": 480,
                    "max_daily_visits": 6,
                },
            )
            cp.societies.add(society)

            for sk in skills:
                CookSkill.objects.get_or_create(cook=cp, skill=skill_objs[sk])

            # Weekly availability: Mon-Sat 07:00-14:00 (420 to 840) and 17:00-21:00 (1020 to 1260)
            for w in range(0, 6):
                CookAvailability.objects.get_or_create(
                    cook=cp,
                    weekday=w,
                    start_minute=420,
                    end_minute=840,
                )
                CookAvailability.objects.get_or_create(
                    cook=cp,
                    weekday=w,
                    start_minute=1020,
                    end_minute=1260,
                )

        # 7. Package Plans & Active Household Subscription
        plan_12, _ = PackagePlan.objects.get_or_create(
            code="12_slot_flexi",
            defaults={
                "name": "12-Slot Flexi Bi-Weekly",
                "plan_type": PackagePlan.PLAN_CUSTOM,
                "total_visits": 12,
                "validity_days": 30,
                "price_minor_units": 280000,
                "is_active": True,
            },
        )
        PackagePlan.objects.get_or_create(
            code="weekly_routine",
            defaults={
                "name": "Weekly Routine (6 Visits)",
                "plan_type": PackagePlan.PLAN_WEEKLY,
                "total_visits": 6,
                "validity_days": 7,
                "price_minor_units": 150000,
                "is_active": True,
            },
        )
        PackagePlan.objects.get_or_create(
            code="monthly_gourmet",
            defaults={
                "name": "Monthly Gourmet Suite (24 Visits)",
                "plan_type": PackagePlan.PLAN_MONTHLY,
                "total_visits": 24,
                "validity_days": 30,
                "price_minor_units": 520000,
                "is_active": True,
            },
        )

        today = timezone.now().date()
        HouseholdPackageSubscription.objects.get_or_create(
            household=household,
            package_plan=plan_12,
            defaults={
                "status": HouseholdPackageSubscription.STATUS_ACTIVE,
                "start_date": today - datetime.timedelta(days=7),
                "end_date": today + datetime.timedelta(days=23),
                "total_entitled_visits": 12,
                "used_visits": 4,
            },
        )

        # 8. Seed Audit Log Events
        AuditLog.objects.get_or_create(
            action="schedule.plan_committed",
            entity_type="SchedulePlan",
            entity_id="plan-demo-001",
            defaults={
                "actor": admin_user,
                "reason": "Initial Google OR-Tools CP-SAT multi-track schedule published for Green Meadows.",
                "after_state": {"status": "COMMITTED", "version": 1, "shifts_count": 68},
            },
        )
        AuditLog.objects.get_or_create(
            action="household.verification_reviewed",
            entity_type="HouseholdVerificationProfile",
            entity_id=str(household.id),
            defaults={
                "actor": admin_user,
                "reason": "Residency proof verified with society administration NOC for Tower B 402.",
                "after_state": {"status": "VERIFIED", "society_noc_verified": True},
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo database successfully seeded!"))
