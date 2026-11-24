"""Local development settings for SlotChef."""

from .base import *  # noqa: F403
from .base import _env_bool

DEBUG = _env_bool("DJANGO_DEBUG", True)

