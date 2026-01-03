"""
Signaux pour le module C2C
Gestion des notifications et mises à jour automatiques
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import PurchaseIntent, C2COrder, DeliveryVerification
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PurchaseIntent)
def notify_seller_on_purchase_intent(sender, instance, created, **kwargs):
    """
    Notifie le vendeur lorsqu'une nouvelle intention d'achat est créée
    """
    if created and not instance.seller_notified:
        # TODO: Implémenter la notification (email, push, etc.)
        logger.info(f"Nouvelle intention d'achat #{instance.id} pour {instance.seller.username}")
        instance.seller_notified = True
        instance.save(update_fields=['seller_notified'])


@receiver(post_save, sender=C2COrder)
def update_order_status_on_payment(sender, instance, created, **kwargs):
    """
    Met à jour le statut de la commande lorsque le paiement est confirmé
    """
    if instance.payment_transaction and instance.payment_transaction.status == 'success':
        if instance.status == C2COrder.PENDING_PAYMENT:
            instance.status = C2COrder.PAID
            instance.paid_at = timezone.now()
            instance.save(update_fields=['status', 'paid_at'])


@receiver(post_save, sender=DeliveryVerification)
def complete_order_on_verification(sender, instance, created, **kwargs):
    """
    Finalise la commande lorsque la vérification est complète
    """
    if instance.is_completed() and instance.c2c_order.status != C2COrder.COMPLETED:
        instance.c2c_order.status = C2COrder.COMPLETED
        instance.c2c_order.completed_at = timezone.now()
        instance.c2c_order.save(update_fields=['status', 'completed_at'])



