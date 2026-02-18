"""
Signaux Django pour créer automatiquement des notifications admin
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist


# Import direct pour éviter les problèmes de chargement
def get_admin_notification_model():
    """Récupère le modèle AdminNotification de manière sécurisée"""
    try:
        from .models import AdminNotification
        # Vérifier si la table existe
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_adminnotification'")
            if cursor.fetchone():
                return AdminNotification
    except:
        pass
    return None


@receiver(post_save, sender='accounts.ProductBoostRequest')
def notify_admin_on_boost_request(sender, instance, created, **kwargs):
    """Créer une notification admin lorsqu'une demande de boost est créée"""
    try:
        from .models import AdminNotification, ProductBoostRequest
        
        if created and instance.status == ProductBoostRequest.PENDING:
            try:
                related_url = reverse('admin:accounts_productboostrequest_change', args=[instance.id])
            except:
                related_url = f'/admin/accounts/productboostrequest/{instance.id}/change/'
            
            AdminNotification.objects.create(
                notification_type=AdminNotification.BOOST_REQUEST,
                title=f"Demande de boost pour {instance.product.product_name}",
                message=f"Le vendeur {instance.vendor.user.username} a demandé un boost pour le produit '{instance.product.product_name}'.",
                related_object_id=instance.id,
                related_object_type='ProductBoostRequest',
                related_url=related_url
            )
    except Exception as e:
        # Éviter les erreurs qui bloquent la sauvegarde
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la création de la notification admin pour boost: {e}")


@receiver(post_save, sender='accounts.PremiumSubscription')
def notify_admin_on_premium_subscription(sender, instance, created, **kwargs):
    """Créer une notification admin lorsqu'un abonnement premium est créé ou en attente"""
    try:
        from .models import AdminNotification, PremiumSubscription
        
        if created and instance.status == PremiumSubscription.PENDING:
            try:
                related_url = reverse('admin:accounts_premiumsubscription_change', args=[instance.id])
            except:
                related_url = f'/admin/accounts/premiumsubscription/{instance.id}/change/'
            
            AdminNotification.objects.create(
                notification_type=AdminNotification.PREMIUM_SUBSCRIPTION,
                title=f"Demande d'abonnement premium - {instance.vendor.user.username}",
                message=f"Le vendeur {instance.vendor.user.username} a demandé un abonnement premium.",
                related_object_id=instance.id,
                related_object_type='PremiumSubscription',
                related_url=related_url
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la création de la notification admin pour abonnement: {e}")


@receiver(post_save, sender='contact.MessagesList')
def notify_admin_on_contact_message(sender, instance, created, **kwargs):
    """Créer une notification admin lorsqu'un message de contact est reçu"""
    try:
        from .models import AdminNotification
        
        if created:
            try:
                related_url = reverse('admin:contact_messageslist_change', args=[instance.id])
            except:
                related_url = f'/admin/contact/messageslist/{instance.id}/change/'
            
            AdminNotification.objects.create(
                notification_type=AdminNotification.CONTACT_MESSAGE,
                title=f"Nouveau message de {instance.name}",
                message=f"Message reçu de {instance.name} ({instance.email}) : {instance.subject}",
                related_object_id=instance.id,
                related_object_type='MessagesList',
                related_url=related_url
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la création de la notification admin pour message: {e}")


@receiver(post_save, sender='accounts.PeerToPeerProduct')
def notify_admin_on_new_product(sender, instance, created, **kwargs):
    """Notifier l'admin lorsqu'un nouvel article C2C est mis en ligne (pas de validation requise)."""
    try:
        AdminNotification = get_admin_notification_model()
        if not AdminNotification:
            return
        
        from .models import PeerToPeerProduct
        
        if not created or not hasattr(instance, 'status'):
            return
        # Notifier pour tout nouvel article (mis en ligne directement)
        if instance.status != PeerToPeerProduct.APPROVED:
            return
        try:
            related_url = reverse('admin:accounts_peertopeerproduct_change', args=[instance.id])
        except Exception:
            related_url = f'/admin/accounts/peertopeerproduct/{instance.id}/change/'
        
        existing_notification = AdminNotification.objects.filter(
            notification_type=AdminNotification.PRODUCT_APPROVAL,
            related_object_id=instance.id,
            related_object_type='PeerToPeerProduct',
            is_resolved=False
        ).first()
        
        if not existing_notification:
            AdminNotification.objects.create(
                notification_type=AdminNotification.PRODUCT_APPROVAL,
                title=f"Nouvel article C2C en ligne - {instance.product_name}",
                message=f"L'article '{instance.product_name}' de {instance.seller.username} a été mis en ligne.",
                related_object_id=instance.id,
                related_object_type='PeerToPeerProduct',
                related_url=related_url
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la création de la notification admin pour produit: {e}", exc_info=True)

