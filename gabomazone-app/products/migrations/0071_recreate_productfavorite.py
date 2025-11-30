# Generated manually to recreate ProductFavorite table
# 
# Cette migration recrée la table ProductFavorite qui a été supprimée
# par une migration précédente (0071_delete_productfavorite.py qui a été supprimée).
# 
# Cette migration utilise RunSQL pour créer la table seulement si elle n'existe pas,
# ce qui évite les erreurs si la migration 0070 a déjà créé la table.

from django.conf import settings
from django.db import migrations


def create_table_if_not_exists(apps, schema_editor):
    """
    Crée la table products_productfavorite seulement si elle n'existe pas.
    Compatible avec SQLite (base de données par défaut du projet).
    """
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Vérifier si la table existe déjà
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='products_productfavorite'
        """)
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            # Créer la table avec toutes les contraintes
            cursor.execute("""
                CREATE TABLE products_productfavorite (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_key VARCHAR(40) NULL,
                    date DATETIME NULL,
                    product_id INTEGER NOT NULL REFERENCES products_product(id) ON DELETE CASCADE,
                    user_id INTEGER NULL REFERENCES auth_user(id) ON DELETE CASCADE
                )
            """)
            # Créer les index uniques pour les contraintes unique_together
            # Note: SQLite ne supporte pas WHERE dans CREATE UNIQUE INDEX,
            # donc on crée des index simples et Django gérera les contraintes au niveau applicatif
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS products_productfavorite_product_user_unique 
                ON products_productfavorite(product_id, user_id)
            """)
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS products_productfavorite_product_session_unique 
                ON products_productfavorite(product_id, session_key)
            """)
            # Créer les index pour améliorer les performances
            cursor.execute("CREATE INDEX IF NOT EXISTS products_productfavorite_product_id ON products_productfavorite(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS products_productfavorite_user_id ON products_productfavorite(user_id)")


def reverse_create_table(apps, schema_editor):
    """Supprime la table products_productfavorite (pour rollback)"""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS products_productfavorite")


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('products', '0070_productfavorite'),
    ]

    operations = [
        migrations.RunPython(
            create_table_if_not_exists,
            reverse_create_table,
        ),
    ]

