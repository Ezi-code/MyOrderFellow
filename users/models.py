"""User models module."""

import uuid
import secrets

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from users.managers import UserManager
from base.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    """Custom user model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        """String representation of the user."""
        return self.email

    class Meta:
        """Meta class for User model."""

        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
        ]


class OTP(TimeStampedModel):
    """OTP model for storing one-time passwords."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        """String representation of the OTP."""
        return f"OTP for {self.user.email}: {self.code}"

    class Meta:
        """Meta class for OTP model."""

        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_used"]),
            models.Index(fields=["user"]),
        ]


class UserKYC(TimeStampedModel):
    """user kyc model."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="kyc")
    business_registration_number = models.CharField(max_length=10, unique=True)
    business_address = models.CharField(max_length=10, unique=True)
    contact_person_details = models.CharField(max_length=10, unique=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        """String representation of the user KYC."""
        return self.business_registration_number

    class Meta:
        """Meta class for UserKYC model."""

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["approved"]),
        ]


class WebhookSecret(TimeStampedModel):
    """Store webhook secrets for each company."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="webhook_secret"
    )
    secret_key = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class for WebhookSecret model."""

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"Webhook secret for {self.user.email}"

    def is_expired(self):
        """Check if webhook secret is expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def regenerate(self):
        """Regenerate webhook secret."""
        self.secret_key = f"whsk_{secrets.token_urlsafe(32)}"
        self.expires_at = timezone.now() + timedelta(days=90)
        self.is_active = True
        self.save()
        return self.secret_key
