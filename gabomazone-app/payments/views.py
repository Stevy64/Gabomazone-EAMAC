"""
Vues pour les paiements SingPay
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
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
        
        # Construire les URLs
        base_url = f"{request.scheme}://{request.get_host()}"
        callback_url = f"{base_url}/payments/singpay/callback/"
        return_url = f"{base_url}/orders/order/success/"
        
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
            customer_phone=payment_info.phone,
            customer_name=f"{payment_info.first_name} {payment_info.last_name}",
            description=f"Paiement commande #{order.id}",
            callback_url=callback_url,
            return_url=return_url,
            metadata=metadata
        )
        
        if not success:
            logger.error(f"Erreur SingPay init_payment: {response}")
            return JsonResponse({
                'success': False,
                'error': response.get('error', 'Erreur lors de l\'initialisation du paiement')
            }, status=500)
        
        # Créer la transaction dans la base de données
        from datetime import timedelta
        expires_at = None
        if response.get('expires_at'):
            try:
                from datetime import datetime
                expires_at_str = response.get('expires_at')
                # Parser la date ISO avec timezone
                if 'T' in expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    # Convertir en timezone aware si nécessaire
                    if timezone.is_naive(expires_at):
                        expires_at = timezone.make_aware(expires_at)
                else:
                    expires_at = timezone.now() + timedelta(hours=24)
            except Exception as e:
                logger.warning(f"Erreur parsing expires_at: {e}")
                expires_at = timezone.now() + timedelta(hours=24)
        else:
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
        
        transaction = SingPayTransaction.objects.create(
            transaction_id=response.get('transaction_id'),
            reference=response.get('reference'),
            internal_order_id=f"ORDER-{order.id}",
            amount=amount,
            currency=currency,
            status=SingPayTransaction.PENDING,
            transaction_type=SingPayTransaction.ORDER_PAYMENT,
            customer_email=payment_info.Email_Address,
            customer_phone=payment_info.phone,
            customer_name=f"{payment_info.first_name} {payment_info.last_name}",
            payment_url=response.get('payment_url'),
            callback_url=callback_url,
            return_url=return_url,
            user=order.user if order.user else (request.user if request.user.is_authenticated else None),
            order=order,
            description=f"Paiement commande #{order.id}",
            metadata=metadata,
            expires_at=expires_at
        )
        
        return JsonResponse({
            'success': True,
            'payment_url': response.get('payment_url'),
            'transaction_id': transaction.transaction_id,
        })
        
    except Exception as e:
        logger.exception(f"Erreur dans init_singpay_payment: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Une erreur est survenue'
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
        
        # Vérifier la signature
        is_valid = singpay_service.verify_webhook_signature(payload, signature, timestamp)
        
        # Logger le webhook
        webhook_log = SingPayWebhookLog.objects.create(
            transaction=transaction,
            payload=payload_data,
            signature=signature,
            timestamp=timestamp,
            is_valid=is_valid
        )
        
        if not is_valid:
            logger.warning(f"Signature invalide pour la transaction {transaction_id}")
            webhook_log.error_message = "Signature invalide"
            webhook_log.save()
            return HttpResponse(status=401)
        
        # Traiter le statut
        status = payload_data.get('status', '').lower()
        
        if status == 'success':
            transaction.status = SingPayTransaction.SUCCESS
            transaction.paid_at = timezone.now()
            transaction.payment_method = payload_data.get('payment_method', '')
            
            # Mettre à jour la commande
            if transaction.order:
                transaction.order.is_finished = True
                transaction.order.status = Order.Underway
                transaction.order.save()
            
            webhook_log.processed = True
            webhook_log.save()
            
        elif status == 'failed':
            transaction.status = SingPayTransaction.FAILED
            webhook_log.error_message = payload_data.get('error_message', 'Paiement échoué')
            webhook_log.processed = True
            webhook_log.save()
            
        elif status == 'cancelled':
            transaction.status = SingPayTransaction.CANCELLED
            webhook_log.processed = True
            webhook_log.save()
        
        transaction.save()
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.exception(f"Erreur dans singpay_callback: {str(e)}")
        return HttpResponse(status=500)


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
    Page de test pour simuler le paiement SingPay (mode bypass)
    """
    try:
        transaction = get_object_or_404(SingPayTransaction, transaction_id=transaction_id)
        
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
        
        # Afficher la page de test
        context = {
            'transaction': transaction,
            'order': transaction.order,
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
