"""Django admin registration for household models."""

from django.contrib import admin

from apps.households.models import Household, HouseholdMember


class HouseholdMemberInline(admin.TabularInline):
    model = HouseholdMember
    extra = 1
    raw_id_fields = ("user",)


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("apartment_label", "building", "society", "status", "created_at")
    list_filter = ("society", "status")
    search_fields = ("apartment_label", "building__name", "society__name")
    inlines = [HouseholdMemberInline]
    readonly_fields = ("created_at", "updated_at")


@admin.register(HouseholdMember)
class HouseholdMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "household", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("user__email", "household__apartment_label")
    raw_id_fields = ("user", "household")

