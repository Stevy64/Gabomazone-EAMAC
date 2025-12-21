import imp
from django.shortcuts import render
from categories.models import SuperCategory, MainCategory
from .models import (Carousel, HomeAdSidebar, HomeAdMiddlebar,
                     HomeAdSupplier, HomeAdDaily, HomeAdDealTime)
from products.models import Product
from django.http import HttpResponseRedirect
from django.conf import settings
from settings.models import HomePageTheme
from django.db.models import Count
import random
import json
# Create your views here.


def home_page(request):
    if not request.session.has_key('currency'):
        request.session['currency'] = settings.DEFAULT_CURRENCY
    super_category = SuperCategory.objects.all().order_by("?")
    carousels = Carousel.objects.all()
    home_ads_left = HomeAdSidebar.objects.all().filter(
        image_position="Left")[0:1]
    home_ads_right = HomeAdSidebar.objects.all().filter(
        image_position="Right")[0:1]
    home_ad_middlebar = HomeAdMiddlebar.objects.all().order_by("?")
    main_category = MainCategory.objects.all().order_by("?")
    home_ad_suppliers = HomeAdSupplier.objects.all().order_by("?")
    home_ad_daily = HomeAdDaily.objects.all().order_by("?")
    home_ads_deal_time = HomeAdDealTime.objects.all().order_by("?")
    index = str(HomePageTheme.objects.all().filter(active=True).first())
    
    # Récupérer les produits les plus populaires (priorisant les boostés, puis par vues)
    from django.db.models import Q, F, Case, When, IntegerField
    from django.utils import timezone
    from orders.models import OrderDetails
    
    try:
        # S'assurer que Product est importé
        from products.models import Product
        from accounts.models import PeerToPeerProduct
        
        now = timezone.now()
        
        # Récupérer les IDs des produits normaux boostés actifs
        from accounts.models import ProductBoostRequest
        active_boosted_product_ids = list(
            ProductBoostRequest.objects.filter(
                status=ProductBoostRequest.ACTIVE,
                start_date__lte=now,
                end_date__gte=now,
                payment_status=True
            ).values_list('product_id', flat=True)
        )
        
        # Récupérer les IDs des produits C2C boostés actifs
        from c2c.models import ProductBoost
        active_boosted_c2c_boosts = ProductBoost.objects.filter(
            status=ProductBoost.ACTIVE,
            start_date__lte=now,
            end_date__gte=now
        )
        active_boosted_c2c_product_ids = list(active_boosted_c2c_boosts.values_list('product_id', flat=True))
        
        # Debug: afficher les produits C2C boostés trouvés
        if active_boosted_c2c_product_ids:
            print(f"DEBUG: Produits C2C boostés trouvés: {active_boosted_c2c_product_ids}")
        
        # Annoter avec le nombre de commandes (via OrderDetails)
        # Filtrer les OrderDetails avec des commandes terminées
        from django.db.models import Value
        from django.db.models.functions import Coalesce
        popular_products_queryset = Product.objects.filter(
            PRDISactive=True, 
            PRDISDeleted=False
        ).annotate(
            like_count=Count('favorites', distinct=True),
            # Compter les commandes terminées via OrderDetails
            order_count=Count(
                'orderdetails',
                filter=Q(orderdetails__order__is_finished=True),
                distinct=True
            ),
            # Flag pour indiquer si le produit est boosté
            is_boosted=Case(
                When(id__in=active_boosted_product_ids if active_boosted_product_ids else [], then=1),
                default=0,
                output_field=IntegerField()
            ),
            # Gérer les valeurs None pour view_count
            view_count_safe=Coalesce('view_count', Value(0))
        )
        
        # Filtrer uniquement les produits boostés OU ceux ayant des vues > 0
        # Puis ordonner : d'abord les boostés, puis par nombre de vues décroissant
        popular_products_queryset = popular_products_queryset.filter(
            Q(is_boosted=1) | Q(view_count_safe__gt=0)
        ).order_by(
            '-is_boosted',  # Prioriser les produits boostés
            '-view_count_safe',  # Puis par nombre de vues décroissant
            '-date'  # Enfin par date
        )[:12]
        
        # Récupérer les produits C2C boostés ou avec des vues
        # Note: PeerToPeerProduct utilise 'favorites' comme related_name, pas 'peer_to_peer_product_favorites'
        popular_c2c_products_queryset = PeerToPeerProduct.objects.filter(
            status=PeerToPeerProduct.APPROVED
        ).annotate(
            like_count=Count('favorites', distinct=True),
            # Flag pour indiquer si le produit est boosté
            is_boosted=Case(
                When(id__in=active_boosted_c2c_product_ids if active_boosted_c2c_product_ids else [], then=1),
                default=0,
                output_field=IntegerField()
            ),
            # Gérer les valeurs None pour view_count
            view_count_safe=Coalesce('view_count', Value(0))
        ).filter(
            Q(is_boosted=1) | Q(view_count_safe__gt=0)
        )
        
        # Combiner les deux querysets et créer une liste unifiée
        all_popular_products = []
        
        # Ajouter les produits normaux
        for product in popular_products_queryset:
            is_boosted = getattr(product, 'is_boosted', 0)
            view_count = getattr(product, 'view_count_safe', 0) or 0
            all_popular_products.append({
                'product': product,
                'is_peer_to_peer': False,
                'is_boosted': int(is_boosted == 1),  # Convertir en int pour le tri
                'view_count': int(view_count),
            })
        
        # Ajouter les produits C2C
        for product in popular_c2c_products_queryset:
            is_boosted = getattr(product, 'is_boosted', 0)
            view_count = getattr(product, 'view_count_safe', 0) or getattr(product, 'view_count', 0) or 0
            all_popular_products.append({
                'product': product,
                'is_peer_to_peer': True,
                'is_boosted': int(is_boosted == 1),  # Convertir en int pour le tri
                'view_count': int(view_count),
            })
        
        # Trier la liste combinée : d'abord les boostés (1), puis par nombre de vues décroissant
        all_popular_products.sort(key=lambda x: (-x['is_boosted'], -x['view_count']))
        
        # Debug: afficher les produits triés
        print(f"DEBUG: Nombre total de produits populaires: {len(all_popular_products)}")
        for i, item in enumerate(all_popular_products[:5]):
            print(f"  {i+1}. {item['product'].product_name} - Boosté: {item['is_boosted']}, Vues: {item['view_count']}, C2C: {item['is_peer_to_peer']}")
        
        # Limiter à 12 produits
        all_popular_products = all_popular_products[:12]
    except Exception as e:
        # Fallback en cas d'erreur
        import traceback
        print(f"Erreur dans la récupération des produits populaires: {e}")
        print(traceback.format_exc())
        all_popular_products = []
        try:
            from products.models import Product
            fallback_products = Product.objects.filter(
                PRDISactive=True, 
                PRDISDeleted=False
            ).order_by('-date')[:12]
            for product in fallback_products:
                all_popular_products.append({
                    'product': product,
                    'is_peer_to_peer': False,
                    'is_boosted': False,
                    'view_count': getattr(product, 'view_count', 0) or 0,
                })
        except:
            pass
    
    # Récupérer les nouveaux produits (par date)
    new_products_queryset = Product.objects.filter(
        PRDISactive=True, 
        PRDISDeleted=False
    ).order_by('-date')[:12]
    
    # Préparer les données des produits populaires avec images multiples
    popular_products_data = []
    for item in all_popular_products:
        product = item['product']
        is_peer_to_peer = item['is_peer_to_peer']
        is_boosted = item['is_boosted']
        view_count = item['view_count']
        
        product_images = []
        if is_peer_to_peer:
            # Produit C2C
            if product.product_image:
                img_path = str(product.product_image)
                if not img_path.startswith('/media/'):
                    img_path = '/media/' + img_path
                product_images.append(img_path)
            # Les produits C2C n'ont généralement qu'une seule image
        else:
            # Produit normal
            if product.product_image:
                img_path = str(product.product_image)
                if not img_path.startswith('/media/'):
                    img_path = '/media/' + img_path
                product_images.append(img_path)
            if hasattr(product, 'additional_image_1') and product.additional_image_1:
                img_path = str(product.additional_image_1)
                if not img_path.startswith('/media/'):
                    img_path = '/media/' + img_path
                product_images.append(img_path)
            if hasattr(product, 'additional_image_2') and product.additional_image_2:
                img_path = str(product.additional_image_2)
                if not img_path.startswith('/media/'):
                    img_path = '/media/' + img_path
                product_images.append(img_path)
            if hasattr(product, 'additional_image_3') and product.additional_image_3:
                img_path = str(product.additional_image_3)
                if not img_path.startswith('/media/'):
                    img_path = '/media/' + img_path
                product_images.append(img_path)
            if hasattr(product, 'additional_image_4') and product.additional_image_4:
                img_path = str(product.additional_image_4)
                if not img_path.startswith('/media/'):
                    img_path = '/media/' + img_path
                product_images.append(img_path)
        
        like_count = 0
        try:
            if is_peer_to_peer:
                # Pour les produits C2C, utiliser le related_name 'favorites'
                like_count = getattr(product, 'like_count', 0)
                if like_count is None or like_count == 0:
                    from accounts.models import PeerToPeerProductFavorite
                    like_count = PeerToPeerProductFavorite.objects.filter(product=product).count()
            else:
                like_count = getattr(product, 'like_count', 0)
                if like_count is None:
                    like_count = 0
                if like_count == 0:
                    from products.models import ProductFavorite
                    like_count = ProductFavorite.objects.filter(product=product).count()
        except:
            like_count = 0
        
        # Récupérer les statistiques du produit
        order_count = 0
        if not is_peer_to_peer:
            order_count = getattr(product, 'order_count', 0) or 0
        
        popular_products_data.append({
            'product': product,
            'product_images': json.dumps(product_images),
            'like_count': like_count,
            'order_count': order_count,
            'view_count': view_count,
            'is_boosted': bool(is_boosted),  # Convertir en bool pour le template
            'is_peer_to_peer': is_peer_to_peer,
        })
    
    # Préparer les données des nouveaux produits avec images multiples
    new_products_data = []
    for product in new_products_queryset:
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
        
        like_count = 0
        try:
            from products.models import ProductFavorite
            like_count = ProductFavorite.objects.filter(product=product).count()
        except:
            like_count = 0
        
        # Récupérer les statistiques du produit
        view_count = getattr(product, 'view_count', 0) or 0
        
        # Vérifier si c'est un produit peer-to-peer
        is_peer_to_peer = False
        try:
            from accounts.models import PeerToPeerProduct
            is_peer_to_peer = PeerToPeerProduct.objects.filter(id=product.id).exists()
        except:
            pass
        
        new_products_data.append({
            'product': product,
            'product_images': json.dumps(product_images),
            'like_count': like_count,
            'view_count': view_count,
            'is_peer_to_peer': is_peer_to_peer,
        })
    
    # Récupérer les meilleurs magasins (priorisant Premium, puis par nombre d'articles vus)
    from accounts.models import Profile, PremiumSubscription
    from django.db.models import Sum, Q
    from django.utils import timezone
    
    try:
        now = timezone.now()
        
        # Récupérer les magasins avec abonnement Premium actif
        premium_vendors = Profile.objects.filter(
            status="vendor",
            admission=True,
            premium_subscription__status=PremiumSubscription.ACTIVE,
            premium_subscription__end_date__gt=now
        ).distinct()
        
        # Récupérer tous les magasins approuvés
        all_vendors = Profile.objects.filter(
            status="vendor",
            admission=True
        )
        
        # Annoter avec le total des vues de leurs produits
        vendors_with_views = all_vendors.annotate(
            total_views=Sum('product__view_count', filter=Q(product__PRDISDeleted=False, product__PRDISactive=True))
        )
        
        # Créer une liste de magasins avec leurs données
        vendors_list = []
        for vendor in vendors_with_views:
            # Vérifier si le magasin a un abonnement Premium actif
            is_premium = False
            try:
                premium_sub = PremiumSubscription.objects.filter(
                    vendor=vendor,
                    status=PremiumSubscription.ACTIVE,
                    end_date__gt=now
                ).first()
                if premium_sub and premium_sub.is_active():
                    is_premium = True
            except:
                pass
            
            total_views = vendor.total_views or 0
            
            vendors_list.append({
                'vendor': vendor,
                'is_premium': is_premium,
                'total_views': int(total_views),
            })
        
        # Trier : d'abord les Premium (is_premium=True), puis par total_views décroissant
        vendors_list.sort(key=lambda x: (-x['is_premium'], -x['total_views']))
        
        # Limiter à 12 magasins
        top_vendors_data = vendors_list[:12]
        
    except Exception as e:
        import traceback
        print(f"Erreur dans la récupération des meilleurs magasins: {e}")
        print(traceback.format_exc())
        top_vendors_data = []
    
    context = {
        "super_category": super_category,
        "carousels": carousels,
        "home_ads_left": home_ads_left,
        "home_ads_right": home_ads_right,
        "main_category": main_category,
        "home_ad_middlebar": home_ad_middlebar,
        "popular_products_data": popular_products_data,
        "new_products_data": new_products_data,
        "top_vendors_data": top_vendors_data,
        "home_ad_suppliers": home_ad_suppliers,
        "home_ad_daily": home_ad_daily,
        "home_ads_deal_time": home_ads_deal_time,
    }
    # FORCER LE NOUVEAU DESIGN FLAVORIZ - TOUJOURS
    return render(request, 'home/index-flavoriz.html', context)


def set_currency(request):
    lasturl = request.META.get("HTTP_REFERER")
    if request.method == "POST":
        request.session["currency"] = request.POST["currency"]
        print(request.POST["currency"])

    return HttpResponseRedirect(lasturl)
