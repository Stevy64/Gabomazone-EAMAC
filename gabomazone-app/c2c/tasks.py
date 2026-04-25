from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def expire_old_intents():
    """Expire les intentions d'achat trop anciennes."""
    from .models import PurchaseIntent

    expired = PurchaseIntent.objects.filter(
        expires_at__lt=timezone.now(),
        status__in=[
            PurchaseIntent.PENDING,
            PurchaseIntent.NEGOTIATING,
            PurchaseIntent.AWAITING_AVAILABILITY,
        ]
    )
    count = expired.count()
    expired.update(status=PurchaseIntent.EXPIRED)
    logger.info('%d intentions d\'achat expirées.', count)
    return f'{count} intentions expirées.'


@shared_task
def expire_old_negotiations():
    """Expire les propositions de négociation sans réponse après 24h."""
    from .models import Negotiation

    expired = Negotiation.objects.filter(
        expires_at__lt=timezone.now(),
        status=Negotiation.PENDING,
    )
    count = expired.count()
    expired.update(status=Negotiation.REJECTED)
    logger.info('%d négociations expirées (sans réponse).', count)
    return f'{count} négociations expirées.'
