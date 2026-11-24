"""Django admin registration for cook capacity and policy models."""

from django.contrib import admin

from apps.cooks.models import (
    CookAvailability,
    CookBreak,
    CookLeave,
    CookProfile,
    CookSkill,
    CookWorkPolicy,
    Skill,
)


class CookSkillInline(admin.TabularInline):
    model = CookSkill
    extra = 1


class CookAvailabilityInline(admin.TabularInline):
    model = CookAvailability
    extra = 1


class CookBreakInline(admin.TabularInline):
    model = CookBreak
    extra = 1


class CookWorkPolicyInline(admin.StackedInline):
    model = CookWorkPolicy
    can_delete = False


@admin.register(CookProfile)
class CookProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "verification_status",
        "active_status",
        "max_daily_minutes",
        "max_daily_visits",
        "created_at",
    )
    list_filter = ("verification_status", "active_status", "societies")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    raw_id_fields = ("user",)
    filter_horizontal = ("societies",)
    inlines = [CookWorkPolicyInline, CookSkillInline, CookAvailabilityInline, CookBreakInline]
    readonly_fields = ("created_at", "updated_at")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "created_at")
    search_fields = ("code", "name")


@admin.register(CookSkill)
class CookSkillAdmin(admin.ModelAdmin):
    list_display = ("cook", "skill", "proficiency_level", "created_at")
    list_filter = ("proficiency_level", "skill")
    search_fields = ("cook__user__email", "skill__name")


@admin.register(CookAvailability)
class CookAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("cook", "weekday", "specific_date", "start_minute", "end_minute", "availability_type")
    list_filter = ("availability_type", "weekday")
    search_fields = ("cook__user__email",)


@admin.register(CookBreak)
class CookBreakAdmin(admin.ModelAdmin):
    list_display = ("cook", "start_minute", "end_minute", "recurring_weekday", "specific_date", "reason")
    search_fields = ("cook__user__email", "reason")


@admin.register(CookLeave)
class CookLeaveAdmin(admin.ModelAdmin):
    list_display = ("cook", "start_date", "end_date", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("cook__user__email", "reason")


@admin.register(CookWorkPolicy)
class CookWorkPolicyAdmin(admin.ModelAdmin):
    list_display = ("cook", "max_consecutive_visits", "max_daily_minutes", "buffer_between_visits_minutes")

