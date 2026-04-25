"""
Signaux pour le module C2C
Gestion des notifications et mises à jour automatiques
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import PurchaseIntent, C2COrder, DeliveryVerification
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PurchaseIntent)
def notify_seller_on_purchase_intent(sender, instance, created, **kwargs):
    """
    Logue la création d'une intention d'achat.
    seller_notified reste False → le vendeur verra la notification non lue
    dans sa messagerie et devra d'abord confirmer la disponibilité de l'article.
    """
    if created and not kwargs.get('raw', False):
        logger.info(
            '[C2C·SIGNAL] Nouvelle intention #%d — seller=%s product=#%d (seller_notified=%s)',
            instance.id, instance.seller_id, instance.product_id, instance.seller_notified,
        )


@receiver(post_save, sender=C2COrder)
def update_order_status_on_payment(sender, instance, created, **kwargs):
    """
    Met à jour le statut de la commande lorsque le paiement est confirmé
    """
    if kwargs.get('raw', False):
        return
    if instance.payment_transaction and instance.payment_transaction.status == 'success':
        if instance.status == C2COrder.PENDING_PAYMENT:
            instance.status = C2COrder.PAID
            instance.paid_at = timezone.now()
            instance.save(update_fields=['status', 'paid_at'])


@receiver(post_save, sender=DeliveryVerification)
def complete_order_on_verification(sender, instance, created, **kwargs):
    """
    Finalise la commande lorsque la vérification est complète.
    Marque le produit comme VENDU et libère les fonds en escrow.
    """
    if kwargs.get('raw', False):
        return
    if instance.is_completed() and instance.c2c_order.status != C2COrder.COMPLETED:
        order = instance.c2c_order
        order.status = C2COrder.COMPLETED
        order.completed_at = timezone.now()
        order.save(update_fields=['status', 'completed_at'])

        # Marquer le produit comme VENDU
        try:
            from accounts.models import PeerToPeerProduct
            product = order.product
            if product.status != PeerToPeerProduct.SOLD:
                product.status = PeerToPeerProduct.SOLD
                product.save(update_fields=['status'])
                logger.info('[C2C·SIGNAL] Produit #%d marqué SOLD', product.id)
        except Exception as e:
            logger.warning('[C2C·SIGNAL] Impossible de marquer le produit SOLD: %s', e)

        # Libérer les fonds en escrow
        try:
            from payments.escrow_service import EscrowService
            success, response = EscrowService.release_escrow_for_c2c_order(order)
            if success:
                logger.info('[C2C·SIGNAL] Fonds escrow libérés pour commande C2C #%d', order.id)
            else:
                logger.error('[C2C·SIGNAL] Erreur libération escrow: %s', response.get('error'))
        except Exception as e:
            logger.exception('[C2C·SIGNAL] Erreur libération escrow C2C: %s', e)
