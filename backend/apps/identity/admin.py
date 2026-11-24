"""Django admin registration for identity models."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.identity.models import Role, User, UserRole


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "phone", "first_name", "last_name", "is_active", "is_staff", "created_at")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "phone", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "created_at")
    search_fields = ("code", "name")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__email", "role__name")

