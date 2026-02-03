"""user admin."""

from django.contrib import admin
from users.models import UserKYC, User, OTP


@admin.register(UserKYC)
class UserKYCAdmin(admin.ModelAdmin):
    """User KYC admin."""

    list_display = ("business_registration_number", "user", "approved")
    list_filter = ("approved",)
    search_fields = ("user__email", "business_registration_number")
    ordering = ["business_registration_number"]


@admin.register(OTP)
class UserOTPAdmin(admin.ModelAdmin):
    """User OTP admin."""

    list_display = ("code", "user", "is_used", "created_at")
    list_filter = ("is_used",)
    search_fields = ("user__email", "code")
    ordering = ["-created_at"]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """user admin."""

    list_display = ("username", "email")
    list_filter = ("is_active",)
    search_fields = ("username", "email")
    ordering = ("username", "email")
