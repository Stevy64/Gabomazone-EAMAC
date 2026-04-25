from .models import ProductFavorite, Product
from django.db import connection
from django.db.models import Q
from django.urls import reverse
from accounts.models import PeerToPeerProductFavorite, ProductConversation, B2CProductConversation


def new_products_obj(request):
    """Context processor pour les nouveaux produits"""
    try:
        new_products = Product.objects.all().filter(PRDISactive=True).order_by('-date')[:10]
        return {
            'new_products': new_products,
        }
    except Exception as e:
        return {
            'new_products': [],
        }


def wishlist_count(request):
    """Context processor pour le compteur de la liste à souhaits (produits normaux + articles d'occasion)"""
    try:
        # Vérifier si les tables existent
        existing_tables = connection.introspection.table_names()
        product_fav_table_exists = ProductFavorite._meta.db_table in existing_tables
        peer_fav_table_exists = PeerToPeerProductFavorite._meta.db_table in existing_tables
        
        if not product_fav_table_exists and not peer_fav_table_exists:
            return {'wishlist_count': 0}
        
        wishlist_count = 0
        
        if request.user.is_authenticated:
            if product_fav_table_exists:
                wishlist_count += ProductFavorite.objects.filter(user=request.user).count()
            if peer_fav_table_exists:
                wishlist_count += PeerToPeerProductFavorite.objects.filter(user=request.user).count()
        else:
            session_key = request.session.session_key
            if session_key:
                if product_fav_table_exists:
                    wishlist_count += ProductFavorite.objects.filter(session_key=session_key).count()
                if peer_fav_table_exists:
                    wishlist_count += PeerToPeerProductFavorite.objects.filter(session_key=session_key).count()
            else:
                wishlist_count = 0
        
        return {'wishlist_count': wishlist_count}
    except Exception as e:
        # En cas d'erreur, retourner 0 pour éviter de casser le template
        return {'wishlist_count': 0}


def messages_count(request):
    """Context processor pour le compteur de messages non lus, commandes et notifications totales"""
    try:
        if not request.user.is_authenticated:
            return {
                'messages_count': 0,
                'unread_messages_count': 0,
                'unread_orders_count': 0,
                'total_notifications_count': 0,
            }
        
        total_unread_messages = 0
        total_unread_orders = 0
        total_unread_intents = 0
        
        # Vérifier si les tables existent
        existing_tables = connection.introspection.table_names()
        conv_table_exists = 'accounts_productconversation' in existing_tables
        notif_table_exists = 'accounts_peertopeerordernotification' in existing_tables
        intent_table_exists = 'c2c_purchaseintent' in existing_tables
        
        # Messages non lus dans les conversations (hors conversations archivées)
        if conv_table_exists:
            # Messages non lus en tant que vendeur
            seller_conversations = ProductConversation.objects.filter(
                seller=request.user, is_archived_by_seller=False)
            for conv in seller_conversations:
                total_unread_messages += conv.get_unread_count_for_seller()

            # Messages non lus en tant qu'acheteur
            buyer_conversations = ProductConversation.objects.filter(
                buyer=request.user, is_archived_by_buyer=False)
            for conv in buyer_conversations:
                total_unread_messages += conv.get_unread_count_for_buyer()
        
        # Commandes non lues (notifications peer-to-peer)
        if notif_table_exists:
            from accounts.models import PeerToPeerOrderNotification
            total_unread_orders = PeerToPeerOrderNotification.objects.filter(
                seller=request.user,
                is_read=False
            ).count()
        
        # Intentions d'achat non notifiées (ajouter aux notifications de commandes)
        if intent_table_exists:
            from c2c.models import PurchaseIntent
            total_unread_intents = PurchaseIntent.objects.filter(
                seller=request.user,
                seller_notified=False,
                status__in=[
                    PurchaseIntent.PENDING,
                    PurchaseIntent.AWAITING_AVAILABILITY,
                    PurchaseIntent.NEGOTIATING,
                ]
            ).count()
        
        # Total des messages non lus (conversations uniquement)
        unread_messages = total_unread_messages
        
        # Total des commandes non lues (commandes + intentions d'achat)
        unread_orders = total_unread_orders + total_unread_intents
        
        # Total des notifications (messages + commandes)
        total_notifications = unread_messages + unread_orders
        
        # Messagerie B2C produit : badge uniquement côté vendeur pro (interface dans le dashboard vendeur)
        b2c_unread_messages_count = 0
        b2c_conv_table_exists = 'accounts_b2cproductconversation' in existing_tables
        if b2c_conv_table_exists:
            from accounts.models import Profile
            prof = Profile.objects.filter(user=request.user).first()
            if prof and prof.status == 'vendor' and prof.admission:
                for conv in B2CProductConversation.objects.filter(vendor=request.user):
                    b2c_unread_messages_count += conv.unread_for_vendor()

        return {
            'messages_count': total_notifications,  # Pour compatibilité
            'unread_messages_count': unread_messages,
            'unread_orders_count': unread_orders,
            'total_notifications_count': total_notifications,
            'b2c_unread_messages_count': b2c_unread_messages_count,
        }
    except Exception as e:
        # En cas d'erreur, retourner 0 pour éviter de casser le template
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in messages_count context processor: {e}")
        return {
            'messages_count': 0,
            'unread_messages_count': 0,
            'unread_orders_count': 0,
            'total_notifications_count': 0,
            'b2c_unread_messages_count': 0,
        }


def pending_c2c_meeting_for_modal(request):
    """
    Commande C2C où l'utilisateur doit confirmer un point de rencontre proposé par l'autre partie.
    Utilisé pour afficher une modale (base.html) avec lien vers la fiche commande + carte.
    """
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {'pending_c2c_meeting': None}
    try:
        from c2c.models import C2COrder

        existing_tables = connection.introspection.table_names()
        if 'c2c_c2corder' not in existing_tables:
            return {'pending_c2c_meeting': None}

        order = (
            C2COrder.objects.filter(
                Q(buyer=request.user) | Q(seller=request.user),
                status__in=[
                    C2COrder.PAID,
                    C2COrder.PENDING_DELIVERY,
                    C2COrder.DELIVERED,
                ],
                meeting_type__in=[C2COrder.MEETING_SAFE_ZONE, C2COrder.MEETING_CUSTOM],
                meeting_proposed_by__isnull=False,
            )
            .exclude(meeting_proposed_by=request.user)
            .filter(
                Q(buyer=request.user, meeting_confirmed_by_buyer=False)
                | Q(seller=request.user, meeting_confirmed_by_seller=False)
            )
            .select_related('product', 'meeting_proposed_by')
            .order_by('-id')
            .first()
        )
        if not order:
            return {'pending_c2c_meeting': None}

        proposer = order.meeting_proposed_by
        proposer_display = (
            (proposer.get_full_name() or proposer.username or 'La contrepartie')
            if proposer
            else 'La contrepartie'
        )
        product_name = (
            order.product.product_name
            if getattr(order, 'product_id', None)
            else 'Votre commande'
        )
        confirm_path = reverse('c2c:order-detail', args=[order.id]) + '?meeting_pending=1'
        return {
            'pending_c2c_meeting': {
                'order_id': order.id,
                'product_name': product_name[:200],
                'proposer_display': proposer_display[:120],
                'confirm_path': confirm_path,
            }
        }
    except Exception:
        return {'pending_c2c_meeting': None}
