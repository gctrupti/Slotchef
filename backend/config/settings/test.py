"""Test settings for SlotChef.

Uses TEST_DATABASE_URL if provided, otherwise falls back to DATABASE_URL when
configured. For isolated offline unit tests without live PostgreSQL
credentials, set SLOTCHEF_UNIT_TEST_SQLITE=1 explicitly.
"""

from __future__ import annotations

import os

from .base import *  # noqa: F403
from .base import build_postgres_config

DEBUG = False
IS_TESTING = True
TESTING = True
CELERY_TASK_ALWAYS_EAGER = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

_test_db_url = os.environ.get("TEST_DATABASE_URL", "").strip()
_use_postgres = os.environ.get("SLOTCHEF_TEST_POSTGRES", "").strip() in {
    "1",
    "true",
    "yes",
}

if _test_db_url:
    DATABASES = {"default": build_postgres_config(_test_db_url)}
elif _use_postgres:
    DATABASES = {"default": build_postgres_config()}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

