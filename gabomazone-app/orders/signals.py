"""
Signaux pour les commandes B2C : finalisation et libération escrow après double vérification
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from .models import Order, B2CDeliveryVerification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=B2CDeliveryVerification)
def b2c_verification_complete_release_escrow(sender, instance, **kwargs):
    """
    Lorsque la vérification B2C est complète (les deux codes validés),
    marquer la commande comme COMPLETE pour déclencher la libération de l'escrow.
    """
    if instance.is_completed() and instance.order_id:
        order = instance.order
        if order.status != Order.COMPLETE:
            order.status = Order.COMPLETE
            order.save(update_fields=['status'])
            logger.info(f"Commande B2C #{order.id} marquée COMPLETE après vérification livraison #{instance.id}")
