"""
Services pour le module C2C
Abstraction de la logique métier et intégration avec SingPay
"""
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings
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
        logger.info('[C2C·SVC] create_purchase_intent product=#%d buyer=%s price=%s',
                    product.id, buyer.pk, initial_price)
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
        
        active_statuses = [
            PurchaseIntent.PENDING,
            PurchaseIntent.AWAITING_AVAILABILITY,
            PurchaseIntent.NEGOTIATING,
        ]
        existing = PurchaseIntent.objects.filter(
            product=product, buyer=buyer, status__in=active_statuses,
        ).first()
        
        if existing:
            logger.info('[C2C·SVC] Intent existante #%d réutilisée (status=%s)', existing.id, existing.status)
            return existing
        
        # Si une intention existe mais est terminée (REJECTED, CANCELLED, EXPIRED), la réactiver
        existing_terminated = PurchaseIntent.objects.filter(
            product=product,
            buyer=buyer,
            status__in=[PurchaseIntent.REJECTED, PurchaseIntent.CANCELLED, PurchaseIntent.EXPIRED]
        ).first()
        
        if existing_terminated:
            logger.info('[C2C·SVC] Réactivation intent #%d (ancien status=%s)', existing_terminated.id, existing_terminated.status)
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
        
        buyer_name = buyer.get_full_name() or buyer.username
        welcome_message = (
            f"👋 {buyer_name} souhaite acheter votre article « {product.product_name} ».\n\n"
            f"💰 Prix affiché : {initial_price:,.0f} FCFA\n\n"
            f"📦 Vendeur, veuillez d'abord confirmer que cet article est toujours disponible "
            f"à la vente via le bouton dans les « Intentions d'achat »."
        )
        
        ProductMessage.objects.create(
            conversation=conversation,
            sender=buyer,
            message=welcome_message,
        )
        
        conversation.last_message_at = timezone.now()
        conversation.save()
        
        logger.info('[C2C·SVC] Intent #%d créée — en attente de dispo (seller_notified=False)', intent.id)
        return intent
    
    @staticmethod
    def get_negotiation_offer_rules(intent: PurchaseIntent, user):
        """
        Règles « chacun son tour » :
        - Tant qu'une offre est en attente : le proposant ne peut pas en envoyer une autre ;
          l'autre doit accepter ou refuser (pas de nouvelle offre par le formulaire).
        - Après un refus : seule la personne qui n'avait PAS fait la dernière offre refusée
          peut proposer le prochain prix (contre-offre).
        Retourne (can_make_offer: bool, message_fr str ou '').
        """
        if intent.status == PurchaseIntent.PENDING or intent.status == PurchaseIntent.AWAITING_AVAILABILITY:
            return False, "Le vendeur doit d'abord confirmer la disponibilité de l'article."
        if intent.status not in (PurchaseIntent.NEGOTIATING,):
            return False, "La négociation n'est plus ouverte pour cette intention."
        pending = (
            intent.negotiations.filter(status=Negotiation.PENDING)
            .order_by('-created_at')
            .first()
        )
        if pending:
            if pending.proposer_id == user.id:
                return (
                    False,
                    "Votre proposition est en attente. L'autre partie doit répondre (accepter ou refuser) avant une nouvelle offre.",
                )
            return (
                False,
                "Une proposition est en cours : utilisez Accepter ou Refuser sur l'offre ci-dessus avant d'en proposer une nouvelle.",
            )
        last = intent.negotiations.order_by('-created_at').first()
        if last and last.status == Negotiation.REJECTED and last.proposer_id == user.id:
            return (
                False,
                "Après ce refus, c'est au tour de l'autre partie de faire la prochaine proposition de prix.",
            )
        return True, ''
    
    @staticmethod
    def create_negotiation(intent: PurchaseIntent, proposer, proposed_price, message=None):
        """
        Crée une proposition de négociation
        """
        logger.info('[C2C·SVC] create_negotiation intent=#%d proposer=%s price=%s',
                    intent.id, proposer.pk, proposed_price)
        can, msg = PurchaseIntentService.get_negotiation_offer_rules(intent, proposer)
        if not can:
            logger.warning('[C2C·SVC] Offre bloquée pour intent=#%d: %s', intent.id, msg)
            raise ValidationError(msg)
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
        logger.info('[C2C·SVC] accept_negotiation #%d actor=%s price=%s',
                    negotiation.id, actor.pk, negotiation.proposed_price)
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
        logger.info('[C2C·SVC] reject_negotiation #%d actor=%s', negotiation.id, actor.pk)
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
        logger.info('[C2C·SVC] accept_final_price intent=#%d price=%s', intent.id, final_price)
        existing_order = C2COrder.objects.filter(purchase_intent=intent).first()
        if existing_order:
            logger.info('[C2C·SVC] Commande existante #%d retournée', existing_order.id)
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
        
        verification = DeliveryVerification.objects.create(c2c_order=c2c_order)
        logger.info('[C2C·SVC] Commande #%d créée — buyer_total=%s seller_net=%s — verification #%d',
                    c2c_order.id, c2c_order.buyer_total, c2c_order.seller_net, verification.id)
        
        return c2c_order


class SingPayService:
    """Service pour intégrer SingPay dans le système C2C"""
    
    @staticmethod
    def init_c2c_payment(c2c_order: C2COrder, request):
        """
        Initialise un paiement SingPay pour une commande C2C via l'API réelle
        """
        from payments.services.singpay import singpay_service
        from accounts.models import Profile
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Préparer les données pour SingPay
        amount = float(c2c_order.buyer_total)
        currency = 'XOF'
        order_id = f"C2C-{c2c_order.id}"
        description = f"Paiement C2C - {c2c_order.product.product_name}"
        
        # Récupérer les informations du client
        customer_email = c2c_order.buyer.email
        customer_name = c2c_order.buyer.get_full_name() or c2c_order.buyer.username
        
        # Formater le numéro de téléphone en format international
        def format_phone_international(phone):
            """Formate le numéro de téléphone en format international (+241XXXXXXXXX)"""
            if not phone:
                return ''
            # Supprimer les espaces et caractères spéciaux
            phone = ''.join(filter(str.isdigit, phone))
            # Si le numéro commence par 0, remplacer par +241 (Gabon)
            if phone.startswith('0'):
                phone = '+241' + phone[1:]
            # Si le numéro ne commence pas par +, ajouter +241
            elif not phone.startswith('+'):
                if phone.startswith('241'):
                    phone = '+' + phone
                else:
                    phone = '+241' + phone
            return phone
        
        # Récupérer le numéro de téléphone
        customer_phone = ''
        try:
            profile = Profile.objects.get(user=c2c_order.buyer)
            if profile.mobile_number:
                customer_phone = format_phone_international(profile.mobile_number)
        except Profile.DoesNotExist:
            pass
        
        # Construire les URLs
        # En développement (DEBUG=True), utiliser localhost
        # En production, utiliser le domaine de production
        if settings.DEBUG:
            # Mode développement : utiliser localhost
            base_url = f"{request.scheme}://{request.get_host()}"
        else:
            # Mode production : utiliser le domaine de production
            production_domain = getattr(settings, 'SINGPAY_PRODUCTION_DOMAIN', 'gabomazone.pythonanywhere.com')
            base_url = f"https://{production_domain}"
        
        callback_url = f"{base_url}/payments/singpay/callback/"
        return_url = f"{base_url}/c2c/order/{c2c_order.id}/payment-success/"
        
        # Métadonnées
        metadata = {
            'order_id': str(c2c_order.id),
            'user_id': str(c2c_order.buyer.id),
            'payment_type': 'c2c_payment',
            'product_id': str(c2c_order.product.id),
        }
        
        # Initialiser le paiement via l'API SingPay
        logger.info(f"Initialisation paiement SingPay pour commande C2C #{c2c_order.id}")
        success, response = singpay_service.init_payment(
            amount=amount,
            currency=currency,
            order_id=order_id,
            customer_email=customer_email,
            customer_phone=customer_phone,
            customer_name=customer_name,
            description=description,
            callback_url=callback_url,
            return_url=return_url,
            metadata=metadata
        )
        
        if not success:
            error_message = response.get('error', 'Erreur lors de l\'initialisation du paiement')
            logger.error(f"Erreur SingPay init_payment pour la commande C2C {c2c_order.id}: {error_message}")
            raise Exception(f"Erreur lors de l'initialisation du paiement: {error_message}")
        
        # Créer la transaction SingPay
        payment_url = response.get('payment_url')
        transaction_id = response.get('transaction_id')
        reference = response.get('reference')
        expires_at_str = response.get('expires_at')
        
        # Parser la date d'expiration si elle existe
        expires_at = None
        if expires_at_str:
            try:
                from datetime import datetime
                import re
                
                expires_at_str_clean = str(expires_at_str).strip()
                parsed = False
                
                # Essayer d'abord avec regex pour gérer le format américain "1/9/2026, 11:41:11 PM"
                match = re.match(r'(\d+)/(\d+)/(\d+), (\d+):(\d+):(\d+) (AM|PM)', expires_at_str_clean)
                if match:
                    try:
                        month, day, year, hour, minute, second, am_pm = match.groups()
                        hour = int(hour)
                        if am_pm == 'PM' and hour != 12:
                            hour += 12
                        elif am_pm == 'AM' and hour == 12:
                            hour = 0
                        expires_at = datetime(int(year), int(month), int(day), hour, int(minute), int(second))
                        parsed = True
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Erreur lors de la construction de la date depuis regex: {e}")
                
                if not parsed:
                    # Essayer le format ISO
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str_clean.replace('Z', '+00:00'))
                        parsed = True
                    except ValueError:
                        try:
                            # Essayer le format avec T
                            expires_at = datetime.strptime(expires_at_str_clean, "%Y-%m-%dT%H:%M:%S")
                            parsed = True
                        except ValueError:
                            logger.warning(f"Impossible de parser expires_at: {expires_at_str}")
                            expires_at = None
                
                # Convertir en timezone-aware si nécessaire
                if expires_at and timezone.is_naive(expires_at):
                    expires_at = timezone.make_aware(expires_at)
            except Exception as e:
                logger.warning(f"Erreur lors du parsing de expires_at: {e}")
                expires_at = None
        
        # Vérifier si une transaction existe déjà pour cette commande C2C
        existing_transaction = None
        
        # Chercher une transaction existante par transaction_id
        if transaction_id:
            try:
                existing_transaction = SingPayTransaction.objects.get(transaction_id=transaction_id)
            except SingPayTransaction.DoesNotExist:
                pass
        
        # Si pas trouvée par transaction_id, chercher par commande C2C
        if not existing_transaction:
            try:
                existing_transaction = SingPayTransaction.objects.filter(
                    peer_product=c2c_order.product,
                    user=c2c_order.buyer,
                    transaction_type=SingPayTransaction.C2C_PAYMENT,
                    status=SingPayTransaction.PENDING
                ).first()
            except Exception:
                pass
        
        if existing_transaction:
            # Mettre à jour la transaction existante
            logger.info(f"Transaction C2C existante trouvée: {existing_transaction.transaction_id}, mise à jour...")
            existing_transaction.payment_url = payment_url
            existing_transaction.callback_url = callback_url
            existing_transaction.return_url = return_url
            existing_transaction.expires_at = expires_at
            if transaction_id and existing_transaction.transaction_id != transaction_id:
                existing_transaction.transaction_id = transaction_id
            if reference:
                existing_transaction.reference = reference
            existing_transaction.save()
            singpay_transaction = existing_transaction
        else:
            # Créer une nouvelle transaction
            singpay_transaction = SingPayTransaction.objects.create(
                transaction_id=transaction_id,
                reference=reference,
                internal_order_id=order_id,
                amount=amount,
                currency=currency,
                customer_email=customer_email,
                customer_phone=customer_phone,
                customer_name=customer_name,
                description=description,
                transaction_type=SingPayTransaction.C2C_PAYMENT,
                user=c2c_order.buyer,
                peer_product=c2c_order.product,
                callback_url=callback_url,
                return_url=return_url,
                payment_url=payment_url,
                status=SingPayTransaction.PENDING,
                expires_at=expires_at
            )
        
        # Ajouter les métadonnées pour faciliter la recherche d'escrow
        if not singpay_transaction.metadata:
            singpay_transaction.metadata = {}
        singpay_transaction.metadata['c2c_order_id'] = c2c_order.id
        singpay_transaction.save()
        
        # Lier la transaction à la commande C2C
        c2c_order.payment_transaction = singpay_transaction
        c2c_order.save()
        
        logger.info(f"Transaction SingPay créée: {transaction_id} pour commande C2C #{c2c_order.id}")
        
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
        
        # Traçabilité : paiement reçu, fonds en escrow
        try:
            from .models import C2CPaymentEvent
            C2CPaymentEvent.log_event(
                c2c_order=c2c_order,
                event_type=C2CPaymentEvent.PAID_ESCROW,
                transaction=singpay_transaction,
            )
        except Exception as e:
            logger.warning(f"Log C2CPaymentEvent PAID_ESCROW non enregistré: {e}")
        
        return c2c_order
    
    @staticmethod
    def init_boost_payment(product: PeerToPeerProduct, user, duration, request):
        """
        Initialise un paiement SingPay pour un boost de produit C2C
        Utilise l'API SingPay réelle pour créer le paiement
        """
        from payments.models import SingPayTransaction
        from payments.services.singpay import singpay_service
        from accounts.models import Profile
        
        # Calculer le prix du boost
        price = BoostService.get_boost_price(duration)
        
        # Préparer les données pour SingPay
        amount = float(price)
        description = f"Boost produit C2C - {product.product_name} ({duration})"
        order_id = f"BOOST-C2C-{product.id}-{duration}"
        
        # Récupérer le téléphone du client
        customer_phone = ''
        try:
            profile = Profile.objects.get(user=user)
            customer_phone = profile.mobile_number or ''
        except Profile.DoesNotExist:
            pass
        
        # Construire les URLs
        if settings.DEBUG:
            base_url = f"{request.scheme}://{request.get_host()}"
        else:
            production_domain = getattr(settings, 'SINGPAY_PRODUCTION_DOMAIN', 'gabomazone.pythonanywhere.com')
            base_url = f"https://{production_domain}"
        
        callback_url = f"{base_url}/payments/singpay/callback/"
        return_url = f"{base_url}/c2c/boost/{product.id}/success/"
        
        # Initialiser le paiement via l'API SingPay
        success, response = singpay_service.init_payment(
            amount=amount,
            currency='XOF',
            order_id=order_id,
            customer_email=user.email,
            customer_phone=customer_phone,
            customer_name=user.get_full_name() or user.username,
            description=description,
            callback_url=callback_url,
            return_url=return_url,
            metadata={
                'product_id': product.id,
                'product_name': product.product_name,
                'boost_duration': duration,
                'boost_type': 'c2c'
            }
        )
        
        if not success:
            error_message = response.get('error', 'Erreur lors de l\'initialisation du paiement')
            logger.error(f"Erreur SingPay init_payment pour boost C2C: {error_message}")
            raise Exception(f"Erreur lors de l'initialisation du paiement: {error_message}")
        
        # Extraire les informations de la réponse
        payment_url = response.get('payment_url')
        transaction_id = response.get('transaction_id')
        reference = response.get('reference')
        expires_at_str = response.get('expires_at')
        
        # Parser la date d'expiration
        expires_at = None
        if expires_at_str:
            try:
                from datetime import datetime
                import re
                
                expires_at_str_clean = str(expires_at_str).strip()
                parsed = False
                
                # Essayer le format "1/9/2026, 11:41:11 PM"
                match = re.match(r'(\d+)/(\d+)/(\d+), (\d+):(\d+):(\d+) (AM|PM)', expires_at_str_clean)
                if match:
                    try:
                        month, day, year, hour, minute, second, am_pm = match.groups()
                        hour = int(hour)
                        if am_pm == 'PM' and hour != 12:
                            hour += 12
                        elif am_pm == 'AM' and hour == 12:
                            hour = 0
                        expires_at = datetime(int(year), int(month), int(day), hour, int(minute), int(second))
                        parsed = True
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Erreur lors de la construction de la date depuis regex: {e}")
                
                if not parsed:
                    # Essayer le format ISO
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str_clean.replace('Z', '+00:00'))
                        parsed = True
                    except ValueError:
                        try:
                            expires_at = datetime.strptime(expires_at_str_clean, "%Y-%m-%dT%H:%M:%S")
                            parsed = True
                        except ValueError:
                            logger.warning(f"Impossible de parser expires_at: {expires_at_str}")
                            expires_at = None
                
                if expires_at and timezone.is_naive(expires_at):
                    expires_at = timezone.make_aware(expires_at)
            except Exception as e:
                logger.warning(f"Erreur lors du parsing de expires_at: {e}")
                expires_at = None
        
        # Créer ou mettre à jour la transaction SingPay
        singpay_transaction, created = SingPayTransaction.objects.get_or_create(
            transaction_id=transaction_id,
            defaults={
                'reference': reference,
                'internal_order_id': order_id,
                'amount': amount,
                'currency': 'XOF',
                'status': SingPayTransaction.PENDING,
                'transaction_type': SingPayTransaction.BOOST_PAYMENT,
                'customer_email': user.email,
                'customer_phone': customer_phone,
                'customer_name': user.get_full_name() or user.username,
                'payment_url': payment_url,
                'callback_url': callback_url,
                'return_url': return_url,
                'user': user,
                'peer_product': product,
                'description': description,
                'expires_at': expires_at
            }
        )
        
        if not created:
            # Mettre à jour la transaction existante
            singpay_transaction.payment_url = payment_url
            singpay_transaction.callback_url = callback_url
            singpay_transaction.return_url = return_url
            singpay_transaction.expires_at = expires_at
            singpay_transaction.save()
        
        logger.info(f"Paiement boost C2C initialisé pour produit #{product.id}, transaction: {transaction_id}")
        
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
        except Exception:
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
        logger.info('[C2C·SVC] verify_seller_code order=#%d code=%s…', c2c_order.id, code[:2] if code else '?')
        verification = c2c_order.delivery_verification
        if code == verification.buyer_code and not verification.seller_code_verified:
            verification.seller_code_verified = True
            verification.seller_code_verified_at = timezone.now()
            if verification.status == DeliveryVerification.PENDING:
                verification.status = DeliveryVerification.SELLER_CODE_VERIFIED
            verification.save()
            
            if c2c_order.status == C2COrder.PAID:
                c2c_order.status = C2COrder.PENDING_DELIVERY
                c2c_order.save()
            logger.info('[C2C·SVC] seller_code vérifié OK order=#%d → status=%s', c2c_order.id, verification.status)
            return True
        logger.warning('[C2C·SVC] seller_code FAIL order=#%d (mismatch ou déjà vérifié)', c2c_order.id)
        return False
    
    @staticmethod
    def verify_buyer_code(c2c_order: C2COrder, code):
        """
        Vérifie le code vendeur (V-CODE) saisi par l'acheteur
        L'acheteur entre le code V-CODE du vendeur pour confirmer qu'il a reçu l'article
        """
        logger.info('[C2C·SVC] verify_buyer_code order=#%d code=%s…', c2c_order.id, code[:2] if code else '?')
        verification = c2c_order.delivery_verification
        if code == verification.seller_code and not verification.buyer_code_verified:
            verification.buyer_code_verified = True
            verification.buyer_code_verified_at = timezone.now()
            if verification.status == DeliveryVerification.SELLER_CODE_VERIFIED:
                verification.status = DeliveryVerification.COMPLETED
                verification.completed_at = timezone.now()
            elif verification.status == DeliveryVerification.PENDING:
                verification.status = DeliveryVerification.BUYER_CODE_VERIFIED
            verification.save()
            
            if verification.status == DeliveryVerification.COMPLETED:
                c2c_order.status = C2COrder.COMPLETED
                c2c_order.completed_at = timezone.now()
                c2c_order.save()
                logger.info('[C2C·SVC] 🎉 TRANSACTION COMPLÈTE order=#%d — mise à jour stats vendeur', c2c_order.id)
                DeliveryVerificationService._update_seller_stats(c2c_order.seller)
            else:
                logger.info('[C2C·SVC] buyer_code vérifié OK order=#%d → verif_status=%s', c2c_order.id, verification.status)
            return True
        logger.warning('[C2C·SVC] buyer_code FAIL order=#%d (mismatch ou déjà vérifié)', c2c_order.id)
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

