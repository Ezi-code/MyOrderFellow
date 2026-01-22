"""order receptions app config."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrderreceptionsConfig(AppConfig):
    """order receptions app config."""

    name = "orderReceptions"
    verbose_name = _("Order receptions")
    default_auto_field = "django.db.models.BigAutoField"
