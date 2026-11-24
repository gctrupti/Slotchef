"""Django admin registration for community models."""

from django.contrib import admin

from apps.communities.models import Apartment, Building, Society


@admin.register(Society)
class SocietyAdmin(admin.ModelAdmin):
    list_display = ("name", "timezone", "status", "created_at")
    list_filter = ("status", "timezone")
    search_fields = ("name", "address")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("name", "society", "code", "created_at")
    list_filter = ("society",)
    search_fields = ("name", "code", "society__name")


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ("number", "building", "floor", "created_at")
    list_filter = ("building__society", "building")
    search_fields = ("number", "building__name")

