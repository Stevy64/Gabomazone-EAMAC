from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_sessions():
    """Nettoie les sessions expirées de la base de données."""
    from django.core.management import call_command
    call_command('clearsessions')
    logger.info('Sessions expirées nettoyées.')
    return 'Sessions nettoyées.'
