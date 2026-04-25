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
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from decimal import Decimal
import json
import logging
import traceback

logger = logging.getLogger(__name__)

from .models import (
    PurchaseIntent, Negotiation, C2COrder, DeliveryVerification,
    ProductBoost, PlatformSettings, DisputeCase, SafeZone,
    SellerReview, BuyerReview,
)
from .meeting_map_data import (
    build_popular_points_geo,
    get_popular_meeting_min_uses,
    get_safe_zones_models_and_geo,
)
from .services import (
    PurchaseIntentService, CommissionCalculator, SingPayService,
    DeliveryVerificationService, BoostService
)
from accounts.models import PeerToPeerProduct


def _purchase_intent_wants_json(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    accept = request.headers.get('Accept', '')
    return 'application/json' in accept


@login_required
def get_purchase_intent_for_conversation(request):
    """
    Récupère l'intention d'achat pour une conversation donnée avec l'historique des négociations
    """
    product_id = request.GET.get('product_id')
    buyer_id = request.GET.get('buyer_id')
    seller_id = request.GET.get('seller_id')
    intent_id = request.GET.get('intent_id')
    logger.info('[C2C·FLOW] get_purchase_intent user=%s intent_id=%s product=%s buyer=%s seller=%s',
                request.user.pk, intent_id, product_id, buyer_id, seller_id)
    
    try:
        if intent_id:
            intent = PurchaseIntent.objects.filter(id=intent_id).first()
        elif all([product_id, buyer_id, seller_id]):
            intent = PurchaseIntent.objects.filter(
                product_id=product_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                status__in=[
                    PurchaseIntent.PENDING,
                    PurchaseIntent.AWAITING_AVAILABILITY,
                    PurchaseIntent.NEGOTIATING,
                    PurchaseIntent.AGREED,
                ],
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
                    'expires_at_iso': neg.expires_at.isoformat() if neg.expires_at else None,
                })
            
            # Un prix n'est éligible au paiement que si une proposition a été acceptée
            accepted_neg = negotiations_qs.filter(status=Negotiation.ACCEPTED).order_by('-created_at').first()
            can_accept_final_price = accepted_neg is not None
            
            # Récupérer les infos de commande C2C si déjà créée
            order_id = None
            order_status = None
            order_data = None
            verification_data = None
            
            can_make_offer, offer_block_msg = PurchaseIntentService.get_negotiation_offer_rules(
                intent, request.user
            )

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
                    'meeting_type': existing_order.meeting_type,
                    'meeting_confirmed_by_buyer': existing_order.meeting_confirmed_by_buyer,
                    'meeting_confirmed_by_seller': existing_order.meeting_confirmed_by_seller,
                    'meeting_agreed': bool(
                        existing_order.meeting_type
                        and existing_order.meeting_confirmed_by_buyer
                        and existing_order.meeting_confirmed_by_seller
                    ),
                }
                
                # Récupérer les infos de vérification si la commande est payée
                if existing_order.status in [C2COrder.PAID, C2COrder.PENDING_DELIVERY, C2COrder.DELIVERED, C2COrder.VERIFIED, C2COrder.COMPLETED]:
                    try:
                        verification = existing_order.delivery_verification
                        codes_unlocked = verification.codes_unlocked_for_exchange()
                        # Codes masqués tant que les deux parties n'ont pas confirmé remise/réception
                        verification_data = {
                            'status': verification.status,
                            'seller_code': verification.seller_code if codes_unlocked else None,
                            'buyer_code': verification.buyer_code if codes_unlocked else None,
                            'codes_unlocked': codes_unlocked,
                            'buyer_handover_confirmed': bool(verification.buyer_handover_confirmed_at),
                            'seller_handover_confirmed': bool(verification.seller_handover_confirmed_at),
                            'seller_code_verified': verification.seller_code_verified,
                            'buyer_code_verified': verification.buyer_code_verified,
                            'is_completed': verification.is_completed(),
                        }
                    except Exception:
                        pass
            except Exception:
                pass
            
            # Nombre d'acheteurs concurrents actifs sur ce produit
            competing_buyers = 0
            try:
                competing_buyers = PurchaseIntent.objects.filter(
                    product=intent.product,
                    status__in=[
                        PurchaseIntent.PENDING, PurchaseIntent.AWAITING_AVAILABILITY,
                        PurchaseIntent.NEGOTIATING,
                    ]
                ).exclude(id=intent.id).count()
            except Exception:
                pass

            return JsonResponse({
                'success': True,
                'purchase_intent_id': intent.id,
                'initial_price': str(intent.initial_price),
                'negotiated_price': str(accepted_neg.proposed_price if accepted_neg else intent.negotiated_price) if (accepted_neg or intent.negotiated_price) else None,
                'final_price': str(intent.final_price) if intent.final_price else None,
                'status': intent.status,
                'availability_confirmed': bool(intent.availability_confirmed_at),
                'buyer_id': intent.buyer.id,
                'seller_id': intent.seller.id,
                'negotiations': negotiations_data,
                'can_accept_final_price': can_accept_final_price,
                'can_make_offer': can_make_offer,
                'offer_form_block_message': offer_block_msg or '',
                'order_id': order_id,
                'order_status': order_status,
                'order': order_data,
                'verification': verification_data,
                'competing_buyers': competing_buyers,
            })
        else:
            return JsonResponse({'success': False, 'purchase_intent_id': None})
    except Exception as e:
        logger.exception("Error in get_purchase_intent_for_conversation")
        return JsonResponse({'success': False, 'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def create_purchase_intent(request, product_id):
    """
    Crée une intention d'achat pour un produit C2C
    Remplace le paiement direct par un système de négociation obligatoire
    """
    product = get_object_or_404(PeerToPeerProduct, id=product_id, status=PeerToPeerProduct.APPROVED)
    wants_json = _purchase_intent_wants_json(request)

    if product.seller == request.user:
        msg = "Vous ne pouvez pas acheter votre propre article."
        if wants_json:
            return JsonResponse({'success': False, 'error': msg}, status=403)
        messages.error(request, msg)
        return redirect('accounts:peer-product-details', slug=product.PRDSlug)

    messages_url = reverse('accounts:my-messages') + f'?product_id={product.id}&action=propose_offer'

    if request.method == 'POST':
        try:
            logger.info('[C2C·FLOW] create_purchase_intent POST user=%s product=#%d price=%s',
                        request.user.pk, product.id, product.PRDPrice)
            PurchaseIntentService.create_purchase_intent(
                product=product,
                buyer=request.user,
                initial_price=product.PRDPrice
            )
            logger.info('[C2C·FLOW] Intent créée avec succès pour product=#%d buyer=%s', product.id, request.user.pk)
            messages.success(request, "Intention d'achat créée. Une conversation a été ouverte avec le vendeur.")
            if wants_json:
                return JsonResponse({'success': True, 'redirect': messages_url})
            return redirect(messages_url)
        except Exception as e:
            if 'UNIQUE constraint' in str(e) or 'unique constraint' in str(e).lower():
                try:
                    existing_intent = PurchaseIntent.objects.filter(
                        product=product,
                        buyer=request.user
                    ).first()
                    if existing_intent:
                        info_msg = "Une intention d'achat existe déjà pour cet article. Redirection vers la messagerie..."
                        messages.info(request, info_msg)
                        if wants_json:
                            return JsonResponse({'success': True, 'redirect': messages_url, 'message': info_msg})
                        return redirect(messages_url)
                except Exception:
                    pass
            err_msg = f"Erreur lors de la création de l'intention d'achat: {str(e)}"
            if wants_json:
                return JsonResponse({'success': False, 'error': err_msg}, status=400)
            messages.error(request, err_msg)
            return redirect('accounts:peer-product-details', slug=product.PRDSlug)

    if wants_json:
        if product.product_image:
            image_url = request.build_absolute_uri(product.product_image.url)
        else:
            image_url = request.build_absolute_uri(
                settings.STATIC_URL + 'assets/imgs/theme/no-image.png'
            )
        price_num = product.PRDPrice
        try:
            price_label = f"{int(price_num):,}".replace(',', '\u202f') + '\u00a0FCFA'
        except (TypeError, ValueError):
            price_label = f"{price_num}\u00a0FCFA"
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.product_name,
                'slug': product.PRDSlug,
                'image_url': image_url,
                'seller_name': product.seller.get_full_name() or product.seller.username,
                'price_label': price_label,
            },
        })

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
        logger.info('[C2C·FLOW] create_negotiation intent=#%d user=%s price=%s',
                    intent_id, request.user.pk, proposed_price)
        message = data.get('message', '')
        
        if proposed_price <= 0:
            return JsonResponse({'success': False, 'error': 'Le prix proposé doit être supérieur à 0'}, status=400)
        
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
        
    except ValidationError as e:
        text = ' '.join(getattr(e, 'messages', None) or []) or str(e)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': text}, status=400)
        messages.error(request, text)
        return redirect('accounts:my-messages')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('accounts:my-messages')


@login_required
@require_POST
def accept_negotiation(request, negotiation_id):
    """
    Accepte une proposition de négociation (destinataire uniquement)
    """
    logger.info('[C2C·FLOW] accept_negotiation #%d user=%s', negotiation_id, request.user.pk)
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
        logger.exception("Error in accept_negotiation")
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
@require_POST
def reject_negotiation(request, negotiation_id):
    """
    Refuse une proposition de négociation
    """
    logger.info('[C2C·FLOW] reject_negotiation #%d user=%s', negotiation_id, request.user.pk)
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
        logger.exception("Error in reject_negotiation")
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
@require_POST
def confirm_availability(request, intent_id):
    """
    Le vendeur confirme que son article est toujours en vente.
    Passe l'intention de PENDING → NEGOTIATING et enregistre availability_confirmed_at.
    Crée un message automatique dans la conversation.
    """
    logger.info('[C2C·FLOW] confirm_availability #%d user=%s', intent_id, request.user.pk)
    intent = get_object_or_404(PurchaseIntent, id=intent_id)

    if request.user != intent.seller:
        return JsonResponse({'error': "Seul le vendeur peut confirmer la disponibilité."}, status=403)

    if intent.status not in (PurchaseIntent.PENDING, PurchaseIntent.AWAITING_AVAILABILITY):
        return JsonResponse({
            'error': f"Cette action n'est plus possible (statut : {intent.get_status_display()}).",
            'current_status': intent.status,
        }, status=400)

    try:
        intent.availability_confirmed_at = timezone.now()
        intent.status = PurchaseIntent.NEGOTIATING
        intent.seller_notified = True
        intent.save(update_fields=['status', 'seller_notified', 'availability_confirmed_at'])

        from accounts.models import ProductConversation, ProductMessage
        try:
            conv = ProductConversation.objects.get(
                product=intent.product, buyer=intent.buyer, seller=intent.seller,
            )
            seller_name = intent.seller.get_full_name() or intent.seller.username
            ProductMessage.objects.create(
                conversation=conv,
                sender=intent.seller,
                message=(
                    f"✅ {seller_name} confirme que l'article « {intent.product.product_name} » "
                    f"est toujours disponible à la vente.\n\n"
                    f"💬 La négociation du prix est maintenant ouverte !"
                ),
            )
            conv.last_message_at = timezone.now()
            conv.save()
        except Exception as e:
            logger.error('[C2C·FLOW] confirm_availability msg error: %s', e)

        logger.info('[C2C·FLOW] Disponibilité confirmée intent=#%d → NEGOTIATING', intent.id)
        return JsonResponse({
            'success': True,
            'message': "Article confirmé disponible ! La négociation est ouverte.",
        })
    except Exception as e:
        logger.exception('[C2C·FLOW] confirm_availability ERROR')
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def decline_availability(request, intent_id):
    """
    Le vendeur indique que l'article n'est plus disponible → CANCELLED.
    """
    logger.info('[C2C·FLOW] decline_availability #%d user=%s', intent_id, request.user.pk)
    intent = get_object_or_404(PurchaseIntent, id=intent_id)

    if request.user != intent.seller:
        return JsonResponse({'error': "Seul le vendeur peut effectuer cette action."}, status=403)

    if intent.status not in (PurchaseIntent.PENDING, PurchaseIntent.AWAITING_AVAILABILITY):
        return JsonResponse({'error': "Action impossible pour le statut actuel."}, status=400)

    try:
        intent.status = PurchaseIntent.CANCELLED
        intent.seller_notified = True
        intent.save(update_fields=['status', 'seller_notified'])

        from accounts.models import ProductConversation, ProductMessage
        try:
            conv = ProductConversation.objects.get(
                product=intent.product, buyer=intent.buyer, seller=intent.seller,
            )
            seller_name = intent.seller.get_full_name() or intent.seller.username
            ProductMessage.objects.create(
                conversation=conv,
                sender=intent.seller,
                message=f"❌ {seller_name} indique que l'article « {intent.product.product_name} » n'est plus disponible.",
            )
            conv.last_message_at = timezone.now()
            conv.save()
        except Exception:
            pass

        return JsonResponse({'success': True, 'message': "Intention annulée — article indisponible."})
    except Exception as e:
        logger.exception('[C2C·FLOW] decline_availability ERROR')
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def accept_purchase_intent(request, intent_id):
    """
    Accepte une intention d'achat (le vendeur accepte de négocier).
    Si la disponibilité n'a pas encore été confirmée, la confirme en même temps.
    """
    logger.info('[C2C·FLOW] accept_purchase_intent #%d user=%s', intent_id, request.user.pk)
    intent = get_object_or_404(PurchaseIntent, id=intent_id)
    
    if request.user != intent.seller:
        return JsonResponse({'error': 'Seul le vendeur peut accepter cette intention d\'achat.'}, status=403)
    
    if intent.status not in [PurchaseIntent.PENDING, PurchaseIntent.AWAITING_AVAILABILITY, PurchaseIntent.NEGOTIATING]:
        return JsonResponse({
            'error': f'Cette intention d\'achat ne peut plus être acceptée. Statut actuel: {intent.get_status_display()}',
            'current_status': intent.status
        }, status=400)
    
    try:
        if not intent.availability_confirmed_at:
            intent.availability_confirmed_at = timezone.now()
        intent.status = PurchaseIntent.NEGOTIATING
        intent.seller_notified = True
        intent.save()
        
        # Créer un message automatique
        from accounts.models import ProductConversation, ProductMessage
        from django.db import connection as db_connection
        
        # Vérifier si la table existe
        try:
            table_exists = 'accounts_productconversation' in db_connection.introspection.table_names()
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
                logger.error(f"Error creating message in accept_purchase_intent: {msg_error}")
        
        return JsonResponse({
            'success': True,
            'message': 'Intention d\'achat acceptée. Vous pouvez maintenant négocier le prix.',
            'product_id': intent.product.id,
            'conversation_id': conversation.id if table_exists and 'conversation' in locals() else None
        })
    except Exception as e:
        logger.exception("Error in accept_purchase_intent")
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
@require_POST
def reject_purchase_intent(request, intent_id):
    """
    Refuse une intention d'achat
    """
    logger.info('[C2C·FLOW] reject_purchase_intent #%d user=%s', intent_id, request.user.pk)
    intent = get_object_or_404(PurchaseIntent, id=intent_id)
    
    # Vérifier que c'est le vendeur
    if request.user != intent.seller:
        return JsonResponse({'error': 'Seul le vendeur peut refuser cette intention d\'achat.'}, status=403)
    
    # Vérifier le statut
    if intent.status not in [PurchaseIntent.PENDING, PurchaseIntent.AWAITING_AVAILABILITY, PurchaseIntent.NEGOTIATING]:
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
        try:
            table_exists = 'accounts_productconversation' in db_connection.introspection.table_names()
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
                logger.error(f"Error creating message in reject_purchase_intent: {msg_error}")
        
        return JsonResponse({
            'success': True,
            'message': 'Intention d\'achat refusée.'
        })
    except Exception as e:
        logger.exception("Error in reject_purchase_intent")
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
@require_POST
def cancel_purchase_intent(request, intent_id):
    """
    Annule une intention d'achat (par l'acheteur ou le vendeur)
    """
    logger.info('[C2C·FLOW] cancel_purchase_intent #%d user=%s', intent_id, request.user.pk)
    intent = get_object_or_404(PurchaseIntent, id=intent_id)
    
    # Vérifier que c'est l'acheteur ou le vendeur
    if request.user not in [intent.buyer, intent.seller]:
        return JsonResponse({'error': 'Vous n\'avez pas la permission d\'annuler cette intention d\'achat.'}, status=403)
    
    # Vérifier le statut - ne peut être annulé que si en attente ou en négociation
    if intent.status not in [PurchaseIntent.PENDING, PurchaseIntent.AWAITING_AVAILABILITY, PurchaseIntent.NEGOTIATING]:
        return JsonResponse({'error': 'Cette intention d\'achat ne peut plus être annulée.'}, status=400)
    
    try:
        intent.status = PurchaseIntent.CANCELLED
        intent.seller_notified = True  # Marquer comme notifié pour ne plus compter
        intent.save()
        
        # Créer un message automatique dans la conversation si elle existe
        from accounts.models import ProductConversation, ProductMessage
        from django.db import connection as db_connection
        
        # Vérifier si la table existe
        try:
            table_exists = 'accounts_productconversation' in db_connection.introspection.table_names()
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
        logger.exception("Error in cancel_purchase_intent")
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
@require_POST
def accept_final_price(request, intent_id):
    """
    Accepte un prix final et crée la commande C2C
    """
    logger.info('[C2C·FLOW] accept_final_price intent=#%d user=%s', intent_id, request.user.pk)
    intent = get_object_or_404(PurchaseIntent, id=intent_id)
    
    # Vérifier les permissions
    if request.user not in [intent.buyer, intent.seller]:
        messages.error(request, "Vous n'avez pas la permission d'effectuer cette action.")
        return redirect('accounts:my-messages')
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        final_price = Decimal(str(data.get('final_price', intent.final_price or intent.negotiated_price)))
        logger.info('[C2C·FLOW] accept_final_price → final_price=%s', final_price)
        
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

    # Annulation possible tant que la double vérification n'est pas faite (fonds en escrow)
    can_cancel = False
    if verification and order.status in (C2COrder.PAID, C2COrder.PENDING_DELIVERY, C2COrder.DELIVERED):
        if not verification.is_completed():
            t = getattr(order, 'payment_transaction', None)
            if t and getattr(t, 'escrow_status', None) == 'escrow_pending':
                can_cancel = True
    
    is_buyer = request.user == order.buyer
    is_seller = request.user == order.seller

    # Fenêtre de litige : 48h après completed_at, acheteur uniquement, pas de litige déjà ouvert
    can_dispute = False
    existing_dispute = None
    if is_buyer and order.status == C2COrder.COMPLETED:
        existing_dispute = DisputeCase.objects.filter(order=order).first()
        if not existing_dispute:
            if order.dispute_deadline:
                can_dispute = timezone.now() <= order.dispute_deadline
            else:
                # Fallback: 48h après completed_at si dispute_deadline pas encore renseigné
                if order.completed_at:
                    can_dispute = timezone.now() <= order.completed_at + timezone.timedelta(hours=48)

    popular_min_uses = get_popular_meeting_min_uses()

    safe_zones = []
    safe_zones_geo = []
    popular_points_geo = []
    if order.status in (C2COrder.PAID, C2COrder.PENDING_DELIVERY, C2COrder.DELIVERED, C2COrder.PENDING_PAYMENT):
        safe_zones, safe_zones_geo = get_safe_zones_models_and_geo(limit=20)
        popular_points_geo = build_popular_points_geo(
            popular_min_uses=popular_min_uses,
        )

    # Point de rencontre : montrer le picker si la commande est en cours après paiement
    show_meeting_picker = order.status in (C2COrder.PAID, C2COrder.PENDING_DELIVERY, C2COrder.DELIVERED)

    meeting_pending_scroll = request.GET.get('meeting_pending') == '1'

    # Notation post-transaction (acheteur → vendeur, vendeur → acheteur)
    c2c_review_button_url = None
    c2c_review_button_text = None
    c2c_review_done_message = None
    if order.status == C2COrder.COMPLETED:
        if is_buyer:
            if SellerReview.objects.filter(order=order).exists():
                c2c_review_done_message = (
                    "Vous avez déjà laissé un avis sur le vendeur pour cette commande."
                )
            else:
                ok, _ = SellerReview.can_review(order, request.user)
                if ok:
                    c2c_review_button_url = reverse('c2c:create-review', args=[order.id])
                    c2c_review_button_text = "Noter le vendeur"
        elif is_seller:
            if BuyerReview.objects.filter(order=order).exists():
                c2c_review_done_message = (
                    "Vous avez déjà laissé un avis sur l'acheteur pour cette commande."
                )
            else:
                ok, _ = BuyerReview.can_review(order, request.user)
                if ok:
                    c2c_review_button_url = reverse('c2c:create-review', args=[order.id])
                    c2c_review_button_text = "Noter l'acheteur"

    context = {
        'order': order,
        'verification': verification,
        'is_buyer': is_buyer,
        'is_seller': is_seller,
        'can_cancel': can_cancel,
        'can_dispute': can_dispute,
        'existing_dispute': existing_dispute,
        'safe_zones': safe_zones,
        'safe_zones_geo_json': safe_zones_geo,
        'popular_points_geo_json': popular_points_geo,
        'show_meeting_picker': show_meeting_picker,
        'meeting_pending_scroll': meeting_pending_scroll,
        'c2c_review_button_url': c2c_review_button_url,
        'c2c_review_button_text': c2c_review_button_text,
        'c2c_review_done_message': c2c_review_done_message,
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
            'commission_rate_seller': platform_settings.c2c_seller_commission_rate,
        }
        return render(request, 'c2c/payment.html', context)
    
    # Si POST, initialiser le paiement
    try:
        buyer_phone = ''
        try:
            buyer_phone = (order.buyer.profile.mobile_number or '').strip()
        except Exception:
            buyer_phone = ''
        if not buyer_phone:
            messages.error(
                request,
                "Ajoutez votre numero de telephone dans votre profil avant de payer (obligatoire pour l'escrow et les remboursements)."
            )
            return redirect('accounts:account_details')

        # Initialiser le paiement SingPay via l'API réelle
        singpay_transaction = SingPayService.init_c2c_payment(order, request)
        
        # Rediriger vers l'URL de paiement SingPay
        if singpay_transaction.payment_url:
            return redirect(singpay_transaction.payment_url)
        else:
            messages.error(request, "URL de paiement non disponible. Veuillez réessayer.")
            return redirect('c2c:order-detail', order_id=order_id)
        
    except Exception as e:
        logger.exception(f"Erreur lors de l'initialisation du paiement C2C: {str(e)}")
        messages.error(request, f"Erreur lors de l'initialisation du paiement: {str(e)}")
        return redirect('c2c:order-detail', order_id=order_id)




@login_required
def payment_success(request, order_id):
    """
    Page de succès de paiement C2C - Redirige vers la messagerie
    """
    logger.info('[C2C·FLOW] payment_success order=#%d user=%s', order_id, request.user.pk)
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
            logger.info('[C2C·FLOW] order #%d → PAID', order.id)
    
    # Récupérer les codes de vérification
    verification = None
    try:
        verification = order.delivery_verification
    except DeliveryVerification.DoesNotExist:
        # Créer la vérification si elle n'existe pas
        verification = DeliveryVerification.objects.create(c2c_order=order)
    
    # Ne pas afficher les codes ici : ils sont révélés dans la messagerie après confirmation mutuelle remise/réception.
    if request.user == order.buyer:
        messages.success(
            request,
            "Paiement réussi ! Dans la messagerie, confirmez la réception puis échangez les codes de vérification avec le vendeur."
        )
    else:
        messages.success(
            request,
            "Paiement reçu ! Dans la messagerie, confirmez la remise puis échangez les codes de vérification avec l’acheteur."
        )
    
    # Rediriger vers la messagerie avec le produit concerné
    from django.urls import reverse
    return redirect(f"{reverse('accounts:my-messages')}?product_id={order.product.id}")


@login_required
@require_POST
def cancel_c2c_order(request, order_id):
    """
    Annule une commande C2C avant la double vérification des codes.
    L'acheteur est remboursé (montant - frais), la plateforme garde les frais de service.
    Accessible à l'acheteur ou au vendeur.
    """
    logger.info('[C2C·FLOW] cancel_c2c_order order=#%d user=%s', order_id, request.user.pk)
    from payments.escrow_service import EscrowService
    from payments.models import SingPayTransaction

    order = get_object_or_404(C2COrder, id=order_id)
    if request.user not in [order.buyer, order.seller]:
        messages.error(request, "Vous n'avez pas le droit d'annuler cette commande.")
        return redirect('c2c:order-detail', order_id=order_id)

    if order.status not in (C2COrder.PAID, C2COrder.PENDING_DELIVERY, C2COrder.DELIVERED):
        messages.error(request, "Cette commande ne peut plus être annulée.")
        return redirect('c2c:order-detail', order_id=order_id)

    try:
        verification = order.delivery_verification
        if verification.is_completed():
            messages.error(request, "La double vérification des codes est déjà effectuée ; l'annulation n'est plus possible.")
            return redirect('c2c:order-detail', order_id=order_id)
    except Exception:
        pass

    if not order.payment_transaction or order.payment_transaction.escrow_status != SingPayTransaction.ESCROW_PENDING:
        messages.error(request, "Aucun paiement en attente à annuler pour cette commande.")
        return redirect('c2c:order-detail', order_id=order_id)

    initiated_by = 'buyer' if request.user == order.buyer else 'seller'
    reason = request.POST.get('reason', f'Annulation par l\'{initiated_by} avant double vérification')
    success, response = EscrowService.refund_escrow_c2c_cancel(order, reason=reason, initiated_by=initiated_by)

    if success:
        messages.success(
            request,
            "Transaction annulée. Vous serez remboursé sous peu (frais de service conservés par la plateforme)."
        )
    else:
        messages.error(request, response.get('error', "Impossible d'annuler la transaction."))
    return redirect('c2c:order-detail', order_id=order_id)


@login_required
@require_POST
def confirm_handover(request, order_id):
    """
    Confirmation mutuelle avant affichage des codes A/V : l'acheteur confirme la réception,
    le vendeur confirme la remise.
    """
    logger.info('[C2C·FLOW] confirm_handover order=#%d user=%s', order_id, request.user.pk)
    order = get_object_or_404(C2COrder, id=order_id)
    if request.user not in (order.buyer, order.seller):
        logger.warning('[C2C·FLOW] confirm_handover DENIED user=%s order=#%d', request.user.pk, order_id)
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    if order.status not in (
        C2COrder.PAID,
        C2COrder.PENDING_DELIVERY,
        C2COrder.DELIVERED,
        C2COrder.VERIFIED,
        C2COrder.COMPLETED,
    ):
        return JsonResponse({'error': 'Commande non éligible'}, status=400)

    verification, _ = DeliveryVerification.objects.get_or_create(c2c_order=order)
    if verification.is_completed():
        return JsonResponse({
            'success': True,
            'buyer_handover_confirmed': True,
            'seller_handover_confirmed': True,
            'codes_unlocked': True,
        })

    now = timezone.now()
    if request.user == order.buyer and not verification.buyer_handover_confirmed_at:
        verification.buyer_handover_confirmed_at = now
        verification.save(update_fields=['buyer_handover_confirmed_at'])
    elif request.user == order.seller and not verification.seller_handover_confirmed_at:
        verification.seller_handover_confirmed_at = now
        verification.save(update_fields=['seller_handover_confirmed_at'])

    verification.refresh_from_db()
    unlocked = verification.codes_unlocked_for_exchange()
    logger.info('[C2C·FLOW] confirm_handover OK order=#%d buyer=%s seller=%s unlocked=%s',
                order.id,
                bool(verification.buyer_handover_confirmed_at),
                bool(verification.seller_handover_confirmed_at),
                unlocked)
    return JsonResponse({
        'success': True,
        'buyer_handover_confirmed': bool(verification.buyer_handover_confirmed_at),
        'seller_handover_confirmed': bool(verification.seller_handover_confirmed_at),
        'codes_unlocked': unlocked,
    })


@login_required
@require_POST
def verify_seller_code(request, order_id):
    """
    Vérifie le code vendeur (V-CODE) — le vendeur saisit le A-CODE de l'acheteur.
    """
    logger.info('[C2C·FLOW] verify_seller_code order=#%d user=%s', order_id, request.user.pk)
    order = get_object_or_404(C2COrder, id=order_id)
    
    # Vérifier que c'est le vendeur
    if request.user != order.seller:
        logger.warning('[C2C·FLOW] verify_seller_code DENIED user=%s (not seller) order=#%d', request.user.pk, order_id)
        return JsonResponse({'error': 'Seul le vendeur peut vérifier ce code'}, status=403)
    
    try:
        verification = order.delivery_verification
        if not verification.codes_unlocked_for_exchange():
            return JsonResponse({
                'error': 'Les codes ne sont disponibles qu’après confirmation mutuelle (réception et remise) dans la messagerie.',
                'codes_locked': True,
            }, status=403)
    except Exception:
        return JsonResponse({'error': 'Vérification indisponible'}, status=400)
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        code = data.get('code', '').strip()
        
        if DeliveryVerificationService.verify_seller_code(order, code):
            logger.info('[C2C·FLOW] verify_seller_code OK order=#%d', order.id)
            order.refresh_from_db()
            can_review = False
            review_url = None
            try:
                verification = order.delivery_verification
                if verification.buyer_code_verified and verification.seller_code_verified:
                    can_review, _ = BuyerReview.can_review(order, order.seller)
                    if can_review:
                        review_url = reverse('c2c:create-review', args=[order.id])
            except Exception:
                pass
            
            return JsonResponse({
                'success': True,
                'message': 'Code vendeur vérifié avec succès',
                'can_review': can_review,
                'review_url': review_url
            })
        else:
            logger.warning('[C2C·FLOW] verify_seller_code FAIL code invalide order=#%d', order.id)
            return JsonResponse({
                'error': 'Code invalide ou déjà vérifié'
            }, status=400)
            
    except Exception as e:
        logger.exception('[C2C·FLOW] verify_seller_code ERROR order=#%d', order_id)
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def verify_buyer_code(request, order_id):
    """
    Vérifie le code acheteur (V-CODE) — l'acheteur saisit le V-CODE du vendeur.
    """
    logger.info('[C2C·FLOW] verify_buyer_code order=#%d user=%s', order_id, request.user.pk)
    order = get_object_or_404(C2COrder, id=order_id)
    
    # Vérifier que c'est l'acheteur
    if request.user != order.buyer:
        logger.warning('[C2C·FLOW] verify_buyer_code DENIED user=%s (not buyer) order=#%d', request.user.pk, order_id)
        return JsonResponse({'error': 'Seul l\'acheteur peut vérifier ce code'}, status=403)
    
    try:
        verification = order.delivery_verification
        if not verification.codes_unlocked_for_exchange():
            return JsonResponse({
                'error': 'Les codes ne sont disponibles qu’après confirmation mutuelle (réception et remise) dans la messagerie.',
                'codes_locked': True,
            }, status=403)
    except Exception:
        return JsonResponse({'error': 'Vérification indisponible'}, status=400)
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        code = data.get('code', '').strip()
        
        if DeliveryVerificationService.verify_buyer_code(order, code):
            logger.info('[C2C·FLOW] verify_buyer_code OK order=#%d — transaction potentiellement complète', order.id)
            order.refresh_from_db()
            can_review = False
            review_url = None
            try:
                can_review, _ = SellerReview.can_review(order, order.buyer)
                if can_review:
                    review_url = reverse('c2c:create-review', args=[order.id])
            except Exception:
                pass
            
            return JsonResponse({
                'success': True,
                'message': 'Code vérifié avec succès. La transaction est maintenant complète !',
                'can_review': can_review,
                'review_url': review_url
            })
        else:
            logger.warning('[C2C·FLOW] verify_buyer_code FAIL code invalide order=#%d', order.id)
            return JsonResponse({
                'error': 'Code invalide ou déjà vérifié'
            }, status=400)
            
    except Exception as e:
        logger.exception('[C2C·FLOW] verify_buyer_code ERROR order=#%d', order_id)
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
        logger.exception("Erreur lors de l'achat du boost")
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
def seller_dashboard(request):
    """
    Dashboard du vendeur C2C — vue enrichie avec niveau, avis, revenus et activité récente.
    """
    from django.db.models import Sum, Avg, Count
    from .models import SellerReview

    # ── Commandes ──────────────────────────────────────────────────
    all_orders_qs = C2COrder.objects.filter(seller=request.user)
    total_orders = all_orders_qs.count()
    pending_orders = all_orders_qs.filter(
        status__in=[C2COrder.PAID, C2COrder.PENDING_DELIVERY, C2COrder.DELIVERED]
    ).count()
    completed_orders = all_orders_qs.filter(status=C2COrder.COMPLETED).count()
    disputed_orders = all_orders_qs.filter(status=C2COrder.DISPUTED).count()
    revenue_agg = all_orders_qs.filter(status=C2COrder.COMPLETED).aggregate(
        total=Sum('seller_net'))
    total_revenue = revenue_agg['total'] or 0

    # ── Intentions d'achat ──────────────────────────────────────────
    pending_intents = PurchaseIntent.objects.filter(
        seller=request.user,
        status__in=[PurchaseIntent.PENDING, PurchaseIntent.AWAITING_AVAILABILITY, PurchaseIntent.NEGOTIATING]
    ).select_related('product', 'buyer').order_by('-created_at')[:5]

    active_intents_count = PurchaseIntent.objects.filter(
        seller=request.user,
        status__in=[PurchaseIntent.PENDING, PurchaseIntent.AWAITING_AVAILABILITY, PurchaseIntent.NEGOTIATING]
    ).count()

    # ── Avis vendeur ────────────────────────────────────────────────
    review_stats = {'average_rating': 0, 'total_reviews': 0}
    try:
        review_stats = SellerReview.get_seller_stats(request.user)
    except Exception:
        pass

    # ── Niveau vendeur ──────────────────────────────────────────────
    seller_level = None
    try:
        seller_level = request.user.profile.get_seller_level()
    except Exception:
        pass

    # ── Commandes récentes (5 dernières toutes statuts) ────────────
    recent_orders = all_orders_qs.select_related('product', 'buyer').order_by('-created_at')[:5]

    # ── Articles actifs ─────────────────────────────────────────────
    from accounts.models import PeerToPeerProduct as P2P
    active_listings = P2P.objects.filter(seller=request.user, status=P2P.APPROVED).count()
    total_listings = P2P.objects.filter(seller=request.user).count()

    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'disputed_orders': disputed_orders,
        'total_revenue': total_revenue,
        'pending_intents': pending_intents,
        'active_intents_count': active_intents_count,
        'review_stats': review_stats,
        'seller_level': seller_level,
        'recent_orders': recent_orders,
        'active_listings': active_listings,
        'total_listings': total_listings,
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


@login_required
@require_http_methods(["GET", "POST"])
def open_dispute(request, order_id):
    """
    Ouvre un litige sur une commande terminée dans la fenêtre de 48h.
    Seul l'acheteur peut ouvrir un litige.
    """
    order = get_object_or_404(C2COrder, id=order_id)

    if request.user != order.buyer:
        messages.error(request, "Seul l'acheteur peut ouvrir un litige.")
        return redirect('c2c:order-detail', order_id=order_id)

    if order.status != C2COrder.COMPLETED:
        messages.error(request, "Vous ne pouvez ouvrir un litige que sur une commande terminée.")
        return redirect('c2c:order-detail', order_id=order_id)

    # Vérifier la fenêtre de 48h
    if order.dispute_deadline and timezone.now() > order.dispute_deadline:
        messages.error(request, "Le délai de 48h pour ouvrir un litige est dépassé.")
        return redirect('c2c:order-detail', order_id=order_id)

    # Un seul litige par commande
    existing = DisputeCase.objects.filter(order=order).first()
    if existing:
        messages.warning(request, "Un litige est déjà ouvert pour cette commande.")
        return redirect('c2c:order-detail', order_id=order_id)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        description = request.POST.get('description', '').strip()

        valid_reasons = [r for r, _ in DisputeCase.REASON_CHOICES]
        if reason not in valid_reasons:
            messages.error(request, "Motif de litige invalide.")
            return redirect('c2c:open-dispute', order_id=order_id)

        if len(description) < 20:
            messages.error(request, "La description doit comporter au moins 20 caractères.")
            return redirect('c2c:open-dispute', order_id=order_id)

        DisputeCase.objects.create(
            order=order,
            claimant=request.user,
            reason=reason,
            description=description,
        )
        messages.success(
            request,
            "Votre litige a été ouvert. L'équipe Gabomazone vous contactera sous 48h."
        )
        return redirect('c2c:order-detail', order_id=order_id)

    context = {
        'order': order,
        'reason_choices': DisputeCase.REASON_CHOICES,
    }
    return render(request, 'c2c/open_dispute.html', context)


def safe_zones_list(request):
    """Liste publique des zones d'échange sécurisées Gabomazone."""
    zones = SafeZone.objects.filter(status=SafeZone.ACTIVE).order_by('-is_featured', 'city', 'name')
    context = {'zones': zones}
    return render(request, 'c2c/safe_zones.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def set_meeting_point(request, order_id):
    """
    Permet à l'acheteur ou au vendeur de proposer un point de rencontre
    pour la remise de l'article.
    GET  → retourne l'état actuel (JSON)
    POST → enregistre le point proposé / confirme l'accord
    """
    order = get_object_or_404(C2COrder, id=order_id)

    if request.user not in [order.buyer, order.seller]:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)

    if order.status not in ['paid', 'pending_delivery', 'delivered']:
        return JsonResponse({'error': 'Le point de rencontre ne peut être défini qu\'après paiement.'}, status=400)

    if request.method == 'GET':
        return _meeting_point_json(order)

    try:
        payload = json.loads(request.body or '{}')
    except Exception:
        return JsonResponse({'error': 'Corps JSON invalide'}, status=400)

    action = payload.get('action', 'propose')

    if action == 'confirm':
        # L'autre partie confirme le point proposé
        if request.user == order.buyer:
            order.meeting_confirmed_by_buyer = True
        else:
            order.meeting_confirmed_by_seller = True
        order.save()
        return _meeting_point_json(order, message='Point de rencontre confirmé !')

    # Propose / mise à jour du point de rencontre
    meeting_type = payload.get('meeting_type')
    if meeting_type not in [C2COrder.MEETING_SAFE_ZONE, C2COrder.MEETING_CUSTOM]:
        return JsonResponse({'error': 'Type de point de rencontre invalide.'}, status=400)

    order.meeting_type = meeting_type
    order.meeting_proposed_by = request.user
    order.meeting_confirmed_by_buyer = False
    order.meeting_confirmed_by_seller = False

    if meeting_type == C2COrder.MEETING_SAFE_ZONE:
        zone_id = payload.get('safe_zone_id')
        zone = SafeZone.objects.filter(id=zone_id, status=SafeZone.ACTIVE).first()
        if not zone:
            return JsonResponse({'error': 'Zone introuvable ou inactive.'}, status=400)
        order.meeting_safe_zone = zone
        order.meeting_address = None
        order.meeting_latitude = zone.latitude
        order.meeting_longitude = zone.longitude
    else:
        address = (payload.get('address') or '').strip()
        if len(address) < 10:
            return JsonResponse({'error': 'Adresse trop courte (10 caractères minimum).'}, status=400)
        order.meeting_address = address
        order.meeting_safe_zone = None
        # Décharge explicite : l'utilisateur accepte que Gabomazone n'est pas responsable
        if not payload.get('liability_waiver'):
            return JsonResponse({'error': 'Vous devez accepter la décharge de responsabilité.'}, status=400)
        # Coordonnées GPS du lieu choisi sur la carte (optionnelles mais fortement recommandées)
        try:
            lat = payload.get('latitude')
            lng = payload.get('longitude')
            order.meeting_latitude = float(lat) if lat is not None else None
            order.meeting_longitude = float(lng) if lng is not None else None
        except (TypeError, ValueError):
            order.meeting_latitude = None
            order.meeting_longitude = None

    order.meeting_notes = (payload.get('notes') or '')[:200]

    # La personne qui propose confirme automatiquement de son côté
    if request.user == order.buyer:
        order.meeting_confirmed_by_buyer = True
    else:
        order.meeting_confirmed_by_seller = True

    order.save()

    # Envoyer un message dans la conversation
    try:
        from accounts.models import ProductConversation, ProductMessage
        conv = ProductConversation.objects.filter(
            product=order.product, buyer=order.buyer, seller=order.seller
        ).first()
        if conv:
            proposer_name = request.user.get_full_name() or request.user.username
            if meeting_type == C2COrder.MEETING_SAFE_ZONE:
                loc = f"Zone Gabomazone : {order.meeting_safe_zone.name}"
            else:
                loc = f"Point personnalisé : {order.meeting_address}"
            detail_url = request.build_absolute_uri(
                reverse('c2c:order-detail', args=[order.id]) + '?meeting_pending=1'
            )
            msg = (
                f"📍 Point de rencontre proposé par {proposer_name} — {loc}"
                f"\n\nOuvrez la fiche commande pour voir la carte et confirmer ce lieu (ou en proposer un autre) :\n{detail_url}"
            )
            if order.meeting_notes:
                msg += f"\nPrécisions : {order.meeting_notes}"
            ProductMessage.objects.create(conversation=conv, sender=request.user, message=msg)
            conv.last_message_at = timezone.now()
            conv.save()
    except Exception:
        pass

    resp = _meeting_point_json(order, message='Point de rencontre enregistré !')
    try:
        data = json.loads(resp.content.decode('utf-8'))
    except Exception:
        data = {}
    data['redirect_url'] = reverse('accounts:my-messages') + f'?product_id={order.product_id}'
    return JsonResponse(data)


def _meeting_point_json(order, message=None):
    """Helper — sérialise le point de rencontre d'une commande."""
    data = {
        'meeting_type': order.meeting_type,
        'meeting_confirmed_by_buyer': order.meeting_confirmed_by_buyer,
        'meeting_confirmed_by_seller': order.meeting_confirmed_by_seller,
        'both_confirmed': order.meeting_confirmed_by_buyer and order.meeting_confirmed_by_seller,
        'proposed_by_id': order.meeting_proposed_by_id,
        'meeting_notes': order.meeting_notes or '',
        'latitude': float(order.meeting_latitude) if order.meeting_latitude is not None else None,
        'longitude': float(order.meeting_longitude) if order.meeting_longitude is not None else None,
    }
    if order.meeting_type == C2COrder.MEETING_SAFE_ZONE and order.meeting_safe_zone:
        z = order.meeting_safe_zone
        data['safe_zone'] = {
            'id': z.id, 'name': z.name, 'address': z.address,
            'city': z.city, 'landmark': z.landmark or '', 'opening_hours': z.opening_hours or '',
            'latitude': float(z.latitude) if z.latitude is not None else None,
            'longitude': float(z.longitude) if z.longitude is not None else None,
        }
    elif order.meeting_type == C2COrder.MEETING_CUSTOM:
        data['custom_address'] = order.meeting_address or ''
    if message:
        data['message'] = message
    return JsonResponse(data)

