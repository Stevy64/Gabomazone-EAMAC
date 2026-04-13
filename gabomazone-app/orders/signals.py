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
    if kwargs.get('raw', False):
        return
    if instance.is_completed() and instance.order_id:
        order = instance.order
        if order.status != Order.COMPLETE:
            order.status = Order.COMPLETE
            order.save(update_fields=['status'])
            logger.info(f"Commande B2C #{order.id} marquée COMPLETE après vérification livraison #{instance.id}")


@receiver(post_save, sender=Order)
def pay_commissions_on_complete(sender, instance, **kwargs):
    """
    Paye les commissions B2C au vendeur uniquement après confirmation livraison (status=COMPLETE).
    Les commissions ne sont JAMAIS payées au moment du paiement initial.
    Décrémente également le stock des produits vendus.
    """
    if kwargs.get('raw', False):
        return
    if instance.status == Order.COMPLETE:
        try:
            from payments.views import _pay_order_commissions
            _pay_order_commissions(instance)
            logger.info("Commissions B2C payées pour commande #%s (COMPLETE)", instance.id)
        except Exception as e:
            logger.error("Erreur paiement commissions B2C commande #%s: %s", instance.id, e)

        # Décrémente le stock des produits vendus
        try:
            from orders.models import OrderDetails
            for detail in OrderDetails.objects.filter(order=instance):
                if detail.product:
                    detail.product.update_stock(detail.quantity)
        except Exception as e:
            logger.error("Erreur mise à jour stock commande #%s: %s", instance.id, e)
