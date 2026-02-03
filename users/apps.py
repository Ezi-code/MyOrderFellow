"""user authentication app config."""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """user authentication app config."""

    name = "users"
    verbose_name = "User Authentication"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """Import signals when app is ready."""
        import users.signals  # noqa: F401
