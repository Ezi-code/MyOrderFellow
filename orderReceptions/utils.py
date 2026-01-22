"""order receptions utils."""

from django.core.mail import send_mail

from rest_framework import settings
from django.tasks import task


@task(priority=1, queue_name="high_priority")
def send_order_received_confirmation(order):
    """send order confirmation email to customer."""
    subject = "Order Received"
    message = (
        f"Hello {order.customer_details.name}, Your order: {order.id} "
        f"is received successfully!"
    )

    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [order.customer_details.email]
    send_mail(subject, message, email_from, recipient_list)
