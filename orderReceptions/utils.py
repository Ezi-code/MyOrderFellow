"""order receptions utils."""

import logging
import time
from django.core.mail import send_mail

from django.conf import settings
from django_tasks import task

from orderReceptions.models import OrderDetails

logger = logging.getLogger(__name__)


def send_email_with_retry(subject, message, email_from, recipient_list, retries=3, delay=5):
    """Send email with retry mechanism."""
    for attempt in range(retries):
        try:
            return send_mail(subject, message, email_from, recipient_list)
        except Exception as err:
            if attempt < retries - 1:
                logger.warning(
                    f"Email sending failed. Retrying in {delay} seconds. Error: {err}"
                )
                time.sleep(delay)
            else:
                raise err


@task(queue_name="high_priority")
def send_order_received_confirmation(order_id):
    """send order confirmation email to customer."""
    from orderReceptions.models import OrderDetails

    try:
        order = OrderDetails.objects.get(pk=order_id)
    except OrderDetails.DoesNotExist:
        return

    subject = "Order Received"
    message = (
        f"Hello {order.customer_details.name}, Your order: {order.id} "
        f"is received successfully!"
    )

    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [order.customer_details.email]
    send_email_with_retry(subject, message, email_from, recipient_list)


@task(queue_name="high_priority")
def send_order_status_update_email(order_id):
    """send order status update email to customer."""
    from orderReceptions.models import OrderStatusHistory

    order_instance = OrderDetails.objects.get(pk=order_id)
    try:
        OrderStatusHistory.objects.create(
            order=order_instance, status=order_instance.tracking_status
        ).order
    except OrderStatusHistory.DoesNotExist:
        return

    subject = "Order Status"
    message = (
        f"Hello {order_instance.customer_details.name}, Your order with id: {order_instance.id} "
        f"status is now {str(order_instance.tracking_status)}"
    )
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [order_instance.customer_details.email]
    send_email_with_retry(subject, message, email_from, recipient_list)


@task(queue_name="high_priority")
def send_order_deleted_email(order_id, customer_email):
    """send order deleted email to customer."""
    subject = "Order Deleted"
    message = f"Order {order_id} has been deleted!"
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [customer_email]
    send_email_with_retry(subject, message, email_from, recipient_list)
