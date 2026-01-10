"""
Vues pour les paiements SingPay
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
import json
import logging

from .models import SingPayTransaction, SingPayWebhookLog
from .services.singpay import singpay_service
from orders.models import Order, Payment as OrderPayment
from accounts.models import Profile

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
def init_singpay_payment(request):
    """
    Initialise un paiement SingPay
    Endpoint pour Flutter WebView et web
    """
    try:
        # Récupérer la commande
        order_id = request.session.get('order_id')
        if not order_id:
            return JsonResponse({
                'success': False,
                'error': 'Aucune commande trouvée'
            }, status=400)
        
        order = get_object_or_404(Order, id=order_id, is_finished=False)
        
        # Récupérer les informations de paiement
        try:
            payment_info = OrderPayment.objects.get(order=order)
        except OrderPayment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Informations de paiement non trouvées. Veuillez remplir le formulaire de facturation.'
            }, status=400)
        
        # Mettre à jour le mode de paiement
        payment_info.payment_method = 'SingPay'
        payment_info.save()
        
        # Calculer le montant
        amount = float(order.amount)
        currency = 'XOF'  # FCFA
        
        # Construire les URLs (absolues pour la production)
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
        # URL de retour après paiement - doit être accessible sans authentification
        return_url = f"{base_url}/payments/singpay/return/"
        
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
        
        customer_phone = format_phone_international(payment_info.phone)
        
        # Métadonnées
        metadata = {
            'order_id': str(order.id),
            'user_id': str(request.user.id) if request.user.is_authenticated else None,
            'payment_type': 'order_payment',
        }
        
        # Initialiser le paiement SingPay
        success, response = singpay_service.init_payment(
            amount=amount,
            currency=currency,
            order_id=f"ORDER-{order.id}",
            customer_email=payment_info.Email_Address,
            customer_phone=customer_phone,
            customer_name=f"{payment_info.first_name} {payment_info.last_name}",
            description=f"Paiement commande #{order.id}",
            callback_url=callback_url,
            return_url=return_url,
            metadata=metadata
        )
        
        if not success:
            error_message = response.get('error', 'Erreur lors de l\'initialisation du paiement')
            logger.error(f"Erreur SingPay init_payment pour la commande {order.id}: {error_message}")
            logger.error(f"Détails de la réponse: {response}")
            
            # Vérifier si on est en mode bypass
            bypass_mode = getattr(settings, 'SINGPAY_BYPASS_API', True)
            if not bypass_mode:
                # En mode production, donner plus de détails sur l'erreur
                api_error = response.get('api_error', {})
                if api_error:
                    error_message = api_error.get('message', error_message)
            
            return JsonResponse({
                'success': False,
                'error': error_message,
                'details': response.get('details', '') if isinstance(response, dict) else ''
            }, status=500)
        
        # Créer la transaction dans la base de données
        from datetime import timedelta, datetime
        expires_at = None
        expires_at_str = response.get('expires_at')
        if expires_at_str:
            try:
                # Parser la date - peut être au format ISO ou format américain "1/9/2026, 11:41:11 PM"
                if isinstance(expires_at_str, str):
                    # Essayer le format ISO d'abord
                    if 'T' in expires_at_str or expires_at_str.count('-') >= 2:
                        try:
                            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                        except ValueError:
                            # Essayer le format américain "1/9/2026, 11:41:11 PM"
                            try:
                                expires_at = datetime.strptime(expires_at_str, "%m/%d/%Y, %I:%M:%S %p")
                            except ValueError:
                                logger.warning(f"Format de date non reconnu: {expires_at_str}")
                                expires_at = None
                    else:
                        # Essayer le format américain "1/9/2026, 11:41:11 PM"
                        try:
                            expires_at = datetime.strptime(expires_at_str, "%m/%d/%Y, %I:%M:%S %p")
                        except ValueError:
                            logger.warning(f"Format de date non reconnu: {expires_at_str}")
                            expires_at = None
                    
                    # Convertir en timezone aware si nécessaire
                    if expires_at and timezone.is_naive(expires_at):
                        expires_at = timezone.make_aware(expires_at)
                elif isinstance(expires_at_str, datetime):
                    expires_at = expires_at_str
                    if timezone.is_naive(expires_at):
                        expires_at = timezone.make_aware(expires_at)
            except Exception as e:
                logger.warning(f"Erreur parsing expires_at: {e}")
                expires_at = None
        
        # Si pas de date d'expiration, utiliser une valeur par défaut (24h)
        if not expires_at:
            expires_at = timezone.now() + timedelta(hours=24)
        
        # S'assurer que la commande a un utilisateur associé
        if not order.user and request.user.is_authenticated:
            order.user = request.user
            order.save()
        elif not order.user and payment_info.Email_Address:
            # Si pas d'utilisateur authentifié, essayer de trouver par email
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(email=payment_info.Email_Address)
                order.user = user
                order.save()
            except User.DoesNotExist:
                pass
        
        # S'assurer que l'URL de paiement est absolue
        payment_url = response.get('payment_url', '')
        logger.info(f"URL de paiement reçue: {payment_url}")
        logger.info(f"Base URL du serveur: {base_url}")
        
        if payment_url:
            # Si l'URL est relative, la rendre absolue avec le base_url du serveur Django
            if not payment_url.startswith('http://') and not payment_url.startswith('https://'):
                # URL relative - la convertir en absolue avec le base_url du serveur
                if payment_url.startswith('/'):
                    payment_url = f"{base_url}{payment_url}"
                else:
                    payment_url = f"{base_url}/{payment_url}"
                logger.info(f"URL convertie en absolue: {payment_url}")
            else:
                # URL déjà absolue (de l'API SingPay réelle)
                logger.info(f"URL déjà absolue: {payment_url}")
        
        # Vérifier si une transaction existe déjà pour cette commande
        transaction_id = response.get('transaction_id')
        
        # S'assurer que transaction_id existe
        # init_payment devrait toujours retourner un transaction_id (soit de l'API, soit généré)
        if not transaction_id:
            import uuid
            # Utiliser la référence si disponible, sinon générer un ID basé sur order.id
            reference = response.get('reference')
            if reference:
                transaction_id = f"{reference}-{uuid.uuid4().hex[:8].upper()}"
            else:
                transaction_id = f"TXN-{order.id}-{uuid.uuid4().hex[:12].upper()}"
            logger.error(f"transaction_id manquant dans la réponse de init_payment! Génération d'un ID de secours: {transaction_id}")
            logger.error(f"Réponse complète: {response}")
        
        logger.info(f"Transaction ID à utiliser: {transaction_id}")
        logger.info(f"Référence: {response.get('reference')}")
        logger.info(f"URL de paiement: {response.get('payment_url')}")
        existing_transaction = None
        
        # Chercher une transaction existante par transaction_id ou par order
        if transaction_id:
            try:
                existing_transaction = SingPayTransaction.objects.get(transaction_id=transaction_id)
                logger.info(f"Transaction existante trouvée par transaction_id: {existing_transaction.transaction_id}")
            except SingPayTransaction.DoesNotExist:
                pass
        
        # Si pas trouvée par transaction_id, chercher par order
        if not existing_transaction:
            try:
                existing_transaction = SingPayTransaction.objects.filter(
                    order=order,
                    status=SingPayTransaction.PENDING
                ).first()
                if existing_transaction:
                    logger.info(f"Transaction existante trouvée par order: {existing_transaction.transaction_id}")
            except Exception as e:
                logger.warning(f"Erreur lors de la recherche par order: {e}")
                pass
        
        if existing_transaction:
            # Mettre à jour la transaction existante
            logger.info(f"Transaction existante trouvée: {existing_transaction.transaction_id}, mise à jour...")
            existing_transaction.payment_url = payment_url
            existing_transaction.callback_url = callback_url
            existing_transaction.return_url = return_url
            existing_transaction.expires_at = expires_at
            # Ne pas changer le transaction_id si la transaction existe déjà (pour éviter les conflits)
            # if transaction_id and existing_transaction.transaction_id != transaction_id:
            #     logger.info(f"Mise à jour du transaction_id de {existing_transaction.transaction_id} vers {transaction_id}")
            #     existing_transaction.transaction_id = transaction_id
            if response.get('reference'):
                existing_transaction.reference = response.get('reference')
            existing_transaction.save()
            transaction = existing_transaction
        else:
            # Créer une nouvelle transaction
            logger.info(f"Création d'une nouvelle transaction avec transaction_id: {transaction_id}")
            try:
                transaction = SingPayTransaction.objects.create(
                    transaction_id=transaction_id,
                    reference=response.get('reference'),
                    internal_order_id=f"ORDER-{order.id}",
                    amount=amount,
                    currency=currency,
                    status=SingPayTransaction.PENDING,
                    transaction_type=SingPayTransaction.ORDER_PAYMENT,
                    customer_email=payment_info.Email_Address,
                    customer_phone=customer_phone,
                    customer_name=f"{payment_info.first_name} {payment_info.last_name}",
                    payment_url=payment_url,
                    callback_url=callback_url,
                    return_url=return_url,
                    user=order.user if order.user else (request.user if request.user.is_authenticated else None),
                    order=order,
                    description=f"Paiement commande #{order.id}",
                    metadata=metadata,
                    expires_at=expires_at
                )
                logger.info(f"Transaction créée avec succès: {transaction.transaction_id} (ID: {transaction.id})")
            except Exception as e:
                logger.error(f"Erreur lors de la création de la transaction: {e}")
                logger.error(f"Données de la transaction: transaction_id={transaction_id}, order={order.id}")
                # Si erreur de contrainte unique, essayer de récupérer la transaction existante
                if 'UNIQUE constraint' in str(e) or 'unique' in str(e).lower():
                    try:
                        transaction = SingPayTransaction.objects.get(transaction_id=transaction_id)
                        logger.info(f"Transaction récupérée après erreur unique: {transaction.transaction_id}")
                    except SingPayTransaction.DoesNotExist:
                        raise
                else:
                    raise
        
        logger.info(f"URL finale renvoyée au client: {payment_url}")
        logger.info(f"Transaction créée: {transaction.transaction_id} - Statut: {transaction.status}")
        
        # Vérifier si on est en mode bypass (en utilisant le service pour avoir la valeur réelle)
        bypass_mode = singpay_service.bypass_api
        
        # Si on n'est pas en mode bypass, s'assurer que l'URL est bien une URL SingPay réelle
        if not bypass_mode:
            if not payment_url or not (payment_url.startswith('http://') or payment_url.startswith('https://')):
                logger.error(f"URL de paiement invalide en mode production: {payment_url}")
                return JsonResponse({
                    'success': False,
                    'error': 'URL de paiement invalide. Veuillez vérifier la configuration SingPay.'
                }, status=500)
            # Vérifier que l'URL n'est pas une URL de test locale
            if '/test-payment/' in payment_url or 'localhost' in payment_url or '127.0.0.1' in payment_url:
                logger.error(f"URL de test détectée en mode production: {payment_url}")
                return JsonResponse({
                    'success': False,
                    'error': 'Configuration incorrecte : le mode test est activé alors que l\'API réelle devrait être utilisée. Veuillez vérifier SINGPAY_BYPASS_API dans settings.py.'
                }, status=500)
        
        return JsonResponse({
            'success': True,
            'payment_url': payment_url,
            'transaction_id': transaction.transaction_id,
            'bypass_mode': bypass_mode,  # Informer le frontend du mode
        })
        
    except Exception as e:
        logger.exception(f"Erreur dans init_singpay_payment: {str(e)}")
        error_msg = str(e)
        
        # Vérifier si c'est une erreur d'endpoint
        if '404' in error_msg or 'Not Found' in error_msg:
            error_msg = (
                "L'endpoint API SingPay n'a pas été trouvé. "
                "Veuillez vérifier la documentation SingPay à https://client.singpay.ga/doc/reference/index.html "
                "pour confirmer le bon endpoint. "
                "Contactez le support SingPay si le problème persiste."
            )
        elif '401' in error_msg or '403' in error_msg or 'Unauthorized' in error_msg:
            error_msg = (
                "Erreur d'authentification avec l'API SingPay. "
                "Vérifiez que vos credentials (API_KEY, API_SECRET, MERCHANT_ID) sont corrects dans settings.py"
            )
        
        return JsonResponse({
            'success': False,
            'error': error_msg,
            'details': str(e) if settings.DEBUG else None
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def singpay_callback(request):
    """
    Callback webhook de SingPay
    """
    try:
        # Récupérer les headers
        signature = request.headers.get('X-Signature', '')
        timestamp = request.headers.get('X-Timestamp', '')
        
        # Lire le payload
        payload = request.body.decode('utf-8')
        payload_data = json.loads(payload)
        
        # Récupérer la transaction
        transaction_id = payload_data.get('transaction_id')
        if not transaction_id:
            logger.error("Transaction ID manquant dans le callback SingPay")
            return HttpResponse(status=400)
        
        try:
            transaction = SingPayTransaction.objects.get(transaction_id=transaction_id)
        except SingPayTransaction.DoesNotExist:
            logger.error(f"Transaction {transaction_id} non trouvée")
            return HttpResponse(status=404)
        
        # Vérifier la signature (peut être vide en mode développement ou si SingPay ne l'envoie pas)
        is_valid = True  # Par défaut, accepter le webhook
        if signature and timestamp:
            is_valid = singpay_service.verify_webhook_signature(payload, signature, timestamp)
        elif settings.DEBUG:
            # En mode développement, accepter les webhooks sans signature
            logger.info(f"Mode DEBUG: Webhook accepté sans vérification de signature pour {transaction_id}")
        else:
            # En production, logger un avertissement mais continuer
            logger.warning(f"Webhook reçu sans signature pour {transaction_id} - traitement continué")
        
        # Logger le webhook
        webhook_log = SingPayWebhookLog.objects.create(
            transaction=transaction,
            payload=payload_data,
            signature=signature or '',
            timestamp=timestamp or '',
            is_valid=is_valid
        )
        
        if not is_valid and not settings.DEBUG:
            # En production, rejeter les webhooks avec signature invalide
            logger.warning(f"Signature invalide pour la transaction {transaction_id}")
            webhook_log.error_message = "Signature invalide"
            webhook_log.save()
            return HttpResponse(status=401)
        
        # Traiter le statut
        status = payload_data.get('status', '').lower()
        logger.info(f"Callback SingPay reçu pour transaction {transaction_id} avec statut: {status}")
        
        if status == 'success':
            logger.info(f"Mise à jour de la transaction {transaction_id} en SUCCESS")
            transaction.status = SingPayTransaction.SUCCESS
            transaction.paid_at = timezone.now()
            transaction.payment_method = payload_data.get('payment_method', '')
            transaction.save()
            
            # Mettre à jour la commande standard
            if transaction.order:
                logger.info(f"Mise à jour de la commande {transaction.order.id} suite au paiement")
                transaction.order.is_finished = True
                transaction.order.status = Order.Underway
                transaction.order.save()
            
            # Mettre à jour la commande C2C si applicable
            if hasattr(transaction, 'c2c_orders') and transaction.c2c_orders.exists():
                from c2c.services import SingPayService as C2CSingPayService
                c2c_order = transaction.c2c_orders.first()
                C2CSingPayService.handle_payment_success(transaction)
                logger.info(f"Paiement C2C réussi pour la commande #{c2c_order.id}")
            
            # Gérer le paiement du boost produit C2C
            if transaction.transaction_type == SingPayTransaction.BOOST_PAYMENT:
                from c2c.services import SingPayService as C2CSingPayService
                try:
                    boost = C2CSingPayService.handle_boost_payment_success(transaction)
                    if boost:
                        logger.info(f"Boost activé avec succès pour le produit #{boost.product.id}")
                except Exception as e:
                    logger.error(f"Erreur lors de l'activation du boost: {str(e)}")
            
            webhook_log.processed = True
            webhook_log.save()
            logger.info(f"Callback traité avec succès pour transaction {transaction_id}")
            
        elif status == 'failed':
            logger.warning(f"Transaction {transaction_id} marquée comme FAILED")
            transaction.status = SingPayTransaction.FAILED
            transaction.save()
            webhook_log.error_message = payload_data.get('error_message', 'Paiement échoué')
            webhook_log.processed = True
            webhook_log.save()
            
        elif status == 'cancelled':
            logger.info(f"Transaction {transaction_id} marquée comme CANCELLED")
            transaction.status = SingPayTransaction.CANCELLED
            transaction.save()
            webhook_log.processed = True
            webhook_log.save()
        else:
            logger.warning(f"Statut inconnu reçu pour transaction {transaction_id}: {status}")
            webhook_log.error_message = f"Statut inconnu: {status}"
            webhook_log.processed = False
            webhook_log.save()
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.exception(f"Erreur dans singpay_callback: {str(e)}")
        return HttpResponse(status=500)


@require_http_methods(["GET"])
@login_required
def singpay_return(request):
    """
    Gère le retour après paiement SingPay
    SingPay redirige vers cette URL après le paiement
    """
    try:
        # Récupérer les paramètres de la requête
        transaction_id = request.GET.get('transaction_id')
        status = request.GET.get('status', '').lower()
        
        if not transaction_id:
            messages.error(request, 'Transaction ID manquant')
            return redirect('orders:cart')
        
        try:
            transaction = SingPayTransaction.objects.get(transaction_id=transaction_id)
        except SingPayTransaction.DoesNotExist:
            messages.error(request, 'Transaction non trouvée')
            return redirect('orders:cart')
        
        # Vérifier que la transaction appartient à l'utilisateur
        if transaction.user and transaction.user != request.user:
            messages.error(request, 'Vous n\'avez pas accès à cette transaction')
            return redirect('orders:cart')
        
        # Toujours vérifier le statut avec l'API SingPay si la transaction est en PENDING
        # ou si le statut dans l'URL n'est pas clair
        should_verify = (
            transaction.status == SingPayTransaction.PENDING or
            not status or
            status not in ['success', 'failed', 'cancelled']
        )
        
        if should_verify:
            logger.info(f"Vérification du statut de la transaction {transaction_id} avec l'API SingPay")
            success, response = singpay_service.verify_payment(transaction_id)
            if success:
                api_status = response.get('status', '').lower()
                logger.info(f"Statut API pour {transaction_id}: {api_status}")
                
                if api_status == 'success':
                    # Mettre à jour la transaction
                    transaction.status = SingPayTransaction.SUCCESS
                    transaction.paid_at = timezone.now()
                    if response.get('payment_method'):
                        transaction.payment_method = response.get('payment_method')
                    transaction.save()
                    
                    # Mettre à jour la commande si elle n'est pas déjà finalisée
                    if transaction.order and not transaction.order.is_finished:
                        transaction.order.is_finished = True
                        transaction.order.status = Order.Underway
                        transaction.order.save()
                        logger.info(f"Commande {transaction.order.id} mise à jour avec succès")
                    
                    # Stocker l'ID de commande dans la session pour la page de succès
                    if transaction.order:
                        request.session['order_id'] = transaction.order.id
                        request.session['cart_id'] = transaction.order.id
                    
                    messages.success(request, 'Paiement effectué avec succès !')
                    return redirect('orders:success')
                elif api_status in ['failed', 'cancelled']:
                    transaction.status = SingPayTransaction.FAILED if api_status == 'failed' else SingPayTransaction.CANCELLED
                    transaction.save()
                    messages.error(request, f'Le paiement a été {api_status}')
                    return redirect('orders:payment')
                else:
                    # Statut encore en attente
                    logger.info(f"Transaction {transaction_id} toujours en attente (statut: {api_status})")
                    messages.info(request, 'Votre paiement est en cours de traitement. Vous serez notifié une fois le paiement confirmé.')
                    return redirect('orders:payment')
            else:
                logger.warning(f"Impossible de vérifier le statut de la transaction {transaction_id} avec l'API")
                # Si on ne peut pas vérifier, utiliser le statut de l'URL ou de la transaction
                if status == 'success' or transaction.status == SingPayTransaction.SUCCESS:
                    if transaction.order and not transaction.order.is_finished:
                        transaction.order.is_finished = True
                        transaction.order.status = Order.Underway
                        transaction.order.save()
                    
                    if transaction.status != SingPayTransaction.SUCCESS:
                        transaction.status = SingPayTransaction.SUCCESS
                        transaction.paid_at = timezone.now()
                        transaction.save()
                    
                    if transaction.order:
                        request.session['order_id'] = transaction.order.id
                        request.session['cart_id'] = transaction.order.id
                    
                    messages.success(request, 'Paiement effectué avec succès !')
                    return redirect('orders:success')
                else:
                    messages.warning(request, 'Impossible de vérifier le statut du paiement. Veuillez réessayer plus tard.')
                    return redirect('orders:payment')
        elif status == 'success' or transaction.status == SingPayTransaction.SUCCESS:
            # Mettre à jour la commande si elle n'est pas déjà finalisée
            if transaction.order and not transaction.order.is_finished:
                transaction.order.is_finished = True
                transaction.order.status = Order.Underway
                transaction.order.save()
            
            # Mettre à jour la transaction si nécessaire
            if transaction.status != SingPayTransaction.SUCCESS:
                transaction.status = SingPayTransaction.SUCCESS
                transaction.paid_at = timezone.now()
                transaction.save()
            
            # Stocker l'ID de commande dans la session pour la page de succès
            if transaction.order:
                request.session['order_id'] = transaction.order.id
                request.session['cart_id'] = transaction.order.id
            
            messages.success(request, 'Paiement effectué avec succès !')
            return redirect('orders:success')
        
        elif status == 'failed' or status == 'cancelled':
            transaction.status = SingPayTransaction.FAILED if status == 'failed' else SingPayTransaction.CANCELLED
            transaction.save()
            messages.error(request, f'Le paiement a été {status}')
            return redirect('orders:payment')
        
    except Exception as e:
        logger.exception(f"Erreur dans singpay_return: {str(e)}")
        messages.error(request, 'Une erreur est survenue lors du traitement du retour')
        return redirect('orders:cart')


@require_http_methods(["GET"])
def verify_singpay_payment(request, transaction_id):
    """
    Vérifie le statut d'une transaction SingPay
    """
    try:
        transaction = get_object_or_404(SingPayTransaction, transaction_id=transaction_id)
        
        # Vérifier avec l'API SingPay (ou bypass en mode test)
        success, response = singpay_service.verify_payment(transaction_id)
        
        if success:
            status = response.get('status', '').lower()
            
            if status == 'success' and transaction.status != SingPayTransaction.SUCCESS:
                transaction.status = SingPayTransaction.SUCCESS
                transaction.paid_at = timezone.now()
                transaction.payment_method = response.get('payment_method', 'AirtelMoney')
                
                if transaction.order:
                    transaction.order.is_finished = True
                    transaction.order.status = Order.Underway
                    transaction.order.save()
                
                transaction.save()
            
            return JsonResponse({
                'success': True,
                'status': transaction.status,
                'transaction_id': transaction.transaction_id,
            })
        else:
            return JsonResponse({
                'success': False,
                'error': response.get('error', 'Erreur de vérification')
            }, status=500)
            
    except Exception as e:
        logger.exception(f"Erreur dans verify_singpay_payment: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Une erreur est survenue'
        }, status=500)


@require_http_methods(["GET", "POST"])
def test_singpay_payment(request, transaction_id):
    """
    Page de test pour simuler le paiement SingPay (mode bypass uniquement)
    Si l'API réelle est activée, redirige vers l'URL SingPay réelle
    """
    try:
        transaction = get_object_or_404(SingPayTransaction, transaction_id=transaction_id)
        
        # Vérifier si on est en mode bypass (en utilisant le service pour avoir la valeur réelle)
        bypass_mode = singpay_service.bypass_api
        
        # Si on n'est pas en mode bypass et qu'on a une URL de paiement réelle, rediriger
        if not bypass_mode and transaction.payment_url:
            # Vérifier que l'URL est bien une URL SingPay réelle (pas locale)
            if transaction.payment_url.startswith('http://') or transaction.payment_url.startswith('https://'):
                # Rediriger vers l'URL SingPay réelle si elle ne pointe pas vers localhost
                if 'localhost' not in transaction.payment_url and '127.0.0.1' not in transaction.payment_url and '/test-payment/' not in transaction.payment_url:
                    logger.info(f"Redirection vers l'URL SingPay réelle: {transaction.payment_url}")
                    return redirect(transaction.payment_url)
                elif 'singpay' in transaction.payment_url.lower() or 'client.singpay.ga' in transaction.payment_url:
                    logger.info(f"Redirection vers l'URL SingPay réelle: {transaction.payment_url}")
                    return redirect(transaction.payment_url)
        
        # Si on est en mode bypass, afficher la page de test
        if request.method == 'POST':
            # Simuler un paiement réussi
            transaction.status = SingPayTransaction.SUCCESS
            transaction.paid_at = timezone.now()
            transaction.payment_method = request.POST.get('payment_method', 'AirtelMoney')
            
            if transaction.order:
                transaction.order.is_finished = True
                transaction.order.status = Order.Underway
                transaction.order.save()
                
                # Créer des notifications pour les vendeurs peer-to-peer
                from orders.models import OrderDetails
                from accounts.models import PeerToPeerOrderNotification
                
                order_details = OrderDetails.objects.filter(
                    order=transaction.order,
                    peer_product__isnull=False
                )
                
                for order_detail in order_details:
                    if order_detail.peer_product:
                        # Vérifier si la notification existe déjà
                        notification, created = PeerToPeerOrderNotification.objects.get_or_create(
                            order=transaction.order,
                            order_detail=order_detail,
                            peer_product=order_detail.peer_product,
                            defaults={
                                'seller': order_detail.peer_product.seller,
                                'buyer': transaction.order.user if transaction.order.user else None,
                                'status': PeerToPeerOrderNotification.PENDING,
                                'is_read': False,
                            }
                        )
            
            transaction.save()
            
            # Rediriger vers la page de commande
            messages.success(request, 'Paiement effectué avec succès !')
            return redirect('accounts:dashboard_customer')
        
        # Afficher la page de test uniquement en mode bypass
        if not bypass_mode:
            # Si on arrive ici sans URL de paiement, c'est une erreur
            messages.error(request, 'URL de paiement non disponible. Veuillez réessayer.')
            logger.error(f"Transaction {transaction_id} sans URL de paiement en mode production")
            return redirect('orders:payment')
        
        context = {
            'transaction': transaction,
            'order': transaction.order,
            'bypass_mode': bypass_mode,
        }
        return render(request, 'payments/test-payment.html', context)
        
    except Exception as e:
        logger.exception(f"Erreur dans test_singpay_payment: {str(e)}")
        messages.error(request, 'Une erreur est survenue')
        return redirect('orders:cart')


@require_http_methods(["GET"])
def get_transaction_details(request, transaction_id):
    """
    Retourne les détails d'une transaction en JSON (pour la boîte de dialogue)
    """
    try:
        transaction = get_object_or_404(SingPayTransaction, transaction_id=transaction_id)
        
        steps = transaction.get_status_steps()
        
        return JsonResponse({
            'success': True,
            'transaction': {
                'id': transaction.id,
                'transaction_id': transaction.transaction_id,
                'amount': str(transaction.amount),
                'currency': transaction.currency,
                'status': transaction.status,
                'status_display': transaction.get_status_display(),
                'payment_method': transaction.payment_method or 'Non spécifié',
                'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
                'paid_at': transaction.paid_at.isoformat() if transaction.paid_at else None,
            },
            'order': {
                'id': transaction.order.id if transaction.order else None,
                'status': transaction.order.status if transaction.order else None,
                'is_finished': transaction.order.is_finished if transaction.order else False,
            } if transaction.order else None,
            'steps': [
                {
                    'name': step['name'],
                    'status': step['status'],
                    'date': step['date'].isoformat() if step['date'] else None,
                    'icon': step.get('icon', 'fi-rs-circle'),
                    'description': step['description'],
                }
                for step in steps
            ],
        })
        
    except Exception as e:
        logger.exception(f"Erreur dans get_transaction_details: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Une erreur est survenue'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def list_singpay_transactions(request):
    """
    Liste toutes les transactions SingPay de l'utilisateur connecté
    """
    try:
        transactions = SingPayTransaction.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        context = {
            'transactions': transactions,
            'total_transactions': transactions.count(),
            'pending_transactions': transactions.filter(status=SingPayTransaction.PENDING).count(),
            'successful_transactions': transactions.filter(status=SingPayTransaction.SUCCESS).count(),
            'failed_transactions': transactions.filter(status=SingPayTransaction.FAILED).count(),
        }
        
        return render(request, 'payments/transactions-list.html', context)
        
    except Exception as e:
        logger.exception(f"Erreur dans list_singpay_transactions: {str(e)}")
        messages.error(request, 'Une erreur est survenue')
        return redirect('accounts:dashboard_customer')
