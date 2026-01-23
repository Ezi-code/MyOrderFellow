"""order receptions utils."""

from django.core.mail import send_mail

from django.conf import settings
from django.tasks import task


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
    send_mail(subject, message, email_from, recipient_list)


@task(queue_name="high_priority")
def send_order_status_update_email(order_id):
    """send order status update email to customer."""
    from orderReceptions.models import OrderDetails

    try:
        order = OrderDetails.objects.get(pk=order_id)
    except OrderDetails.DoesNotExist:
        return

    subject = "Order Status"
    message = (
        f"Hello {order.customer_details.name}, Your order with id: {order.id} "
        f"status is now {str(order.tracking_status)}"
    )
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [order.customer_details.email]
    send_mail(subject, message, email_from, recipient_list)


@task(queue_name="high_priority")
def send_order_deleted_email(order_id, customer_email):
    """send order deleted email to customer."""
    subject = "Order Deleted"
    message = f"Order {order_id} has been deleted!"
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [customer_email]
    send_mail(subject, message, email_from, recipient_list)
