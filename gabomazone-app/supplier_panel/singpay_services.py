"""
Services SingPay pour l'espace vendeur B2C
Gère les paiements d'abonnements premium et de boosts de produits
"""
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from payments.services.singpay import singpay_service
from payments.models import SingPayTransaction
from accounts.models import Profile, PremiumSubscription, ProductBoostRequest
from products.models import Product

logger = logging.getLogger(__name__)


class B2CSingPayService:
    """Service pour intégrer SingPay dans l'espace vendeur B2C"""
    
    # Prix de l'abonnement premium (mensuel)
    PREMIUM_SUBSCRIPTION_PRICE = Decimal('50000')  # 50 000 FCFA par mois
    
    @staticmethod
    def init_subscription_payment(vendor_profile: Profile, request):
        """
        Initialise un paiement SingPay pour un abonnement premium B2C
        
        Args:
            vendor_profile: Profil du vendeur
            request: Objet request Django
            
        Returns:
            tuple: (success: bool, response: dict ou SingPayTransaction)
        """
        try:
            user = vendor_profile.user
            
            # Vérifier si un abonnement actif existe déjà
            existing_subscription = PremiumSubscription.objects.filter(
                vendor=vendor_profile,
                status=PremiumSubscription.ACTIVE
            ).first()
            
            if existing_subscription and existing_subscription.is_active():
                return False, {'error': 'Vous avez déjà un abonnement premium actif'}
            
            # Calculer le montant
            amount = float(B2CSingPayService.PREMIUM_SUBSCRIPTION_PRICE)
            order_id = f"SUBSCRIPTION-B2C-{vendor_profile.id}-{timezone.now().timestamp()}"
            description = f"Abonnement premium B2C - {user.get_full_name() or user.username}"
            
            # Récupérer le téléphone
            customer_phone = vendor_profile.mobile_number or ''
            
            # Construire les URLs
            if settings.DEBUG:
                base_url = f"{request.scheme}://{request.get_host()}"
            else:
                production_domain = getattr(settings, 'SINGPAY_PRODUCTION_DOMAIN', 'gabomazone.pythonanywhere.com')
                base_url = f"https://{production_domain}"
            
            callback_url = f"{base_url}/payments/singpay/callback/"
            return_url = f"{base_url}/supplier/subscriptions/success/"
            
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
                    'vendor_id': vendor_profile.id,
                    'vendor_username': user.username,
                    'subscription_type': 'premium',
                    'subscription_duration': '1_month'
                }
            )
            
            if not success:
                error_message = response.get('error', 'Erreur lors de l\'initialisation du paiement')
                logger.error(f"Erreur SingPay init_payment pour abonnement: {error_message}")
                return False, {'error': error_message}
            
            # Extraire les informations de la réponse
            payment_url = response.get('payment_url')
            transaction_id = response.get('transaction_id')
            reference = response.get('reference')
            expires_at_str = response.get('expires_at')
            
            # Parser la date d'expiration
            expires_at = B2CSingPayService._parse_expires_at(expires_at_str)
            
            # Créer ou mettre à jour la transaction SingPay
            singpay_transaction, created = SingPayTransaction.objects.get_or_create(
                transaction_id=transaction_id,
                defaults={
                    'reference': reference,
                    'internal_order_id': order_id,
                    'amount': amount,
                    'currency': 'XOF',
                    'status': SingPayTransaction.PENDING,
                    'transaction_type': SingPayTransaction.SUBSCRIPTION_PAYMENT,
                    'customer_email': user.email,
                    'customer_phone': customer_phone,
                    'customer_name': user.get_full_name() or user.username,
                    'payment_url': payment_url,
                    'callback_url': callback_url,
                    'return_url': return_url,
                    'user': user,
                    'description': description,
                    'expires_at': expires_at,
                    'metadata': {
                        'vendor_id': vendor_profile.id,
                        'subscription_type': 'premium'
                    }
                }
            )
            
            if not created:
                # Mettre à jour la transaction existante
                singpay_transaction.payment_url = payment_url
                singpay_transaction.callback_url = callback_url
                singpay_transaction.return_url = return_url
                singpay_transaction.expires_at = expires_at
                singpay_transaction.save()
            
            logger.info(f"Paiement abonnement B2C initialisé pour vendeur #{vendor_profile.id}, transaction: {transaction_id}")
            
            return True, singpay_transaction
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'initialisation du paiement d'abonnement: {str(e)}")
            return False, {'error': str(e)}
    
    @staticmethod
    def init_boost_payment(boost_request: ProductBoostRequest, request):
        """
        Initialise un paiement SingPay pour un boost de produit B2C
        
        Args:
            boost_request: Demande de boost (ProductBoostRequest)
            request: Objet request Django
            
        Returns:
            tuple: (success: bool, response: dict ou SingPayTransaction)
        """
        try:
            vendor_profile = boost_request.vendor
            product = boost_request.product
            user = vendor_profile.user
            
            # Vérifier que la demande est en attente
            if boost_request.status != ProductBoostRequest.PENDING:
                return False, {'error': 'Cette demande de boost n\'est plus en attente'}
            
            # Calculer le montant
            amount = float(boost_request.price)
            if amount <= 0:
                return False, {'error': 'Le montant du boost est invalide'}
            
            order_id = f"BOOST-B2C-{product.id}-{boost_request.id}"
            description = f"Boost produit B2C - {product.product_name} ({boost_request.duration_days} jours)"
            
            # Récupérer le téléphone
            customer_phone = vendor_profile.mobile_number or ''
            
            # Construire les URLs
            if settings.DEBUG:
                base_url = f"{request.scheme}://{request.get_host()}"
            else:
                production_domain = getattr(settings, 'SINGPAY_PRODUCTION_DOMAIN', 'gabomazone.pythonanywhere.com')
                base_url = f"https://{production_domain}"
            
            callback_url = f"{base_url}/payments/singpay/callback/"
            return_url = f"{base_url}/supplier/subscriptions/boost-success/{boost_request.id}/"
            
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
                    'vendor_id': vendor_profile.id,
                    'product_id': product.id,
                    'product_name': product.product_name,
                    'boost_request_id': boost_request.id,
                    'boost_duration_days': boost_request.duration_days,
                    'boost_percentage': boost_request.boost_percentage,
                    'boost_type': 'b2c'
                }
            )
            
            if not success:
                error_message = response.get('error', 'Erreur lors de l\'initialisation du paiement')
                logger.error(f"Erreur SingPay init_payment pour boost B2C: {error_message}")
                return False, {'error': error_message}
            
            # Extraire les informations de la réponse
            payment_url = response.get('payment_url')
            transaction_id = response.get('transaction_id')
            reference = response.get('reference')
            expires_at_str = response.get('expires_at')
            
            # Parser la date d'expiration
            expires_at = B2CSingPayService._parse_expires_at(expires_at_str)
            
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
                    'product': product,
                    'description': description,
                    'expires_at': expires_at,
                    'metadata': {
                        'vendor_id': vendor_profile.id,
                        'product_id': product.id,
                        'boost_request_id': boost_request.id,
                        'boost_type': 'b2c'
                    }
                }
            )
            
            if not created:
                # Mettre à jour la transaction existante
                singpay_transaction.payment_url = payment_url
                singpay_transaction.callback_url = callback_url
                singpay_transaction.return_url = return_url
                singpay_transaction.expires_at = expires_at
                singpay_transaction.save()
            
            logger.info(f"Paiement boost B2C initialisé pour produit #{product.id}, transaction: {transaction_id}")
            
            return True, singpay_transaction
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'initialisation du paiement de boost: {str(e)}")
            return False, {'error': str(e)}
    
    @staticmethod
    def handle_subscription_payment_success(singpay_transaction: SingPayTransaction):
        """
        Gère le succès d'un paiement d'abonnement premium B2C
        
        Args:
            singpay_transaction: Transaction SingPay réussie
            
        Returns:
            PremiumSubscription: L'abonnement créé ou mis à jour
        """
        try:
            metadata = singpay_transaction.metadata or {}
            vendor_id = metadata.get('vendor_id')
            
            if not vendor_id:
                logger.error(f"vendor_id manquant dans les métadonnées de la transaction {singpay_transaction.transaction_id}")
                return None
            
            vendor_profile = Profile.objects.get(id=vendor_id)
            
            # Calculer les dates
            start_date = timezone.now()
            end_date = start_date + timedelta(days=30)  # 1 mois
            
            # Créer ou mettre à jour l'abonnement
            subscription, created = PremiumSubscription.objects.get_or_create(
                vendor=vendor_profile,
                defaults={
                    'status': PremiumSubscription.ACTIVE,
                    'start_date': start_date,
                    'end_date': end_date,
                    'price': float(singpay_transaction.amount),
                    'payment_status': True
                }
            )
            
            if not created:
                # Mettre à jour l'abonnement existant
                subscription.status = PremiumSubscription.ACTIVE
                subscription.start_date = start_date
                subscription.end_date = end_date
                subscription.price = float(singpay_transaction.amount)
                subscription.payment_status = True
                subscription.save()
            
            # Mettre à jour le statut de la transaction
            singpay_transaction.status = SingPayTransaction.SUCCESS
            singpay_transaction.paid_at = timezone.now()
            singpay_transaction.save()
            
            logger.info(f"Abonnement premium activé pour vendeur #{vendor_profile.id}")
            
            return subscription
            
        except Profile.DoesNotExist:
            logger.error(f"Profil vendeur non trouvé pour vendor_id: {vendor_id}")
            return None
        except Exception as e:
            logger.exception(f"Erreur lors de l'activation de l'abonnement: {str(e)}")
            return None
    
    @staticmethod
    def handle_boost_payment_success(singpay_transaction: SingPayTransaction):
        """
        Gère le succès d'un paiement de boost de produit B2C
        
        Args:
            singpay_transaction: Transaction SingPay réussie
            
        Returns:
            ProductBoostRequest: La demande de boost mise à jour
        """
        try:
            metadata = singpay_transaction.metadata or {}
            boost_request_id = metadata.get('boost_request_id')
            
            if not boost_request_id:
                logger.error(f"boost_request_id manquant dans les métadonnées de la transaction {singpay_transaction.transaction_id}")
                return None
            
            boost_request = ProductBoostRequest.objects.get(id=boost_request_id)
            
            # Calculer les dates
            start_date = timezone.now()
            end_date = start_date + timedelta(days=boost_request.duration_days)
            
            # Mettre à jour la demande de boost
            boost_request.status = ProductBoostRequest.ACTIVE
            boost_request.payment_status = True
            boost_request.start_date = start_date
            boost_request.end_date = end_date
            boost_request.approved_date = start_date
            boost_request.save()
            
            # Mettre à jour le statut de la transaction
            singpay_transaction.status = SingPayTransaction.SUCCESS
            singpay_transaction.paid_at = timezone.now()
            singpay_transaction.save()
            
            logger.info(f"Boost B2C activé pour produit #{boost_request.product.id}, demande #{boost_request.id}")
            
            return boost_request
            
        except ProductBoostRequest.DoesNotExist:
            logger.error(f"Demande de boost non trouvée pour boost_request_id: {boost_request_id}")
            return None
        except Exception as e:
            logger.exception(f"Erreur lors de l'activation du boost: {str(e)}")
            return None
    
    @staticmethod
    def _parse_expires_at(expires_at_str):
        """
        Parse la date d'expiration depuis différents formats
        
        Args:
            expires_at_str: String de date à parser
            
        Returns:
            datetime ou None
        """
        if not expires_at_str:
            return None
        
        try:
            from datetime import datetime
            import re
            
            expires_at_str_clean = str(expires_at_str).strip()
            parsed = False
            expires_at = None
            
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
            
            return expires_at
            
        except Exception as e:
            logger.warning(f"Erreur lors du parsing de expires_at: {e}")
            return None



