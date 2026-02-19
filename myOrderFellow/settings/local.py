"""local settings for myOrderFellow project."""

from .base import *  # noqa F403

SECRET_KEY = "django-insecure-m5!8_e4vop+j#!_-c@vl)oylv56bt9bz=!*-#7u(r$9s!uc4(8"
DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa F405
    }
}

STATIC_URL = "static/"
