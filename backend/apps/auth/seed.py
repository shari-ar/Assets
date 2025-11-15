from __future__ import annotations

import logging
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.utils import OperationalError, ProgrammingError


logger = logging.getLogger(__name__)


def _database_has_auth_tables() -> bool:
    connection = connections[DEFAULT_DB_ALIAS]
    try:
        table_names = connection.introspection.table_names()
    except (OperationalError, ProgrammingError):
        return False
    user_model = get_user_model()
    return user_model._meta.db_table in table_names


def seed_dev_data() -> None:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return

    if not settings.DEBUG:
        return

    if not _database_has_auth_tables():
        return

    user_model = get_user_model()

    if user_model.objects.exists():
        return

    admin = user_model.objects.create_superuser(
        email="admin@example.com",
        password="AdminPass123!",
        first_name="Dev",
        last_name="Admin",
    )

    user_model.objects.create_user(
        email="user@example.com",
        password="UserPass123!",
        first_name="Demo",
        last_name="User",
        role=user_model.Role.USER,
    )

    logger.info("Seeded development authentication data with default users (admin id=%s)", admin.id)
