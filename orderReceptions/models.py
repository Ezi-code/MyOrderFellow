"""order receptions models."""

from django.db import models
from base.models import TimeStampedModel
import uuid

from orderReceptions.choices import OrderTrackingStatusChoices


class OrderCustomerDetails(TimeStampedModel):
    """order customer details."""

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    email = models.EmailField()

    def __str__(self):
        """Return customer details."""
        return self.name


class OrderDetails(TimeStampedModel):
    """order details model."""

    id = models.UUIDField(
        primary_key=True, editable=False, default=uuid.uuid4, db_index=True
    )
    customer_details = models.ForeignKey(
        OrderCustomerDetails, on_delete=models.CASCADE, db_index=True
    )
    address = models.TextField()
    item_summary = models.TextField()
    tracking_status = models.CharField(
        max_length=20,
        choices=OrderTrackingStatusChoices.choices,
        default=OrderTrackingStatusChoices.PENDING,
    )

    def __str__(self):
        """Return customer details."""
        return f"{self.customer_details.name} >> {self.id}"
