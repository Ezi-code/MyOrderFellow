"""user authentication app config."""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """user authentication app config."""

    name = "users"
    verbose_name = "User Authentication"
    default_auto_field = "django.db.models.BigAutoField"
