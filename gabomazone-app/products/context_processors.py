from .models import ProductFavorite, Product
from django.db import connection
from accounts.models import PeerToPeerProductFavorite, ProductConversation


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
        product_fav_table_name = ProductFavorite._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{product_fav_table_name}'")
            product_fav_table_exists = cursor.fetchone() is not None
        
        peer_fav_table_name = PeerToPeerProductFavorite._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{peer_fav_table_name}'")
            peer_fav_table_exists = cursor.fetchone() is not None
        
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
    """Context processor pour le compteur de messages non lus (conversations + commandes + intentions d'achat)"""
    try:
        if not request.user.is_authenticated:
            return {'messages_count': 0}
        
        total_unread_messages = 0
        total_unread_orders = 0
        total_unread_intents = 0
        
        # Vérifier si les tables existent
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_productconversation'")
            conv_table_exists = cursor.fetchone() is not None
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_peertopeerordernotification'")
            notif_table_exists = cursor.fetchone() is not None
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='c2c_purchaseintent'")
            intent_table_exists = cursor.fetchone() is not None
        
        # Messages non lus dans les conversations
        if conv_table_exists:
            # Messages non lus en tant que vendeur
            seller_conversations = ProductConversation.objects.filter(seller=request.user)
            for conv in seller_conversations:
                total_unread_messages += conv.get_unread_count_for_seller()
            
            # Messages non lus en tant qu'acheteur
            buyer_conversations = ProductConversation.objects.filter(buyer=request.user)
            for conv in buyer_conversations:
                total_unread_messages += conv.get_unread_count_for_buyer()
        
        # Commandes non lues
        if notif_table_exists:
            from accounts.models import PeerToPeerOrderNotification
            total_unread_orders = PeerToPeerOrderNotification.objects.filter(
                seller=request.user,
                is_read=False
            ).count()
        
        # Intentions d'achat non notifiées
        if intent_table_exists:
            from c2c.models import PurchaseIntent
            total_unread_intents = PurchaseIntent.objects.filter(
                seller=request.user,
                seller_notified=False,
                status__in=[PurchaseIntent.PENDING, PurchaseIntent.NEGOTIATING]
            ).count()
        
        total = total_unread_messages + total_unread_orders + total_unread_intents
        
        return {
            'messages_count': total,
            'orders_count': total_unread_orders,
            'intents_count': total_unread_intents,
        }
    except Exception as e:
        # En cas d'erreur, retourner 0 pour éviter de casser le template
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in messages_count context processor: {e}")
        return {'messages_count': 0, 'orders_count': 0, 'intents_count': 0}
