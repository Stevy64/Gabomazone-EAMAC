"""
Vues pour le système de notation des vendeurs C2C
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from .models import SellerReview, BuyerReview, C2COrder
from accounts.models import PeerToPeerProduct
from django.contrib.auth.models import User


@login_required(login_url='accounts:login')
def seller_profile(request, seller_id):
    """
    Affiche le profil d'un vendeur avec ses notes et commentaires
    """
    seller = get_object_or_404(User, id=seller_id)
    
    # Récupérer les statistiques du vendeur (avec gestion d'erreur si la table n'existe pas)
    try:
        stats = SellerReview.get_seller_stats(seller)
    except Exception as e:
        # Si la table n'existe pas encore (migrations non appliquées)
        stats = {
            'average_rating': 0,
            'total_reviews': 0,
            'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        }
    
    # Récupérer les avis visibles (avec gestion d'erreur si la table n'existe pas)
    try:
        reviews = SellerReview.objects.filter(
            seller=seller,
            is_visible=True
        ).select_related('reviewer', 'product', 'order').order_by('-created_at')
    except Exception as e:
        reviews = SellerReview.objects.none()
    
    # Pagination
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Vérifier si l'utilisateur peut noter ce vendeur (avec gestion d'erreur)
    can_review = False
    pending_review_order = None
    if request.user != seller:
        try:
            # Chercher une commande terminée non notée avec vérification complète
            pending_orders = C2COrder.objects.filter(
                buyer=request.user,
                seller=seller,
                status=C2COrder.COMPLETED
            ).exclude(
                review__reviewer=request.user
            ).order_by('-completed_at')
            
            # Filtrer pour ne garder que celles avec vérification complète
            for order in pending_orders:
                try:
                    verification = order.delivery_verification
                    if verification.seller_code_verified and verification.buyer_code_verified:
                        can_review, _ = SellerReview.can_review(order, request.user)
                        if can_review:
                            pending_review_order = order
                            break
                except:
                    continue
        except Exception as e:
            # Si la table n'existe pas encore
            pass
    
    # Produits du vendeur
    seller_products = PeerToPeerProduct.objects.filter(
        seller=seller,
        status=PeerToPeerProduct.APPROVED
    ).order_by('-date')[:6]
    
    context = {
        'seller': seller,
        'stats': stats,
        'reviews': page_obj,
        'can_review': can_review,
        'pending_review_order': pending_review_order,
        'seller_products': seller_products,
    }
    
    return render(request, 'c2c/seller_profile.html', context)


@login_required(login_url='accounts:login')
@require_http_methods(["GET", "POST"])
def create_review(request, order_id):
    """
    Crée ou modifie un avis pour une commande
    Détecte automatiquement si l'utilisateur est acheteur ou vendeur
    """
    order = get_object_or_404(C2COrder, id=order_id)
    
    # Déterminer si l'utilisateur est l'acheteur ou le vendeur
    is_buyer = request.user == order.buyer
    is_seller = request.user == order.seller
    
    if not (is_buyer or is_seller):
        messages.error(request, "Vous n'avez pas la permission de noter cette transaction.")
        return redirect('accounts:my-messages')
    
    # Vérifier les permissions selon le rôle
    if is_buyer:
        can_review, error_message = SellerReview.can_review(order, request.user)
        review_type = 'seller'
    else:
        can_review, error_message = BuyerReview.can_review(order, request.user)
        review_type = 'buyer'
    
    if not can_review:
        messages.error(request, error_message)
        return redirect('accounts:my-messages')
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        
        # Validation
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'La note doit être entre 1 et 5 étoiles.')
            return redirect('c2c:create-review', order_id=order_id)
        
        # Créer ou mettre à jour l'avis selon le type
        if is_buyer:
            review, created = SellerReview.objects.update_or_create(
                order=order,
                reviewer=request.user,
                defaults={
                    'seller': order.seller,
                    'product': order.product,
                    'rating': rating,
                    'comment': comment,
                    'is_visible': True,
                }
            )
            redirect_url = 'c2c:seller-profile'
            redirect_id = order.seller.id
        else:
            review, created = BuyerReview.objects.update_or_create(
                order=order,
                reviewer=request.user,
                defaults={
                    'buyer': order.buyer,
                    'product': order.product,
                    'rating': rating,
                    'comment': comment,
                    'is_visible': True,
                }
            )
            # Pour l'instant, rediriger vers les messages (on pourrait créer une page de profil acheteur)
            redirect_url = 'accounts:my-messages'
            redirect_id = None
        
        if created:
            messages.success(request, 'Votre avis a été publié avec succès. Merci !')
        else:
            messages.success(request, 'Votre avis a été mis à jour avec succès.')
        
        if redirect_id:
            return redirect(redirect_url, seller_id=redirect_id)
        return redirect(redirect_url)
    
    # GET - Afficher le formulaire
    # Vérifier si un avis existe déjà
    if is_buyer:
        existing_review = SellerReview.objects.filter(
            order=order,
            reviewer=request.user
        ).first()
        reviewed_user = order.seller
        reviewed_user_type = 'vendeur'
    else:
        existing_review = BuyerReview.objects.filter(
            order=order,
            reviewer=request.user
        ).first()
        reviewed_user = order.buyer
        reviewed_user_type = 'acheteur'
    
    context = {
        'order': order,
        'existing_review': existing_review,
        'review_type': review_type,
        'reviewed_user': reviewed_user,
        'reviewed_user_type': reviewed_user_type,
    }
    
    return render(request, 'c2c/create_review.html', context)


@login_required(login_url='accounts:login')
@require_http_methods(["POST"])
def delete_review(request, review_id):
    """
    Supprime un avis (seul l'auteur peut le supprimer)
    """
    review = get_object_or_404(SellerReview, id=review_id)
    
    if review.reviewer != request.user:
        messages.error(request, "Vous n'avez pas la permission de supprimer cet avis.")
        return redirect('c2c:seller-profile', seller_id=review.seller.id)
    
    seller_id = review.seller.id
    review.delete()
    messages.success(request, 'Votre avis a été supprimé.')
    
    return redirect('c2c:seller-profile', seller_id=seller_id)


@require_http_methods(["GET"])
def get_seller_stats(request, seller_id):
    """
    API endpoint pour récupérer les statistiques d'un vendeur
    """
    seller = get_object_or_404(User, id=seller_id)
    try:
        stats = SellerReview.get_seller_stats(seller)
        return JsonResponse({
            'average_rating': float(stats['average_rating']),
            'total_reviews': stats['total_reviews'],
            'rating_distribution': stats['rating_distribution'],
        })
    except Exception as e:
        # Si la table n'existe pas encore
        return JsonResponse({
            'average_rating': 0.0,
            'total_reviews': 0,
            'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        })

