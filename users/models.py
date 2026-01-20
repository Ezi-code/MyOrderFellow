"""User models module."""

import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from users.managers import UserManager
from base.models import TimeStampedModel


class User(AbstractBaseUser, TimeStampedModel):
    """Custom user model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        """string representation of the user."""
        return self.email


class OTP(TimeStampedModel):
    """OTP model for storing one-time passwords."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        """string representation of the OTP."""
        return f"OTP for {self.user.email}: {self.code}"
