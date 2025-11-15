from __future__ import annotations

import os
import sys

from django.apps import AppConfig
from django.conf import settings


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auth"
    label = "assets_auth"
    verbose_name = "Authentication"

    def ready(self) -> None:  # pragma: no cover - exercised implicitly on startup
        super().ready()

        if not settings.DEBUG:
            return

        if os.getenv("DISABLE_DEV_SEEDING") == "1":
            return

        if "runserver" not in sys.argv:
            return

        if os.getenv("RUN_MAIN") != "true":
            return

        from .seed import seed_dev_data

        seed_dev_data()
