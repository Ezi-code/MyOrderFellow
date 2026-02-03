from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Time stamped model."""

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options."""

        abstract = True
