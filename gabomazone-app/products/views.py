from django.shortcuts import render, get_object_or_404
from .models import Product, ProductImage, ProductRating, ProductSize, ProductFavorite
from django.core.paginator import Paginator
import random
from django.http import JsonResponse
from django.views.generic import View, TemplateView
from project import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Sum, Count
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from accounts.models import Profile
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from categories.models import SuperCategory
import json
# Create your views here.


def product_details(request, slug):
    print("DEFAULT_Currency: ", settings.DEFAULT_CURRENCY)
    if not request.session.has_key('currency'):
        request.session['currency'] = settings.DEFAULT_CURRENCY
        print("SESSION_Currency: ", request.session['currency'])

    product_detail = get_object_or_404(Product, PRDSlug=slug, PRDISactive=True)
    
    # Incrémenter le compteur de vues
    from django.db.models import F
    Product.objects.filter(id=product_detail.id).update(view_count=F('view_count') + 1)
    product_detail.refresh_from_db()
    
    product_variations = ProductSize.objects.all().filter(PRDIProduct=product_detail)
    product_image = ProductImage.objects.all().filter(PRDIProduct=product_detail)
    related_products_minicategor = product_detail.product_minicategor
    related_products = Product.objects.all().filter(
        product_minicategor=related_products_minicategor, PRDISactive=True)
    supplier_Products = Product.objects.all().filter(product_vendor=product_detail.product_vendor,
                                                     product_minicategor=related_products_minicategor, PRDISactive=True)

    # related = ProductAlternative.objects.all().filter(PALNProduct=product_detail)
    # related_products = product_detail.alternative_products.all()

    product_feedback = ProductRating.objects.all().filter(
        PRDIProduct=product_detail, active=True)
    feedback_sum = ProductRating.objects.all().filter(
        PRDIProduct=product_detail, active=True).aggregate(Sum('rate'))
    feedbak_number = product_feedback.count()

    try:

        average_rating = int(feedback_sum["rate__sum"]) / feedbak_number

        start_1_sum = ProductRating.objects.all().filter(
            PRDIProduct=product_detail, active=True, rate=1).count()

        start_2_sum = ProductRating.objects.all().filter(
            PRDIProduct=product_detail, active=True, rate=2).count()

        start_3_sum = ProductRating.objects.all().filter(
            PRDIProduct=product_detail, active=True, rate=3).count()

        start_4_sum = ProductRating.objects.all().filter(
            PRDIProduct=product_detail, active=True, rate=4).count()

        start_5_sum = ProductRating.objects.all().filter(
            PRDIProduct=product_detail, active=True, rate=5).count()

        start_1 = (start_1_sum / feedbak_number) * 100
        start_2 = (start_2_sum / feedbak_number) * 100
        start_3 = (start_3_sum / feedbak_number) * 100
        start_4 = (start_4_sum / feedbak_number) * 100
        start_5 = (start_5_sum / feedbak_number) * 100

    except:
        average_rating = 0
        start_1 = 0
        start_2 = 0
        start_3 = 0
        start_4 = 0
        start_5 = 0

    # Collecter toutes les images du produit pour la popup
    product_images = []
    if product_detail.product_image:
        product_images.append(product_detail.product_image)
    if product_detail.additional_image_1:
        product_images.append(product_detail.additional_image_1)
    if product_detail.additional_image_2:
        product_images.append(product_detail.additional_image_2)
    if product_detail.additional_image_3:
        product_images.append(product_detail.additional_image_3)
    if product_detail.additional_image_4:
        product_images.append(product_detail.additional_image_4)
    
    # Vérifier si le produit est dans les favoris de l'utilisateur
    is_favorited = False
    like_count = 0
    try:
        from .models import ProductFavorite
        from django.db import connection
        table_name = ProductFavorite._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            table_exists = cursor.fetchone() is not None
        
        if table_exists:
            if request.user.is_authenticated:
                is_favorited = ProductFavorite.objects.filter(product=product_detail, user=request.user).exists()
            else:
                session_key = request.session.session_key
                if session_key:
                    is_favorited = ProductFavorite.objects.filter(product=product_detail, session_key=session_key).exists()
            like_count = ProductFavorite.objects.filter(product=product_detail).count()
    except:
        pass

    context = {
        'product_detail': product_detail,
        'product_variations': product_variations,
        'product_image': product_image,
        'product_images': product_images,  # Toutes les images pour la popup
        'related_products': related_products,
        'supplier_Products': supplier_Products,
        'product_feedback': product_feedback,
        'average_rating': average_rating,
        'feedbak_number': feedbak_number,
        "start_1": start_1,
        "start_2": start_2,
        "start_3": start_3,
        "start_4": start_4,
        "start_5": start_5,
        'is_favorited': is_favorited,
        'like_count': like_count,
    }
    return render(request, 'products/shop-product-vendor.html', context)


def product_search(request):
    context = {}
    if not request.session.has_key('currency'):
        request.session['currency'] = settings.DEFAULT_CURRENCY

    # Récupérer les catégories pour le filtre
    supercategory = SuperCategory.objects.all().order_by('name')
    
    # Préparer les données des produits avec like_count et images
    import json
    products_data = []
    qs = None
    page_obj = None
    
    if request.method == 'POST':
        try:
            word = request.POST['search-product']
        except:
            word = ""
        request.session["search_product"] = word

        try:
            category_select = request.POST['category-select']
        except:
            category_select = "All Categories"
        request.session["search_category_select"] = category_select

        if category_select == "All Categories":
            try:
                queryset = Product.objects.filter(
                    product_name__icontains=word, PRDISDeleted=False, PRDISactive=True).annotate(
                    like_count=Count('favorites')
                ).order_by('-date').distinct()
            except:
                queryset = Product.objects.filter(
                    product_name__icontains=word, PRDISDeleted=False, PRDISactive=True).order_by('-date').distinct()
        else:
            try:
                queryset = Product.objects.filter(
                    product_name__icontains=word, PRDISDeleted=False, PRDISactive=True, 
                    product_supercategory__name=category_select).annotate(
                    like_count=Count('favorites')
                ).order_by('-date').distinct()
            except:
                queryset = Product.objects.filter(
                    product_name__icontains=word, PRDISDeleted=False, PRDISactive=True, 
                    product_supercategory__name=category_select).order_by('-date').distinct()
        
        request.session["products_count"] = queryset.count()
        paginator = Paginator(queryset, 12)
        page = request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
            
    elif "search_product" in request.session.keys():
        word = request.session.get("search_product", "")
        category_select = request.session.get("search_category_select", "All Categories")
        
        if category_select == "All Categories":
            try:
                queryset = Product.objects.filter(
                    product_name__icontains=word, PRDISDeleted=False, PRDISactive=True).annotate(
                    like_count=Count('favorites')
                ).order_by('-date').distinct()
            except:
                queryset = Product.objects.filter(
                    product_name__icontains=word, PRDISDeleted=False, PRDISactive=True).order_by('-date').distinct()
        else:
            try:
                queryset = Product.objects.filter(
                    product_name__icontains=word, PRDISDeleted=False, PRDISactive=True, 
                    product_supercategory__name=category_select).annotate(
                    like_count=Count('favorites')
                ).order_by('-date').distinct()
            except:
                queryset = Product.objects.filter(
                    product_name__icontains=word, PRDISDeleted=False, PRDISactive=True, 
                    product_supercategory__name=category_select).order_by('-date').distinct()
        
        paginator = Paginator(queryset, 12)
        page = request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
    
    # Préparer les données des produits avec images multiples
    if page_obj:
        for product in page_obj:
            # Collecter toutes les images
            product_images = []
            if product.product_image:
                img_path = str(product.product_image)
                if not img_path.startswith('/media/'):
                    img_path = '/media/' + img_path
                product_images.append(img_path)
            if product.additional_image_1:
                img_path = str(product.additional_image_1)
                if not img_path.startswith('/media/'):
                    img_path = '/media/' + img_path
                product_images.append(img_path)
            if product.additional_image_2:
                img_path = str(product.additional_image_2)
                if not img_path.startswith('/media/'):
                    img_path = '/media/' + img_path
                product_images.append(img_path)
            if product.additional_image_3:
                img_path = str(product.additional_image_3)
                if not img_path.startswith('/media/'):
                    img_path = '/media/' + img_path
                product_images.append(img_path)
            if product.additional_image_4:
                img_path = str(product.additional_image_4)
                if not img_path.startswith('/media/'):
                    img_path = '/media/' + img_path
                product_images.append(img_path)
            
            # Récupérer le like_count de manière sécurisée
            like_count = 0
            try:
                like_count = getattr(product, 'like_count', 0)
                if like_count is None:
                    like_count = 0
            except:
                try:
                    from .models import ProductFavorite
                    like_count = ProductFavorite.objects.filter(product=product).count()
                except:
                    like_count = 0
            
            products_data.append({
                'product': product,
                'product_images': json.dumps(product_images),
                'like_count': like_count,
            })

    # Calculer le total de produits pour l'affichage
    total_products = 0
    if page_obj:
        total_products = page_obj.paginator.count
    
    # Récupérer la requête de recherche pour l'affichage
    search_query = ""
    if request.method == 'POST':
        try:
            search_query = request.POST.get('search-product', '').strip()
        except:
            search_query = ""
    elif "search_product" in request.session.keys():
        search_query = request.session.get("search_product", "")
    
    context = {
        'supercategory': supercategory,
        'products_data': products_data,
        'page_obj': page_obj,
        'total_products': total_products,
        'search_query': search_query,
        'qs': page_obj,  # Pour compatibilité avec l'ancien template
    }

    return render(request, 'products/product-search.html', context)


def product_rating(request):
    if request.method == "POST" and request.user.is_authenticated and not request.user.is_anonymous:
        product_id = request.POST.get("product_id")
        product_rate = request.POST.get("product_rate")
        # print(type(product_rate))
        message = request.POST.get("client_message")
        client = Profile.objects.get(user=request.user)
        if request.is_ajax():
            product = Product.objects.get(id=product_id)

            if ProductRating.objects.all().filter(PRDIProduct=product, client_name__user=request.user).exists():
                old_rating = ProductRating.objects.get(
                    PRDIProduct=product, client_name__user=request.user)
                old_rating.vendor = product.product_vendor
                # old_rating.rate = product_rate
                old_rating.client_name = client
                old_rating.client_comment = message
                old_rating.save()

                product_feedback = ProductRating.objects.all().filter(
                    PRDIProduct=product, active=True)
                feedback_sum = ProductRating.objects.all().filter(
                    PRDIProduct=product, active=True).aggregate(Sum('rate'))
                feedbak_number = product_feedback.count()
                try:
                    if feedback_sum != None or feedback_sum != 0:
                        average_rating = round(
                            (int(feedback_sum["rate__sum"]) / feedbak_number) * 20)
                        product.feedbak_average = average_rating
                        product.feedbak_number = feedbak_number
                        product.save()

                except:
                    pass

                # send_mail(
                #     "You received a message from {}".format(name),
                #     f'{message}',
                #     f'{settings.EMAIL_SENDGRID}',
                #     [f'{email}'],
                #     fail_silently=False,
                # )
            else:
                ProductRating.objects.create(
                    PRDIProduct=product,
                    vendor=product.product_vendor,
                    rate=product_rate,
                    client_name=client,

                    client_comment=message,
                )

                product_feedback = ProductRating.objects.all().filter(
                    PRDIProduct=product, active=True)
                feedback_sum = ProductRating.objects.all().filter(
                    PRDIProduct=product, active=True).aggregate(Sum('rate'))
                feedbak_number = product_feedback.count()
                try:
                    if feedback_sum != None or feedback_sum != 0:
                        average_rating = round(
                            (int(feedback_sum["rate__sum"]) / feedbak_number * 20))
                        product.feedbak_average = average_rating
                        product.feedbak_number = feedbak_number
                        product.save()

                except:
                    product.feedbak_average = int(product_rate) * 20
                    product.feedbak_number = 1
                    product.save()
                # send_mail(
                #     "You received a message from {}".format(name),
                #     f'{message}',
                #     f'{settings.EMAIL_SENDGRID}',
                #     [f'{email}'],
                #     fail_silently=False,
                # )
            return JsonResponse({"succes": True, "product_id": product_id, "product_rate": product_rate, }, safe=False)
        return JsonResponse({"succes": False, }, safe=False)


@require_POST
def toggle_favorite(request):
    """Toggle favorite/like pour un produit"""
    if request.method == 'POST':
        try:
            # Vérifier si la table existe
            from django.db import connection
            table_name = ProductFavorite._meta.db_table
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                return JsonResponse({
                    'success': False,
                    'error': 'La fonctionnalité de favoris n\'est pas encore disponible. Veuillez exécuter les migrations.',
                    'like_count': 0
                }, status=503)
            
            product_id = request.POST.get('product_id')
            
            # Vérifier si c'est un article entre particuliers
            is_peer_to_peer = str(product_id).startswith('peer_')
            
            if is_peer_to_peer:
                # Gérer les favoris pour les articles entre particuliers
                from accounts.models import PeerToPeerProduct, PeerToPeerProductFavorite
                try:
                    # Gérer le cas où product_id pourrait déjà avoir "peer_" ou être juste un ID
                    # Enlever tous les préfixes "peer_" possibles (gérer les cas "peer_1", "peer_peer_1", etc.)
                    peer_id_str = str(product_id)
                    while peer_id_str.startswith('peer_'):
                        peer_id_str = peer_id_str.replace('peer_', '', 1)
                    peer_id = int(peer_id_str)
                    peer_product = get_object_or_404(PeerToPeerProduct, id=peer_id, status=PeerToPeerProduct.APPROVED)
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': 'ID d\'article entre particuliers invalide.',
                        'like_count': 0
                    }, status=400)
                
                if request.user.is_authenticated:
                    favorite, created = PeerToPeerProductFavorite.objects.get_or_create(
                        product=peer_product,
                        user=request.user
                    )
                    if not created:
                        favorite.delete()
                        is_favorited = False
                    else:
                        is_favorited = True
                else:
                    # Pour les utilisateurs non authentifiés, utiliser la session
                    session_key = request.session.session_key
                    if not session_key:
                        request.session.create()
                        session_key = request.session.session_key
                    
                    favorite, created = PeerToPeerProductFavorite.objects.get_or_create(
                        product=peer_product,
                        session_key=session_key
                    )
                    if not created:
                        favorite.delete()
                        is_favorited = False
                    else:
                        is_favorited = True
                
                # Compter le nombre total de likes
                like_count = PeerToPeerProductFavorite.objects.filter(product=peer_product).count()
                
                # Compter le nombre total de favoris de l'utilisateur/session (produits normaux + entre particuliers)
                if request.user.is_authenticated:
                    wishlist_count = ProductFavorite.objects.filter(user=request.user).count() + \
                                   PeerToPeerProductFavorite.objects.filter(user=request.user).count()
                else:
                    session_key = request.session.session_key
                    if session_key:
                        wishlist_count = ProductFavorite.objects.filter(session_key=session_key).count() + \
                                       PeerToPeerProductFavorite.objects.filter(session_key=session_key).count()
                    else:
                        wishlist_count = 0
            else:
                # Produit normal
                try:
                    product_id_int = int(product_id)
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': 'ID de produit invalide.',
                        'like_count': 0
                    }, status=400)
                
                product = get_object_or_404(Product, id=product_id_int)
                
                if request.user.is_authenticated:
                    favorite, created = ProductFavorite.objects.get_or_create(
                        product=product,
                        user=request.user
                    )
                    if not created:
                        favorite.delete()
                        is_favorited = False
                    else:
                        is_favorited = True
                else:
                    # Pour les utilisateurs non authentifiés, utiliser la session
                    session_key = request.session.session_key
                    if not session_key:
                        request.session.create()
                        session_key = request.session.session_key
                    
                    favorite, created = ProductFavorite.objects.get_or_create(
                        product=product,
                        session_key=session_key
                    )
                    if not created:
                        favorite.delete()
                        is_favorited = False
                    else:
                        is_favorited = True
                
                # Compter le nombre total de likes
                like_count = ProductFavorite.objects.filter(product=product).count()
                
                # Compter le nombre total de favoris de l'utilisateur/session (produits normaux + entre particuliers)
                if request.user.is_authenticated:
                    from accounts.models import PeerToPeerProductFavorite
                    wishlist_count = ProductFavorite.objects.filter(user=request.user).count() + \
                                   PeerToPeerProductFavorite.objects.filter(user=request.user).count()
                else:
                    session_key = request.session.session_key
                    if session_key:
                        from accounts.models import PeerToPeerProductFavorite
                        wishlist_count = ProductFavorite.objects.filter(session_key=session_key).count() + \
                                       PeerToPeerProductFavorite.objects.filter(session_key=session_key).count()
                    else:
                        wishlist_count = 0
            
            return JsonResponse({
                'success': True,
                'is_favorited': is_favorited,
                'like_count': like_count,
                'wishlist_count': wishlist_count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'like_count': 0
            }, status=400)
    
    return JsonResponse({'success': False}, status=405)


@require_http_methods(["GET"])
def get_wishlist_count(request):
    """Vue AJAX pour obtenir le nombre d'articles dans la liste à souhaits (produits normaux + articles entre particuliers)"""
    try:
        from django.db import connection
        from accounts.models import PeerToPeerProductFavorite
        
        table_name = ProductFavorite._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            return JsonResponse({'wishlist_count': 0})
        
        if request.user.is_authenticated:
            wishlist_count = ProductFavorite.objects.filter(user=request.user).count() + \
                           PeerToPeerProductFavorite.objects.filter(user=request.user).count()
        else:
            session_key = request.session.session_key
            if session_key:
                wishlist_count = ProductFavorite.objects.filter(session_key=session_key).count() + \
                               PeerToPeerProductFavorite.objects.filter(session_key=session_key).count()
            else:
                wishlist_count = 0
        
        return JsonResponse({'wishlist_count': wishlist_count})
    except Exception as e:
        return JsonResponse({'wishlist_count': 0, 'error': str(e)}, status=500)


def wishlist(request):
    """Afficher la liste à souhaits de l'utilisateur (produits normaux + articles d'occasion)"""
    try:
        from django.db import connection
        from accounts.models import PeerToPeerProductFavorite
        
        # Vérifier si les tables existent
        product_fav_table_name = ProductFavorite._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{product_fav_table_name}'")
            product_fav_table_exists = cursor.fetchone() is not None
        
        peer_fav_table_name = PeerToPeerProductFavorite._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{peer_fav_table_name}'")
            peer_fav_table_exists = cursor.fetchone() is not None
        
        favorites = []
        if request.user.is_authenticated:
            if product_fav_table_exists:
                product_favorites = ProductFavorite.objects.filter(user=request.user).select_related('product')
                # Ajouter un attribut pour distinguer les types
                for fav in product_favorites:
                    fav.is_peer_to_peer = False
                favorites.extend(product_favorites)
            if peer_fav_table_exists:
                peer_favorites = PeerToPeerProductFavorite.objects.filter(user=request.user).select_related('product')
                # Ajouter un attribut pour distinguer les types
                for fav in peer_favorites:
                    fav.is_peer_to_peer = True
                favorites.extend(peer_favorites)
        else:
            session_key = request.session.session_key
            if session_key:
                if product_fav_table_exists:
                    product_favorites = ProductFavorite.objects.filter(session_key=session_key).select_related('product')
                    # Ajouter un attribut pour distinguer les types
                    for fav in product_favorites:
                        fav.is_peer_to_peer = False
                    favorites.extend(product_favorites)
                if peer_fav_table_exists:
                    peer_favorites = PeerToPeerProductFavorite.objects.filter(session_key=session_key).select_related('product')
                    # Ajouter un attribut pour distinguer les types
                    for fav in peer_favorites:
                        fav.is_peer_to_peer = True
                    favorites.extend(peer_favorites)
        
        # Trier par date (plus récent en premier)
        favorites.sort(key=lambda x: x.date if hasattr(x, 'date') and x.date else None, reverse=True)
        
        favorites_count = len(favorites)
        
        context = {
            'favorites': favorites,
            'favorites_count': favorites_count,
        }
        return render(request, 'products/wishlist.html', context)
    except Exception as e:
        context = {
            'favorites': [],
            'favorites_count': 0,
            'error': str(e)
        }
        return render(request, 'products/wishlist.html', context)
