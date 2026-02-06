"""order receptions utils."""

from django.core.mail import send_mail

from django.conf import settings
from django_tasks import task
from secrets import compare_digest

from users.models import User


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
    from orderReceptions.models import OrderStatusHistory

    order_instance = None
    try:
        order_instance = OrderStatusHistory.objects.create(
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
    send_mail(subject, message, email_from, recipient_list)


@task(queue_name="high_priority")
def send_order_deleted_email(order_id, customer_email):
    """send order deleted email to customer."""
    subject = "Order Deleted"
    message = f"Order {order_id} has been deleted!"
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [customer_email]
    send_mail(subject, message, email_from, recipient_list)


def verify_webhook_signature(request):
    """verify webhook signature."""
    customer_email = request.headers.get("X-Customer-Email")
    if not customer_email:
        raise ValueError("X-Customer-Email header is missing.")

    try:
        company = User.objects.get(email=customer_email, is_active=True)
    except User.DoesNotExist:
        raise ValueError("Company account not found or inactive.")

    signature = request.headers.get("X-Webhook-Signature")
    if not signature:
        raise ValueError("X-Webhook-Signature header is missing.")

    webhook_secret = company.webhook_secret
    if not webhook_secret.is_active or webhook_secret.is_expired():
        raise ValueError("Webhook secret is inactive or expired")
    if not compare_digest(signature, webhook_secret.secret_key):
        raise Exception("Invalid signature")

    # try:
    #     webhook_secret = company.webhook_secret
    #     if not webhook_secret.is_active or webhook_secret.is_expired():
    #         raise ValueError("Webhook secret is inactive or expired")
    #     if not compare_digest(signature, webhook_secret.secret_key):
    #         raise Exception("Invalid signature")
    # except Exception:
    #     raise ValueError("Invalid webhook signature.")

    return request
