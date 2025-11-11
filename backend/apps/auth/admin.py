from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AuthAuditLog, RefreshToken, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role", "is_staff", "is_superuser"),
            },
        ),
    )


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "revoked", "ip_address")
    list_filter = ("revoked", "created_at")
    search_fields = ("user__email", "ip_address", "user_agent")


@admin.register(AuthAuditLog)
class AuthAuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "email", "successful", "ip_address")
    list_filter = ("action", "successful", "created_at")
    search_fields = ("email", "user__email", "ip_address", "user_agent")
