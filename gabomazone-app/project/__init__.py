import compat_django4  # noqa: F401 — shims pour jsonfield/django-currencies sur Django 4+
from .celery import app as celery_app

__all__ = ('celery_app',)
