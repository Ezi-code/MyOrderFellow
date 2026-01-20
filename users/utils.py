"""user authentication utils."""

from django.core.mail import send_mail
from django.conf import settings
from users.models import OTP
from django.tasks import task
from random import randint


def generate_otp(user) -> str:
    """Generate a 6-digit OTP.
    The method should generate a random 6-digit OTP code
    that will be sent to the user through sent_otp_via_mail task."""

    otp = randint(100000, 999999)
    try:
        if OTP.objects.filter(code=str(otp).zfill(6)).exists():
            return "An active OTP already exists for this user."
        OTP.objects.create(code=str(otp).zfill(6), user=user)
    except Exception as e:
        return str(e)
    return send_otp_via_email.enqueue(user.email, str(otp).zfill(6))


@task(priority=1, queue_name="high_priority")
def send_otp_via_email(email, otp):
    """Send OTP to the user's email address."""
    subject = "Your One-Time Password (OTP)"
    message = f"Your OTP is: {otp}. Click on the link: http://localhost:8000/api/v1/users/verify-otp/?emal={email} to verify your account."

    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)


@task(priority=1, queue_name="data_sync")
def activate_user_account(otp_id):
    """Activate the user's account after the user
    has verified their otp received via email."""

    try:
        user = OTP.objects.get(pk=otp_id).user
        user.is_active = True
        user.save()
    except Exception as e:
        raise str(e)
