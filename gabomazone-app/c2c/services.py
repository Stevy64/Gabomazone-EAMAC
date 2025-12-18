"""
Services pour le module C2C
Abstraction de la logique métier et intégration avec SingPay
"""
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from .models import (
    PlatformSettings, PurchaseIntent, Negotiation, C2COrder,
    DeliveryVerification, ProductBoost, SellerBadge
)
from accounts.models import PeerToPeerProduct
from payments.models import SingPayTransaction
import logging

logger = logging.getLogger(__name__)


class CommissionCalculator:
    """Service pour calculer les commissions C2C"""
    
    @staticmethod
    def calculate_c2c_commissions(price):
        """
        Calcule les commissions C2C pour un prix donné
        Retourne un dictionnaire avec tous les montants calculés
        """
        settings = PlatformSettings.get_active_settings()
        return settings.calculate_c2c_commissions(price)
    
    @staticmethod
    def calculate_b2c_commissions(price):
        """
        Calcule les commissions B2C pour un prix donné
        """
        settings = PlatformSettings.get_active_settings()
        price = Decimal(str(price))
        buyer_commission = price * (settings.b2c_buyer_commission_rate / Decimal('100'))
        seller_commission = price * (settings.b2c_seller_commission_rate / Decimal('100'))
        total_platform_commission = buyer_commission + seller_commission
        seller_net = price - seller_commission
        buyer_total = price + buyer_commission
        
        return {
            'buyer_commission': buyer_commission,
            'seller_commission': seller_commission,
            'platform_commission': total_platform_commission,
            'seller_net': seller_net,
            'buyer_total': buyer_total,
            'original_price': price
        }


class PurchaseIntentService:
    """Service pour gérer les intentions d'achat"""
    
    @staticmethod
    @transaction.atomic
    def create_purchase_intent(product: PeerToPeerProduct, buyer, initial_price=None):
        """
        Crée une intention d'achat pour un produit C2C
        """
        from django.db import connection
        
        # Vérifier si la table existe avant d'essayer de créer une intention
        table_exists = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='c2c_purchaseintent'")
                table_exists = cursor.fetchone() is not None
        except Exception:
            table_exists = False
        
        if not table_exists:
            raise Exception("Les migrations C2C n'ont pas été appliquées. Exécutez: python manage.py migrate c2c")
        
        if initial_price is None:
            initial_price = product.PRDPrice
        
        # Vérifier qu'il n'existe pas déjà une intention d'achat active
        existing = PurchaseIntent.objects.filter(
            product=product,
            buyer=buyer,
            status__in=[PurchaseIntent.PENDING, PurchaseIntent.NEGOTIATING]
        ).first()
        
        if existing:
            return existing
        
        # Si une intention existe mais est terminée (REJECTED, CANCELLED, EXPIRED), la réactiver
        existing_terminated = PurchaseIntent.objects.filter(
            product=product,
            buyer=buyer,
            status__in=[PurchaseIntent.REJECTED, PurchaseIntent.CANCELLED, PurchaseIntent.EXPIRED]
        ).first()
        
        if existing_terminated:
            # Réactiver l'intention
            existing_terminated.status = PurchaseIntent.PENDING
            existing_terminated.initial_price = initial_price
            existing_terminated.negotiated_price = None
            existing_terminated.final_price = None
            existing_terminated.seller_notified = False
            existing_terminated.expires_at = timezone.now() + timedelta(days=7)
            existing_terminated.save()
            return existing_terminated
        
        intent = PurchaseIntent.objects.create(
            product=product,
            buyer=buyer,
            seller=product.seller,
            initial_price=initial_price,
            expires_at=timezone.now() + timedelta(days=7)  # Expire après 7 jours
        )
        
        # Créer ou récupérer la conversation
        from accounts.models import ProductConversation, ProductMessage
        conversation, created = ProductConversation.objects.get_or_create(
            product=product,
            buyer=buyer,
            seller=product.seller,
            defaults={'last_message_at': timezone.now()}
        )
        
        # Créer un message automatique pour notifier le vendeur
        buyer_name = buyer.get_full_name() or buyer.username
        welcome_message = f"👋 Bonjour ! {buyer_name} souhaite négocier l'achat de votre article '{product.product_name}'.\n\n💰 Prix initial : {initial_price:,.0f} FCFA\n\n💬 Vous pouvez maintenant discuter et négocier le prix directement ici."
        
        ProductMessage.objects.create(
            conversation=conversation,
            sender=buyer,
            message=welcome_message
        )
        
        # Mettre à jour la date du dernier message
        conversation.last_message_at = timezone.now()
        conversation.save()
        
        # seller_notified reste False par défaut - sera mis à True quand le vendeur verra la notification
        # Cela permet de compter les intentions non vues
        
        return intent
    
    @staticmethod
    def create_negotiation(intent: PurchaseIntent, proposer, proposed_price, message=None):
        """
        Crée une proposition de négociation
        """
        negotiation = Negotiation.objects.create(
            purchase_intent=intent,
            proposer=proposer,
            proposed_price=proposed_price,
            message=message
        )
        
        # Mettre à jour le statut de l'intention
        if intent.status == PurchaseIntent.PENDING:
            intent.status = PurchaseIntent.NEGOTIATING
            intent.save()
        
        # Mettre à jour le prix négocié
        intent.negotiated_price = proposed_price
        intent.save()
        
        # Créer un message automatique dans la conversation
        from accounts.models import ProductConversation, ProductMessage
        try:
            conversation = ProductConversation.objects.get(
                product=intent.product,
                buyer=intent.buyer,
                seller=intent.seller
            )
            
            proposer_name = proposer.get_full_name() or proposer.username
            negotiation_message = f"💰 {proposer_name} propose un nouveau prix : {proposed_price:,.0f} FCFA"
            if message:
                negotiation_message += f"\n\n💬 Message : {message}"
            
            ProductMessage.objects.create(
                conversation=conversation,
                sender=proposer,
                message=negotiation_message
            )
            
            conversation.last_message_at = timezone.now()
            conversation.save()
        except ProductConversation.DoesNotExist:
            pass  # La conversation n'existe pas encore
        
        return negotiation

    @staticmethod
    @transaction.atomic
    def accept_negotiation(negotiation: Negotiation, actor):
        """
        Accepte une proposition de négociation (par le destinataire)
        """
        intent = negotiation.purchase_intent
        if actor not in [intent.buyer, intent.seller]:
            raise PermissionError("Vous n'avez pas la permission d'accepter cette offre.")
        if actor == negotiation.proposer:
            raise PermissionError("Vous ne pouvez pas accepter votre propre offre.")
        
        # Marquer l'offre comme acceptée et rejeter les autres en attente
        negotiation.status = Negotiation.ACCEPTED
        negotiation.responded_at = timezone.now()
        negotiation.save()
        
        intent.negotiated_price = negotiation.proposed_price
        if intent.status != PurchaseIntent.NEGOTIATING:
            intent.status = PurchaseIntent.NEGOTIATING
        intent.save()
        
        negotiation.purchase_intent.negotiations.exclude(id=negotiation.id).filter(
            status=Negotiation.PENDING
        ).update(status=Negotiation.REJECTED, responded_at=timezone.now())
        
        # Message automatique
        from accounts.models import ProductConversation, ProductMessage
        try:
            conv = ProductConversation.objects.get(
                product=intent.product,
                buyer=intent.buyer,
                seller=intent.seller
            )
            actor_name = actor.get_full_name() or actor.username
            msg = f"✅ {actor_name} a accepté l'offre à {negotiation.proposed_price:,.0f} FCFA."
            ProductMessage.objects.create(conversation=conv, sender=actor, message=msg)
            conv.last_message_at = timezone.now()
            conv.save()
        except ProductConversation.DoesNotExist:
            pass
        
        return intent

    @staticmethod
    @transaction.atomic
    def reject_negotiation(negotiation: Negotiation, actor):
        """
        Refuse une proposition de négociation (par le destinataire)
        """
        intent = negotiation.purchase_intent
        if actor not in [intent.buyer, intent.seller]:
            raise PermissionError("Vous n'avez pas la permission de refuser cette offre.")
        if negotiation.status != Negotiation.PENDING:
            return negotiation
        
        negotiation.status = Negotiation.REJECTED
        negotiation.responded_at = timezone.now()
        negotiation.save()
        
        # Message automatique
        from accounts.models import ProductConversation, ProductMessage
        try:
            conv = ProductConversation.objects.get(
                product=intent.product,
                buyer=intent.buyer,
                seller=intent.seller
            )
            actor_name = actor.get_full_name() or actor.username
            msg = f"❌ {actor_name} a refusé la proposition à {negotiation.proposed_price:,.0f} FCFA."
            ProductMessage.objects.create(conversation=conv, sender=actor, message=msg)
            conv.last_message_at = timezone.now()
            conv.save()
        except ProductConversation.DoesNotExist:
            pass
        
        return negotiation
    
    @staticmethod
    @transaction.atomic
    def accept_final_price(intent: PurchaseIntent, final_price):
        """
        Accepte un prix final et crée la commande C2C
        """
        # Vérifier si une commande existe déjà pour cette intention
        existing_order = C2COrder.objects.filter(purchase_intent=intent).first()
        if existing_order:
            return existing_order
        
        if intent.status != PurchaseIntent.AGREED:
            intent.status = PurchaseIntent.AGREED
            intent.final_price = final_price
            intent.agreed_at = timezone.now()
            intent.save()
        
        # Calculer les commissions
        calculator = CommissionCalculator()
        commissions = calculator.calculate_c2c_commissions(final_price)
        
        # Créer la commande C2C
        c2c_order = C2COrder.objects.create(
            purchase_intent=intent,
            product=intent.product,
            buyer=intent.buyer,
            seller=intent.seller,
            final_price=final_price,
            buyer_commission=commissions['buyer_commission'],
            seller_commission=commissions['seller_commission'],
            platform_commission=commissions['platform_commission'],
            seller_net=commissions['seller_net'],
            buyer_total=commissions['buyer_total']
        )
        
        # Créer la vérification de livraison avec les codes
        DeliveryVerification.objects.create(c2c_order=c2c_order)
        
        return c2c_order


class SingPayService:
    """Service pour intégrer SingPay dans le système C2C"""
    
    @staticmethod
    def init_c2c_payment(c2c_order: C2COrder, request):
        """
        Initialise un paiement SingPay pour une commande C2C
        """
        from payments.views import init_singpay_payment
        
        # Préparer les données pour SingPay
        amount = float(c2c_order.buyer_total)
        description = f"Paiement C2C - {c2c_order.product.product_name}"
        
        # Créer la transaction SingPay
        transaction_data = {
            'amount': amount,
            'currency': 'XOF',
            'customer_email': c2c_order.buyer.email,
            'customer_phone': c2c_order.buyer.profile.mobile_number if hasattr(c2c_order.buyer, 'profile') else '',
            'customer_name': c2c_order.buyer.get_full_name() or c2c_order.buyer.username,
            'description': description,
            'transaction_type': SingPayTransaction.C2C_PAYMENT,
            'internal_order_id': f"C2C-{c2c_order.id}",
            'user': c2c_order.buyer,
            'peer_product': c2c_order.product,
        }
        
        # Utiliser le service SingPay existant (à adapter selon votre implémentation)
        # Pour l'instant, on simule la création
        singpay_transaction = SingPayTransaction.objects.create(
            transaction_id=f"C2C-{c2c_order.id}-{timezone.now().timestamp()}",
            internal_order_id=transaction_data['internal_order_id'],
            amount=amount,
            currency=transaction_data['currency'],
            customer_email=transaction_data['customer_email'],
            customer_phone=transaction_data.get('customer_phone', ''),
            customer_name=transaction_data['customer_name'],
            description=description,
            transaction_type=transaction_data['transaction_type'],
            user=c2c_order.buyer,
            peer_product=c2c_order.product,
            callback_url=request.build_absolute_uri('/payments/singpay/callback/'),
            return_url=request.build_absolute_uri(f'/c2c/order/{c2c_order.id}/payment-success/'),
            status=SingPayTransaction.PENDING
        )
        
        # Lier la transaction à la commande C2C
        c2c_order.payment_transaction = singpay_transaction
        c2c_order.save()
        
        return singpay_transaction
    
    @staticmethod
    def handle_payment_success(singpay_transaction: SingPayTransaction):
        """
        Gère le succès d'un paiement SingPay pour une commande C2C
        """
        c2c_order = singpay_transaction.c2c_orders.first()
        if not c2c_order:
            logger.error(f"Aucune commande C2C trouvée pour la transaction {singpay_transaction.transaction_id}")
            return
        
        # Mettre à jour le statut de la commande
        c2c_order.status = C2COrder.PAID
        c2c_order.paid_at = timezone.now()
        c2c_order.save()
        
        # Mettre à jour le statut de la transaction
        singpay_transaction.status = SingPayTransaction.SUCCESS
        singpay_transaction.paid_at = timezone.now()
        singpay_transaction.save()
        
        return c2c_order
    
    @staticmethod
    def init_boost_payment(product: PeerToPeerProduct, user, duration, request):
        """
        Initialise un paiement SingPay pour un boost de produit
        """
        from payments.models import SingPayTransaction
        
        # Calculer le prix du boost
        price = BoostService.get_boost_price(duration)
        
        # Préparer les données pour SingPay
        amount = float(price)
        description = f"Boost produit C2C - {product.product_name} ({duration})"
        
        # Créer la transaction SingPay
        singpay_transaction = SingPayTransaction.objects.create(
            transaction_id=f"BOOST-{product.id}-{timezone.now().timestamp()}",
            internal_order_id=f"BOOST-{product.id}-{duration}",
            amount=amount,
            currency='XOF',
            customer_email=user.email,
            customer_phone=user.profile.mobile_number if hasattr(user, 'profile') else '',
            customer_name=user.get_full_name() or user.username,
            description=description,
            transaction_type=SingPayTransaction.BOOST_PAYMENT,
            user=user,
            peer_product=product,
            callback_url=request.build_absolute_uri('/payments/singpay/callback/'),
            return_url=request.build_absolute_uri(f'/c2c/boost/{product.id}/success/'),
            status=SingPayTransaction.PENDING
        )
        
        return singpay_transaction
    
    @staticmethod
    def handle_boost_payment_success(singpay_transaction: SingPayTransaction):
        """
        Gère le succès d'un paiement SingPay pour un boost
        """
        product = singpay_transaction.peer_product
        if not product:
            logger.error(f"Aucun produit trouvé pour la transaction boost {singpay_transaction.transaction_id}")
            return None
        
        # Récupérer la durée depuis l'internal_order_id (format: BOOST-{product_id}-{duration})
        try:
            duration = singpay_transaction.internal_order_id.split('-')[-1]
            if duration not in ['24h', '72h', '7d']:
                duration = '24h'  # Par défaut
        except:
            duration = '24h'
        
        # Créer le boost
        boost = BoostService.create_boost(
            product=product,
            buyer=singpay_transaction.user,
            duration=duration,
            payment_transaction=singpay_transaction
        )
        
        # Mettre à jour le statut de la transaction
        singpay_transaction.status = SingPayTransaction.SUCCESS
        singpay_transaction.paid_at = timezone.now()
        singpay_transaction.save()
        
        return boost


class DeliveryVerificationService:
    """Service pour gérer la vérification de livraison avec double code"""
    
    @staticmethod
    def verify_seller_code(c2c_order: C2COrder, code):
        """
        Vérifie le code acheteur (A-CODE) saisi par le vendeur
        Le vendeur entre le code A-CODE de l'acheteur pour confirmer qu'il a remis l'article
        """
        verification = c2c_order.delivery_verification
        # Le vendeur entre le code acheteur (A-CODE)
        if code == verification.buyer_code and not verification.seller_code_verified:
            verification.seller_code_verified = True
            verification.seller_code_verified_at = timezone.now()
            if verification.status == DeliveryVerification.PENDING:
                verification.status = DeliveryVerification.SELLER_CODE_VERIFIED
            verification.save()
            
            # Mettre à jour le statut de la commande
            if c2c_order.status == C2COrder.PAID:
                c2c_order.status = C2COrder.PENDING_DELIVERY
                c2c_order.save()
            return True
        return False
    
    @staticmethod
    def verify_buyer_code(c2c_order: C2COrder, code):
        """
        Vérifie le code vendeur (V-CODE) saisi par l'acheteur
        L'acheteur entre le code V-CODE du vendeur pour confirmer qu'il a reçu l'article
        """
        verification = c2c_order.delivery_verification
        # L'acheteur entre le code vendeur (V-CODE)
        if code == verification.seller_code and not verification.buyer_code_verified:
            verification.buyer_code_verified = True
            verification.buyer_code_verified_at = timezone.now()
            if verification.status == DeliveryVerification.SELLER_CODE_VERIFIED:
                verification.status = DeliveryVerification.COMPLETED
                verification.completed_at = timezone.now()
            elif verification.status == DeliveryVerification.PENDING:
                verification.status = DeliveryVerification.BUYER_CODE_VERIFIED
            verification.save()
            
            # Mettre à jour le statut de la commande
            if verification.status == DeliveryVerification.COMPLETED:
                c2c_order.status = C2COrder.COMPLETED
                c2c_order.completed_at = timezone.now()
                c2c_order.save()
                
                # Mettre à jour les statistiques du vendeur
                DeliveryVerificationService._update_seller_stats(c2c_order.seller)
            return True
        return False
    
    @staticmethod
    def _update_seller_stats(seller):
        """
        Met à jour les statistiques du vendeur après une transaction réussie
        """
        # Compter les transactions réussies
        successful_orders = C2COrder.objects.filter(
            seller=seller,
            status=C2COrder.COMPLETED
        ).count()
        
        # Calculer la note moyenne (à implémenter avec un système de notation)
        # Pour l'instant, on attribue les badges automatiquement
        
        # Nouveau vendeur (< 3 transactions)
        if successful_orders < 3:
            SellerBadge.objects.get_or_create(
                seller=seller,
                badge_type=SellerBadge.NEW_SELLER,
                assignment_type=SellerBadge.AUTO,
                defaults={'is_active': True}
            )
        # Bon vendeur (3-10 transactions)
        elif 3 <= successful_orders < 10:
            SellerBadge.objects.filter(
                seller=seller,
                badge_type=SellerBadge.NEW_SELLER
            ).update(is_active=False)
            SellerBadge.objects.get_or_create(
                seller=seller,
                badge_type=SellerBadge.GOOD_SELLER,
                assignment_type=SellerBadge.AUTO,
                defaults={'is_active': True}
            )
        # Vendeur sérieux (10-50 transactions)
        elif 10 <= successful_orders < 50:
            SellerBadge.objects.filter(
                seller=seller,
                badge_type__in=[SellerBadge.NEW_SELLER, SellerBadge.GOOD_SELLER]
            ).update(is_active=False)
            SellerBadge.objects.get_or_create(
                seller=seller,
                badge_type=SellerBadge.SERIOUS_SELLER,
                assignment_type=SellerBadge.AUTO,
                defaults={'is_active': True}
            )
        # Meilleur vendeur (50+ transactions)
        else:
            SellerBadge.objects.filter(
                seller=seller,
                badge_type__in=[SellerBadge.NEW_SELLER, SellerBadge.GOOD_SELLER, SellerBadge.SERIOUS_SELLER]
            ).update(is_active=False)
            SellerBadge.objects.get_or_create(
                seller=seller,
                badge_type=SellerBadge.BEST_SELLER,
                assignment_type=SellerBadge.AUTO,
                defaults={'is_active': True}
            )


class BoostService:
    """Service pour gérer les boosts de produits"""
    
    BOOST_PRICES = {
        '24h': Decimal('500'),   # 500 FCFA pour 24h
        '72h': Decimal('1200'),  # 1200 FCFA pour 72h
        '7d': Decimal('2500'),   # 2500 FCFA pour 7 jours
    }
    
    @staticmethod
    def get_boost_price(duration):
        """Retourne le prix d'un boost selon sa durée"""
        return BoostService.BOOST_PRICES.get(duration, Decimal('0'))
    
    @staticmethod
    @transaction.atomic
    def create_boost(product: PeerToPeerProduct, buyer, duration, payment_transaction=None):
        """
        Crée un boost pour un produit
        """
        # Calculer les dates
        start_date = timezone.now()
        if duration == ProductBoost.BOOST_24H:
            end_date = start_date + timedelta(hours=24)
        elif duration == ProductBoost.BOOST_72H:
            end_date = start_date + timedelta(hours=72)
        elif duration == ProductBoost.BOOST_7D:
            end_date = start_date + timedelta(days=7)
        else:
            raise ValueError(f"Durée de boost invalide: {duration}")
        
        # Désactiver les autres boosts actifs pour ce produit
        ProductBoost.objects.filter(
            product=product,
            status=ProductBoost.ACTIVE
        ).update(status=ProductBoost.EXPIRED)
        
        # Créer le nouveau boost
        boost = ProductBoost.objects.create(
            product=product,
            buyer=buyer,
            duration=duration,
            start_date=start_date,
            end_date=end_date,
            payment_transaction=payment_transaction,
            price=BoostService.get_boost_price(duration)
        )
        
        return boost

