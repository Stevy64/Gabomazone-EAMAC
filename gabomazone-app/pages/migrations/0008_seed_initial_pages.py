"""
Données initiales pour le footer — section "Entreprise".
Crée les pages standard si elles n'existent pas encore.
"""
from django.db import migrations


INITIAL_PAGES = [
    {"name": "À propos de GabomaZone", "slug": "a-propos",                  "content": "<p>À propos de GabomaZone.</p>"},
    {"name": "Conditions d'utilisation", "slug": "conditions-utilisation",   "content": "<p>Conditions générales d'utilisation.</p>"},
    {"name": "Politique de remboursement", "slug": "politique-de-remboursement", "content": "<p>Notre politique de remboursement.</p>"},
    {"name": "Politique de confidentialité", "slug": "politique-de-confidentialite", "content": "<p>Notre politique de confidentialité.</p>"},
]


def seed_pages(apps, schema_editor):
    PagesList = apps.get_model("pages", "PagesList")
    for page in INITIAL_PAGES:
        PagesList.objects.get_or_create(
            slug=page["slug"],
            defaults={"name": page["name"], "content": page["content"], "active": True},
        )


def unseed_pages(apps, schema_editor):
    PagesList = apps.get_model("pages", "PagesList")
    slugs = [p["slug"] for p in INITIAL_PAGES]
    PagesList.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0007_alter_pageslist_id"),
    ]

    operations = [
        migrations.RunPython(seed_pages, unseed_pages),
    ]
