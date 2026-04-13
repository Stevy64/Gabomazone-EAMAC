# Migration 0071 — no-op
#
# La table products_productfavorite est déjà créée correctement par 0070_productfavorite
# via les opérations Django standard. Cette migration était une sécurité SQLite-only
# qui ne fonctionne pas avec PostgreSQL. Elle est remplacée par un no-op.

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('products', '0070_productfavorite'),
    ]

    operations = [
        migrations.RunPython(
            migrations.RunPython.noop,
            migrations.RunPython.noop,
        ),
    ]
