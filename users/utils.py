"""user authentication utils."""

from django.core.mail import send_mail
from django.conf import settings
from users.models import OTP


def generate_otp(user) -> str:
    """Generate a 6-digit OTP."""
    from random import randint

    otp = randint(100000, 999999)
    try:
        # this should not work if the otp is already used
        if OTP.objects.filter(code=str(otp).zfill(6)).exists():
            return "An active OTP already exists for this user."
        OTP.objects.create(code=str(otp).zfill(6), user=user)
    except Exception as e:
        return str(e)
    return send_otp_via_email(user.email, str(otp).zfill(6))


def send_otp_via_email(email, otp):
    """Send OTP to the user's email address."""
    subject = "Your One-Time Password (OTP)"
    message = f"Your OTP is: {otp}. click on the link: http://localhost:8000/api/users/verify-otp/?email={email}"
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)
