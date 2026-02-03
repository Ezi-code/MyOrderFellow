"""user authentication utils."""

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets

from users.models import OTP, WebhookSecret, UserKYC
from django_tasks import task
from random import randint


def generate_otp(user) -> str:
    """
    Generate a 6-digit OTP.

    The method should generate a random 6-digit OTP code
    that will be sent to the user through sent_otp_via_mail task.
    """
    otp_code = str(randint(100000, 999999)).zfill(6)
    if OTP.objects.filter(code=otp_code, is_used=False, user=user).exists():
        return "An active OTP already exists for this user."

    OTP.objects.create(code=otp_code, user=user)
    return send_otp_via_email.enqueue(user.email, otp_code)


@task(priority=1, queue_name="high_priority")
def send_otp_via_email(email, otp):
    """Send OTP to the user's email address."""
    subject = "Your One-Time Password (OTP)"
    message = (
        f"Your OTP is: {otp}. "
        f"Click on the link: http://localhost:8000/api/v1/users/verify-otp/ to verify your account."
    )

    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)


@task(priority=1, queue_name="data_sync")
def activate_user_account(otp_id):
    """
    Activate the user's account after the user
    has verified their otp received via email.
    """
    try:
        otp = OTP.objects.get(pk=otp_id)
        user = otp.user
        user.is_verified = True
        user.is_active = True
        user.save()
    except OTP.DoesNotExist:
        pass


def get_or_create_webhook_secret(user):
    """
    Get webhook secret for a user.

    If expired, regenerate it.
    If none exists but user is KYC verified, create one.

    Returns:
        tuple: (secret_key, created) or (None, False) if user not KYC verified
    """
    try:
        UserKYC.objects.get(user=user, approved=True)
    except UserKYC.DoesNotExist:
        return None, False

    webhook_secret = WebhookSecret.objects.filter(user=user).first()

    if webhook_secret:
        # Check if expired
        if webhook_secret.is_expired():
            secret_key = webhook_secret.regenerate()
            return secret_key, False
        return webhook_secret.secret_key, False

    # Create new secret
    secret_key = f"whsk_{secrets.token_urlsafe(32)}"
    WebhookSecret.objects.create(
        user=user,
        secret_key=secret_key,
        is_active=True,
        expires_at=timezone.now() + timedelta(days=90),
    )
    return secret_key, True
