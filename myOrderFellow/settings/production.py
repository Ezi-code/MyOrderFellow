"""production settings for myOrderFellow project."""

from .base import *  # noqa f403

SECRET_KEY = "django-insecure-m5!8_e4vop+j#!_-c@vl)oylv56bt9bz=!*-#7u(r$9s!uc4(8"
DEBUG = False

ALLOWED_HOSTS = ["myorderfellow.onrender.com", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3.production",  # noqa F405
    }
}

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"  # noqa F405
MEDIA_ROOT = BASE_DIR / "media"  # noqa F405
