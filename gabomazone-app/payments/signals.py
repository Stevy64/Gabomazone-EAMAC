"""
Signaux pour la gestion de l'escrow
Libération automatique des fonds après confirmation de livraison
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import logging

from orders.models import Order, OrderSupplier
from payments.escrow_service import EscrowService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def release_escrow_on_order_complete(sender, instance, **kwargs):
    """
    Libère les fonds en escrow lorsque la commande B2C est complétée
    """
    # Vérifier si la commande est complétée
    if instance.status == Order.COMPLETE and instance.is_finished:
        try:
            # Libérer l'escrow
            success, response = EscrowService.release_escrow_for_order(instance)
            if success:
                logger.info(f"Fonds en escrow libérés pour la commande {instance.id}")
            else:
                logger.warning(f"Impossible de libérer l'escrow pour la commande {instance.id}: {response.get('error')}")
        except Exception as e:
            logger.exception(f"Erreur lors de la libération de l'escrow pour la commande {instance.id}: {str(e)}")


@receiver(post_save, sender=OrderSupplier)
def release_escrow_on_order_supplier_complete(sender, instance, **kwargs):
    """
    Libère les fonds en escrow lorsque la commande fournisseur est complétée
    """
    # Vérifier si la commande fournisseur est complétée
    if instance.status == OrderSupplier.COMPLETE:
        try:
            # Libérer l'escrow pour la commande principale
            if instance.order:
                success, response = EscrowService.release_escrow_for_order(instance.order)
                if success:
                    logger.info(f"Fonds en escrow libérés pour la commande {instance.order.id} via OrderSupplier {instance.id}")
                else:
                    logger.warning(f"Impossible de libérer l'escrow: {response.get('error')}")
        except Exception as e:
            logger.exception(f"Erreur lors de la libération de l'escrow: {str(e)}")



