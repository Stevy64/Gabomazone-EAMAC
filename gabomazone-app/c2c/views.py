"""
Vues pour le module C2C
Toutes les interactions utilisateur pour le workflow C2C
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)

from .models import (
    PurchaseIntent, Negotiation, C2COrder, DeliveryVerification,
    ProductBoost, PlatformSettings
)
from .services import (
    PurchaseIntentService, CommissionCalculator, SingPayService,
    DeliveryVerificationService, BoostService
)
from accounts.models import PeerToPeerProduct


@login_required
def get_purchase_intent_for_conversation(request):
    """
    Récupère l'intention d'achat pour une conversation donnée avec l'historique des négociations
    """
    product_id = request.GET.get('product_id')
    buyer_id = request.GET.get('buyer_id')
    seller_id = request.GET.get('seller_id')
    intent_id = request.GET.get('intent_id')
    
    try:
        if intent_id:
            intent = PurchaseIntent.objects.filter(id=intent_id).first()
        elif all([product_id, buyer_id, seller_id]):
            intent = PurchaseIntent.objects.filter(
                product_id=product_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                status__in=[PurchaseIntent.PENDING, PurchaseIntent.NEGOTIATING, PurchaseIntent.AGREED]
            ).first()
        else:
            return JsonResponse({'success': False, 'error': 'Paramètres manquants'}, status=400)
        
        if intent:
            # Récupérer l'historique des négociations
            negotiations_qs = intent.negotiations.all().order_by('created_at')
            negotiations_data = []
            for neg in negotiations_qs:
                negotiations_data.append({
                    'id': neg.id,
                    'proposer_id': neg.proposer.id,
                    'proposer_name': neg.proposer.get_full_name() or neg.proposer.username,
                    'proposed_price': str(neg.proposed_price),
                    'message': neg.message or '',
                    'status': neg.status,
                    'created_at': neg.created_at.strftime('%d/%m/%Y à %H:%M'),
                })
            
            # Un prix n'est éligible au paiement que si une proposition a été acceptée
            accepted_neg = negotiations_qs.filter(status=Negotiation.ACCEPTED).order_by('-created_at').first()
            can_accept_final_price = accepted_neg is not None
            
            # Récupérer les infos de commande C2C si déjà créée
            order_id = None
            order_status = None
            order_data = None
            verification_data = None
            
            try:
                existing_order = intent.c2c_order
                order_id = existing_order.id
                order_status = existing_order.status
                order_data = {
                    'id': existing_order.id,
                    'status': existing_order.status,
                    'final_price': str(existing_order.final_price),
                    'buyer_commission': str(existing_order.buyer_commission),
                    'seller_commission': str(existing_order.seller_commission),
                    'buyer_total': str(existing_order.buyer_total),
                    'seller_net': str(existing_order.seller_net),
                    'paid_at': existing_order.paid_at.strftime('%d/%m/%Y à %H:%M') if existing_order.paid_at else None,
                    'completed_at': existing_order.completed_at.strftime('%d/%m/%Y à %H:%M') if existing_order.completed_at else None,
                }
                
                # Récupérer les infos de vérification si la commande est payée
                if existing_order.status in [C2COrder.PAID, C2COrder.PENDING_DELIVERY, C2COrder.DELIVERED, C2COrder.VERIFIED, C2COrder.COMPLETED]:
                    try:
                        verification = existing_order.delivery_verification
                        # Chaque utilisateur voit SON PROPRE code à donner et peut saisir celui de l'autre
                        verification_data = {
                            'status': verification.status,
                            # L'acheteur voit son buyer_code (A-CODE) à donner au vendeur
                            # Le vendeur voit son seller_code (V-CODE) à donner à l'acheteur
                            'seller_code': verification.seller_code,  # V-CODE du vendeur
                            'buyer_code': verification.buyer_code,    # A-CODE de l'acheteur
                            'seller_code_verified': verification.seller_code_verified,
                            'buyer_code_verified': verification.buyer_code_verified,
                            'is_completed': verification.is_completed(),
                        }
                    except Exception:
                        pass
            except Exception:
                pass
            
            return JsonResponse({
                'success': True,
                'purchase_intent_id': intent.id,
                'initial_price': str(intent.initial_price),
                'negotiated_price': str(accepted_neg.proposed_price if accepted_neg else intent.negotiated_price) if (accepted_neg or intent.negotiated_price) else None,
                'final_price': str(intent.final_price) if intent.final_price else None,
                'status': intent.status,
                'buyer_id': intent.buyer.id,
                'seller_id': intent.seller.id,
                'negotiations': negotiations_data,
                'can_accept_final_price': can_accept_final_price,
                'order_id': order_id,
                'order_status': order_status,
                'order': order_data,
                'verification': verification_data,
            })
        else:
            return JsonResponse({'success': False, 'purchase_intent_id': None})
    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def create_purchase_intent(request, product_id):
    """
    Crée une intention d'achat pour un produit C2C
    Remplace le paiement direct par un système de négociation obligatoire
    """
    product = get_object_or_404(PeerToPeerProduct, id=product_id, status=PeerToPeerProduct.APPROVED)
    
    # Vérifier que l'utilisateur n'est pas le vendeur
    if product.seller == request.user:
        messages.error(request, "Vous ne pouvez pas acheter votre propre article.")
        return redirect('accounts:peer-product-details', slug=product.PRDSlug)
    
    if request.method == 'POST':
        try:
            # Créer l'intention d'achat
            intent = PurchaseIntentService.create_purchase_intent(
                product=product,
                buyer=request.user,
                initial_price=product.PRDPrice
            )
            
            messages.success(request, "Intention d'achat créée. Une conversation a été ouverte avec le vendeur.")
            
            # Rediriger vers la messagerie avec la conversation ouverte
            from django.urls import reverse
            messages_url = reverse('accounts:my-messages') + f'?product_id={product.id}&action=propose_offer'
            return redirect(messages_url)
        except Exception as e:
            # Si l'erreur est une contrainte UNIQUE, récupérer l'intention existante
            if 'UNIQUE constraint' in str(e) or 'unique constraint' in str(e).lower():
                try:
                    existing_intent = PurchaseIntent.objects.filter(
                        product=product,
                        buyer=request.user
                    ).first()
                    if existing_intent:
                        messages.info(request, "Une intention d'achat existe déjà pour cet article. Redirection vers la messagerie...")
                        from django.urls import reverse
                        messages_url = reverse('accounts:my-messages') + f'?product_id={product.id}&action=propose_offer'
                        return redirect(messages_url)
                except Exception:
                    pass
            messages.error(request, f"Erreur lors de la création de l'intention d'achat: {str(e)}")
            return redirect('accounts:peer-product-details', slug=product.PRDSlug)
    
    # GET: Afficher le formulaire de confirmation
    context = {
        'product': product,
        'initial_price': product.PRDPrice,
    }
    return render(request, 'c2c/create_purchase_intent.html', context)


@login_required
@require_POST
def create_negotiation(request, intent_id):
    """
    Crée une proposition de négociation
    """
    intent = get_object_or_404(PurchaseIntent, id=intent_id)
    
    # Vérifier les permissions
    if request.user not in [intent.buyer, intent.seller]:
        messages.error(request, "Vous n'avez pas la permission d'effectuer cette action.")
        return redirect('accounts:my-messages')
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        proposed_price = Decimal(str(data.get('proposed_price', 0)))
        message = data.get('message', '')
        
        if proposed_price <= 0:
            return JsonResponse({'error': 'Le prix proposé doit être supérieur à 0'}, status=400)
        
        # Créer la négociation
        negotiation = PurchaseIntentService.create_negotiation(
            intent=intent,
            proposer=request.user,
            proposed_price=proposed_price,
            message=message
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'negotiation_id': negotiation.id,
                'proposed_price': str(negotiation.proposed_price),
                'message': 'Proposition créée avec succès'
            })
        
        messages.success(request, "Proposition de prix envoyée.")
        return redirect('accounts:my-messages')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=400)
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('accounts:my-messages')


@login_required
@require_POST
def accept_negotiation(request, negotiation_id):
    """
    Accepte une proposition de négociation (destinataire uniquement)
    """
    negotiation = get_object_or_404(Negotiation, id=negotiation_id)
    intent = negotiation.purchase_intent
    
    if request.user not in [intent.buyer, intent.seller]:
        return JsonResponse({'error': "Vous n'avez pas la permission d'accepter cette offre."}, status=403)
    if request.user == negotiation.proposer:
        return JsonResponse({'error': "Vous ne pouvez pas accepter votre propre offre."}, status=400)
    
    try:
        PurchaseIntentService.accept_negotiation(negotiation, request.user)
        return JsonResponse({'success': True})
    except PermissionError as e:
        return JsonResponse({'error': str(e)}, status=403)
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
@require_POST
def reject_negotiation(request, negotiation_id):
    """
    Refuse une proposition de négociation
    """
    negotiation = get_object_or_404(Negotiation, id=negotiation_id)
    intent = negotiation.purchase_intent
    
    if request.user not in [intent.buyer, intent.seller]:
        return JsonResponse({'error': "Vous n'avez pas la permission de refuser cette offre."}, status=403)
    
    try:
        PurchaseIntentService.reject_negotiation(negotiation, request.user)
        return JsonResponse({'success': True})
    except PermissionError as e:
        return JsonResponse({'error': str(e)}, status=403)
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
@require_POST
def accept_purchase_intent(request, intent_id):
    """
    Accepte une intention d'achat (le vendeur accepte de négocier)
    """
    intent = get_object_or_404(PurchaseIntent, id=intent_id)
    
    # Vérifier que c'est le vendeur
    if request.user != intent.seller:
        return JsonResponse({'error': 'Seul le vendeur peut accepter cette intention d\'achat.'}, status=403)
    
    # Vérifier le statut - permettre l'acceptation même si déjà en négociation
    if intent.status not in [PurchaseIntent.PENDING, PurchaseIntent.NEGOTIATING]:
        return JsonResponse({
            'error': f'Cette intention d\'achat ne peut plus être acceptée. Statut actuel: {intent.get_status_display()}',
            'current_status': intent.status
        }, status=400)
    
    try:
        intent.status = PurchaseIntent.NEGOTIATING
        intent.seller_notified = True  # Marquer comme notifié
        intent.save()
        
        # Créer un message automatique
        from accounts.models import ProductConversation, ProductMessage
        from django.db import connection as db_connection
        
        # Vérifier si la table existe
        table_exists = False
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_productconversation'")
                table_exists = cursor.fetchone() is not None
        except Exception:
            table_exists = False
        
        if table_exists:
            try:
                conversation, _ = ProductConversation.objects.get_or_create(
                    product=intent.product,
                    buyer=intent.buyer,
                    seller=intent.seller,
                    defaults={'last_message_at': timezone.now()}
                )
                
                seller_name = intent.seller.get_full_name() or intent.seller.username
                message_text = f"✅ {seller_name} a accepté votre intention d'achat. Vous pouvez maintenant négocier le prix !"
                
                ProductMessage.objects.create(
                    conversation=conversation,
                    sender=intent.seller,
                    message=message_text
                )
                
                conversation.last_message_at = timezone.now()
                conversation.save()
            except Exception as msg_error:
                # Logger l'erreur mais continuer
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating message in accept_purchase_intent: {msg_error}")
        
        return JsonResponse({
            'success': True,
            'message': 'Intention d\'achat acceptée. Vous pouvez maintenant négocier le prix.',
            'product_id': intent.product.id,
            'conversation_id': conversation.id if table_exists and 'conversation' in locals() else None
        })
    except Exception as e:
        import traceback
        import logging
        error_trace = traceback.format_exc()
        logger = logging.getLogger(__name__)
        logger.error(f"Error in accept_purchase_intent: {e}\n{error_trace}")
        return JsonResponse({'error': str(e), 'trace': error_trace}, status=500)


@login_required
@require_POST
def reject_purchase_intent(request, intent_id):
    """
    Refuse une intention d'achat
    """
    intent = get_object_or_404(PurchaseIntent, id=intent_id)
    
    # Vérifier que c'est le vendeur
    if request.user != intent.seller:
        return JsonResponse({'error': 'Seul le vendeur peut refuser cette intention d\'achat.'}, status=403)
    
    # Vérifier le statut
    if intent.status not in [PurchaseIntent.PENDING, PurchaseIntent.NEGOTIATING]:
        return JsonResponse({
            'error': f'Cette intention d\'achat ne peut plus être refusée. Statut actuel: {intent.get_status_display()}',
            'current_status': intent.status
        }, status=400)
    
    try:
        intent.status = PurchaseIntent.REJECTED
        intent.seller_notified = True  # Marquer comme notifié
        intent.save()
        
        # Créer un message automatique
        from accounts.models import ProductConversation, ProductMessage
        from django.db import connection as db_connection
        
        # Vérifier si la table existe
        table_exists = False
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_productconversation'")
                table_exists = cursor.fetchone() is not None
        except Exception:
            table_exists = False
        
        if table_exists:
            try:
                conversation, _ = ProductConversation.objects.get_or_create(
                    product=intent.product,
                    buyer=intent.buyer,
                    seller=intent.seller,
                    defaults={'last_message_at': timezone.now()}
                )
                
                seller_name = intent.seller.get_full_name() or intent.seller.username
                message_text = f"❌ {seller_name} a refusé votre intention d'achat pour cet article."
                
                ProductMessage.objects.create(
                    conversation=conversation,
                    sender=intent.seller,
                    message=message_text
                )
                
                conversation.last_message_at = timezone.now()
                conversation.save()
            except Exception as msg_error:
                # Logger l'erreur mais continuer
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating message in reject_purchase_intent: {msg_error}")
        
        return JsonResponse({
            'success': True,
            'message': 'Intention d\'achat refusée.'
        })
    except Exception as e:
        import traceback
        import logging
        error_trace = traceback.format_exc()
        logger = logging.getLogger(__name__)
        logger.error(f"Error in reject_purchase_intent: {e}\n{error_trace}")
        return JsonResponse({'error': str(e), 'trace': error_trace}, status=500)


@login_required
@require_POST
def cancel_purchase_intent(request, intent_id):
    """
    Annule une intention d'achat (par l'acheteur ou le vendeur)
    """
    intent = get_object_or_404(PurchaseIntent, id=intent_id)
    
    # Vérifier que c'est l'acheteur ou le vendeur
    if request.user not in [intent.buyer, intent.seller]:
        return JsonResponse({'error': 'Vous n\'avez pas la permission d\'annuler cette intention d\'achat.'}, status=403)
    
    # Vérifier le statut - ne peut être annulé que si en attente ou en négociation
    if intent.status not in [PurchaseIntent.PENDING, PurchaseIntent.NEGOTIATING]:
        return JsonResponse({'error': 'Cette intention d\'achat ne peut plus être annulée.'}, status=400)
    
    try:
        intent.status = PurchaseIntent.CANCELLED
        intent.seller_notified = True  # Marquer comme notifié pour ne plus compter
        intent.save()
        
        # Créer un message automatique dans la conversation si elle existe
        from accounts.models import ProductConversation, ProductMessage
        from django.db import connection as db_connection
        
        # Vérifier si la table existe
        table_exists = False
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_productconversation'")
                table_exists = cursor.fetchone() is not None
        except Exception:
            table_exists = False
        
        if table_exists:
            try:
                conversation = ProductConversation.objects.get(
                    product=intent.product,
                    buyer=intent.buyer,
                    seller=intent.seller
                )
                
                canceller_name = request.user.get_full_name() or request.user.username
                message_text = f"❌ {canceller_name} a annulé l'intention d'achat pour cet article."
                
                ProductMessage.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    message=message_text
                )
                
                conversation.last_message_at = timezone.now()
                conversation.save()
            except ProductConversation.DoesNotExist:
                pass  # Pas de conversation, pas de problème
        
        return JsonResponse({
            'success': True,
            'message': 'Intention d\'achat annulée.'
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return JsonResponse({'error': str(e), 'trace': error_trace}, status=500)


@login_required
@require_POST
def cancel_purchase_intent(request, intent_id):
    """
    Annule une intention d'achat (par l'acheteur ou le vendeur)
    """
    intent = get_object_or_404(PurchaseIntent, id=intent_id)
    
    # Vérifier que c'est l'acheteur ou le vendeur
    if request.user not in [intent.buyer, intent.seller]:
        return JsonResponse({'error': 'Vous n\'avez pas la permission d\'annuler cette intention d\'achat.'}, status=403)
    
    # Vérifier le statut - ne peut être annulé que si en attente ou en négociation
    if intent.status not in [PurchaseIntent.PENDING, PurchaseIntent.NEGOTIATING]:
        return JsonResponse({'error': 'Cette intention d\'achat ne peut plus être annulée.'}, status=400)
    
    try:
        intent.status = PurchaseIntent.CANCELLED
        intent.seller_notified = True  # Marquer comme notifié pour ne plus compter
        intent.save()
        
        # Créer un message automatique dans la conversation si elle existe
        from accounts.models import ProductConversation, ProductMessage
        from django.db import connection as db_connection
        
        # Vérifier si la table existe
        table_exists = False
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_productconversation'")
                table_exists = cursor.fetchone() is not None
        except Exception:
            table_exists = False
        
        if table_exists:
            try:
                conversation = ProductConversation.objects.get(
                    product=intent.product,
                    buyer=intent.buyer,
                    seller=intent.seller
                )
                
                canceller_name = request.user.get_full_name() or request.user.username
                message_text = f"❌ {canceller_name} a annulé l'intention d'achat pour cet article."
                
                ProductMessage.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    message=message_text
                )
                
                conversation.last_message_at = timezone.now()
                conversation.save()
            except ProductConversation.DoesNotExist:
                pass  # Pas de conversation, pas de problème
        
        return JsonResponse({
            'success': True,
            'message': 'Intention d\'achat annulée.'
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return JsonResponse({'error': str(e), 'trace': error_trace}, status=500)


@login_required
@require_POST
def accept_final_price(request, intent_id):
    """
    Accepte un prix final et crée la commande C2C
    """
    intent = get_object_or_404(PurchaseIntent, id=intent_id)
    
    # Vérifier les permissions
    if request.user not in [intent.buyer, intent.seller]:
        messages.error(request, "Vous n'avez pas la permission d'effectuer cette action.")
        return redirect('accounts:my-messages')
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        final_price = Decimal(str(data.get('final_price', intent.final_price or intent.negotiated_price)))
        
        if not final_price or final_price <= 0:
            return JsonResponse({'error': 'Le prix final doit être supérieur à 0'}, status=400)
        
        # Créer la commande C2C
        c2c_order = PurchaseIntentService.accept_final_price(intent, final_price)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'order_id': c2c_order.id,
                'buyer_total': str(c2c_order.buyer_total),
                'message': 'Prix accepté ! Cliquez sur le bouton vert pour procéder au paiement.'
            })
        
        messages.success(request, "Prix accepté ! Cliquez sur le bouton vert pour procéder au paiement.")
        # Ne pas rediriger automatiquement - l'utilisateur doit cliquer sur le bouton
        return redirect('accounts:my-messages')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=400)
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('accounts:my-messages')


@login_required
def c2c_order_detail(request, order_id):
    """
    Affiche les détails d'une commande C2C
    """
    order = get_object_or_404(C2COrder, id=order_id)
    
    # Vérifier les permissions
    if request.user not in [order.buyer, order.seller]:
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette commande.")
        return redirect('c2c:buyer-orders' if request.user == order.buyer else 'c2c:seller-orders')
    
    # Récupérer la vérification si elle existe
    verification = None
    try:
        verification = order.delivery_verification
    except DeliveryVerification.DoesNotExist:
        pass
    
    context = {
        'order': order,
        'verification': verification,
        'is_buyer': request.user == order.buyer,
        'is_seller': request.user == order.seller,
    }
    return render(request, 'c2c/order_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def init_c2c_payment(request, order_id):
    """
    Affiche la page de paiement ou initialise le paiement SingPay pour une commande C2C
    """
    order = get_object_or_404(C2COrder, id=order_id)
    
    # Vérifier que c'est l'acheteur
    if request.user != order.buyer:
        messages.error(request, "Seul l'acheteur peut effectuer le paiement.")
        return redirect('c2c:order-detail', order_id=order_id)
    
    # Vérifier que le paiement n'a pas déjà été effectué
    if order.status != C2COrder.PENDING_PAYMENT:
        messages.info(request, "Cette commande a déjà été payée.")
        return redirect('c2c:order-detail', order_id=order_id)
    
    # Si GET, afficher la page de paiement
    if request.method == 'GET':
        # Récupérer les taux de commission pour l'affichage
        platform_settings = PlatformSettings.get_active_settings()
        context = {
            'order': order,
            'commission_rate_buyer': platform_settings.c2c_buyer_commission_rate,
            'commission_rate_seller': platform_settings.c2c_seller_commission_rate,
        }
        return render(request, 'c2c/payment.html', context)
    
    # Si POST, initialiser le paiement
    try:
        # Initialiser le paiement SingPay via l'API réelle
        singpay_transaction = SingPayService.init_c2c_payment(order, request)
        
        # Rediriger vers l'URL de paiement SingPay
        if singpay_transaction.payment_url:
            return redirect(singpay_transaction.payment_url)
        else:
            messages.error(request, "URL de paiement non disponible. Veuillez réessayer.")
            return redirect('c2c:order-detail', order_id=order_id)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Erreur lors de l'initialisation du paiement C2C: {str(e)}")
        messages.error(request, f"Erreur lors de l'initialisation du paiement: {str(e)}")
        return redirect('c2c:order-detail', order_id=order_id)




@login_required
def payment_success(request, order_id):
    """
    Page de succès de paiement C2C - Redirige vers la messagerie
    """
    order = get_object_or_404(C2COrder, id=order_id)
    
    # Vérifier que c'est l'acheteur ou le vendeur
    if request.user not in [order.buyer, order.seller]:
        messages.error(request, "Vous n'avez pas accès à cette commande.")
        return redirect('accounts:my-messages')
    
    # Si le paiement est en attente, vérifier et mettre à jour le statut
    if order.status == C2COrder.PENDING_PAYMENT:
        # Vérifier le statut de la transaction
        if order.payment_transaction and order.payment_transaction.status == 'success':
            order.status = C2COrder.PAID
            order.paid_at = timezone.now()
            order.save()
    
    # Récupérer les codes de vérification
    verification = None
    try:
        verification = order.delivery_verification
    except DeliveryVerification.DoesNotExist:
        # Créer la vérification si elle n'existe pas
        verification = DeliveryVerification.objects.create(c2c_order=order)
    
    # Préparer le message avec les codes
    if request.user == order.buyer:
        messages.success(
            request, 
            f"🎉 Paiement réussi ! Votre code de vérification (A-CODE) est : {verification.buyer_code}. "
            f"Communiquez ce code au vendeur lors de la remise de l'article."
        )
    else:
        messages.success(
            request, 
            f"🎉 Paiement reçu ! Votre code de vérification (V-CODE) est : {verification.seller_code}. "
            f"Communiquez ce code à l'acheteur après lui avoir remis l'article."
        )
    
    # Rediriger vers la messagerie avec le produit concerné
    from django.urls import reverse
    return redirect(f"{reverse('accounts:my-messages')}?product_id={order.product.id}")


@login_required
@require_POST
def verify_seller_code(request, order_id):
    """
    Vérifie le code vendeur (V-CODE)
    """
    order = get_object_or_404(C2COrder, id=order_id)
    
    # Vérifier que c'est le vendeur
    if request.user != order.seller:
        return JsonResponse({'error': 'Seul le vendeur peut vérifier ce code'}, status=403)
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        code = data.get('code', '').strip()
        
        if DeliveryVerificationService.verify_seller_code(order, code):
            # Vérifier si le vendeur peut noter l'acheteur
            can_review = False
            review_url = None
            try:
                from .models import BuyerReview
                # Vérifier si les deux codes sont validés
                verification = order.delivery_verification
                if verification.buyer_code_verified and verification.seller_code_verified:
                    can_review, _ = BuyerReview.can_review(order, order.seller)
                    if can_review:
                        review_url = reverse('c2c:create-review', args=[order.id])
            except:
                pass
            
            return JsonResponse({
                'success': True,
                'message': 'Code vendeur vérifié avec succès',
                'can_review': can_review,
                'review_url': review_url
            })
        else:
            return JsonResponse({
                'error': 'Code invalide ou déjà vérifié'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def verify_buyer_code(request, order_id):
    """
    Vérifie le code vendeur (V-CODE) saisi par l'acheteur
    L'acheteur entre le code V-CODE pour confirmer qu'il a reçu l'article
    """
    order = get_object_or_404(C2COrder, id=order_id)
    
    # Vérifier que c'est l'acheteur
    if request.user != order.buyer:
        return JsonResponse({'error': 'Seul l\'acheteur peut vérifier ce code'}, status=403)
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        code = data.get('code', '').strip()
        
        if DeliveryVerificationService.verify_buyer_code(order, code):
            # Vérifier si l'acheteur peut noter le vendeur
            can_review = False
            review_url = None
            try:
                from .models import SellerReview
                can_review, _ = SellerReview.can_review(order, order.buyer)
                if can_review:
                    review_url = reverse('c2c:create-review', args=[order.id])
            except:
                pass
            
            return JsonResponse({
                'success': True,
                'message': 'Code vendeur vérifié avec succès. La transaction est maintenant complète !',
                'can_review': can_review,
                'review_url': review_url
            })
        else:
            return JsonResponse({
                'error': 'Code invalide ou déjà vérifié'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def boost_product(request, product_id):
    """
    Affiche la page de boost d'un produit
    """
    product = get_object_or_404(PeerToPeerProduct, id=product_id)
    
    # Vérifier que c'est le vendeur
    if request.user != product.seller:
        messages.error(request, "Seul le vendeur peut booster son article.")
        return redirect('accounts:peer-product-details', slug=product.PRDSlug)
    
    context = {
        'product': product,
        'boost_prices': {
            '24h': BoostService.get_boost_price('24h'),
            '72h': BoostService.get_boost_price('72h'),
            '7d': BoostService.get_boost_price('7d'),
        }
    }
    return render(request, 'c2c/boost_product.html', context)


@login_required
@require_POST
def purchase_boost(request, product_id):
    """
    Achete un boost pour un produit - Initialise le paiement SingPay
    """
    product = get_object_or_404(PeerToPeerProduct, id=product_id)
    
    # Vérifier que c'est le vendeur
    if request.user != product.seller:
        return JsonResponse({'error': 'Seul le vendeur peut booster son article'}, status=403)
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        duration = data.get('duration', '24h')
        
        if duration not in ['24h', '72h', '7d']:
            return JsonResponse({'error': 'Durée de boost invalide'}, status=400)
        
        # Initialiser le paiement SingPay
        singpay_transaction = SingPayService.init_boost_payment(
            product=product,
            user=request.user,
            duration=duration,
            request=request
        )
        
        # Récupérer l'URL de paiement
        payment_url = singpay_transaction.payment_url
        
        if not payment_url:
            return JsonResponse({
                'success': False,
                'error': 'URL de paiement non disponible'
            }, status=400)
        
        # Rediriger vers la page de paiement SingPay
        return JsonResponse({
            'success': True,
            'payment_url': payment_url,
            'transaction_id': singpay_transaction.transaction_id,
            'message': 'Redirection vers le paiement...'
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Erreur lors de l'achat du boost: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def boost_success(request, product_id):
    """
    Page de succès après paiement du boost
    """
    product = get_object_or_404(PeerToPeerProduct, id=product_id)
    
    # Vérifier que c'est le vendeur
    if request.user != product.seller:
        messages.error(request, "Accès non autorisé.")
        return redirect('accounts:my-published-products')
    
    # Récupérer le dernier boost actif pour ce produit
    try:
        boost = ProductBoost.objects.filter(
            product=product,
            buyer=request.user,
            status=ProductBoost.ACTIVE
        ).order_by('-created_at').first()
        
        if boost:
            duration_display = dict(ProductBoost.DURATION_CHOICES).get(boost.duration, boost.duration)
            messages.success(
                request,
                f"🎉 Boost activé avec succès ! Votre article sera mis en avant pendant {duration_display}."
            )
        else:
            messages.info(request, "Le boost est en cours de traitement.")
    except Exception:
        pass
    
    return redirect('accounts:my-published-products')


@login_required
def simulate_boost_payment(request, product_id):
    """
    Simule le paiement d'un boost (uniquement en mode DEBUG)
    """
    if not settings.DEBUG:
        return JsonResponse({'error': 'Non disponible en production'}, status=403)
    
    product = get_object_or_404(PeerToPeerProduct, id=product_id)
    
    if request.user != product.seller:
        return JsonResponse({'error': 'Seul le vendeur peut booster son article'}, status=403)
    
    duration = request.GET.get('duration', '24h')
    
    if duration not in ['24h', '72h', '7d']:
        return JsonResponse({'error': 'Durée invalide'}, status=400)
    
    try:
        # Créer directement le boost (simulation)
        boost = BoostService.create_boost(
            product=product,
            buyer=request.user,
            duration=duration,
            payment_transaction=None
        )
        
        messages.success(
            request,
            f"🎉 Boost {duration} activé avec succès ! (Mode simulation)"
        )
        return redirect('accounts:my-published-products')
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('accounts:my-published-products')


@login_required
def seller_dashboard(request):
    """
    Dashboard du vendeur C2C
    """
    # Statistiques
    total_orders = C2COrder.objects.filter(seller=request.user).count()
    pending_orders = C2COrder.objects.filter(seller=request.user, status=C2COrder.PENDING_DELIVERY).count()
    completed_orders = C2COrder.objects.filter(seller=request.user, status=C2COrder.COMPLETED).count()
    total_revenue = sum(order.seller_net for order in C2COrder.objects.filter(
        seller=request.user, status=C2COrder.COMPLETED
    ))
    
    # Intentions d'achat en attente
    pending_intents = PurchaseIntent.objects.filter(
        seller=request.user,
        status__in=[PurchaseIntent.PENDING, PurchaseIntent.NEGOTIATING]
    )[:5]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'pending_intents': pending_intents,
    }
    return render(request, 'c2c/seller_dashboard.html', context)


@login_required
def seller_orders(request):
    """
    Liste des commandes du vendeur
    """
    orders = C2COrder.objects.filter(seller=request.user).order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'c2c/seller_orders.html', context)


@login_required
def seller_intents(request):
    """
    Liste des intentions d'achat pour le vendeur
    """
    intents = PurchaseIntent.objects.filter(seller=request.user).order_by('-created_at')
    context = {'intents': intents}
    return render(request, 'c2c/seller_intents.html', context)


@login_required
def buyer_orders(request):
    """
    Liste des commandes de l'acheteur
    """
    orders = C2COrder.objects.filter(buyer=request.user).order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'c2c/buyer_orders.html', context)


@login_required
def buyer_intents(request):
    """
    Liste des intentions d'achat de l'acheteur
    """
    intents = PurchaseIntent.objects.filter(buyer=request.user).order_by('-created_at')
    context = {'intents': intents}
    return render(request, 'c2c/buyer_intents.html', context)

