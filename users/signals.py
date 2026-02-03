"""User signals module."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import secrets

from users.models import UserKYC, WebhookSecret


@receiver(post_save, sender=UserKYC)
def generate_webhook_secret_on_kyc_approval(sender, instance, created, **kwargs):
    """
    Generate webhook secret when KYC is approved.
    Only generates if KYC is newly approved.
    """
    # Only proceed if KYC is approved
    if not instance.approved:
        return

    # Check if secret already exists
    webhook_secret = WebhookSecret.objects.filter(user=instance.user).first()

    if webhook_secret:
        # Secret exists, regenerate it if expired
        if webhook_secret.is_expired():
            webhook_secret.regenerate()
    else:
        # activate user account
        instance.user.is_active = True
        instance.user.save()

        # Create new webhook secret
        secret_key = f"whsk_{secrets.token_urlsafe(32)}"
        WebhookSecret.objects.create(
            user=instance.user,
            secret_key=secret_key,
            is_active=True,
            expires_at=timezone.now() + timedelta(days=90),
        )
