from django.apps import AppConfig


class C2CConfig(AppConfig):
    """Configuration de l'application C2C"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'c2c'
    verbose_name = 'C2C - Vente C2C'

    def ready(self):
        """Import des signaux lors du chargement de l'application"""
        import c2c.signals  # noqa


