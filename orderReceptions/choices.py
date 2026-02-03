"""order receptions model choices."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class OrderTrackingStatusChoices(models.TextChoices):
    """order tracking status choices."""

    PENDING = "PENDING", _("Pending")
    IN_TRANSIT = "IN TRANSIT", _("In transit")
    OUT_FOR_DELIVERY = "OUT FOR DELIVERY", _("Out for delivery")
    DELIVERED = "DELIVERED", _("Delivered")
