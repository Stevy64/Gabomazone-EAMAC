from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = 'payments'
    
    def ready(self):
        """Import des signaux lors du chargement de l'application"""
        import payments.signals  # noqa