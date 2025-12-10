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
    
    # Récupérer les produits les plus populaires (priorisant les boostés, puis par vues et commandes)
    from django.db.models import Q, F, Case, When, IntegerField
    from django.utils import timezone
    from orders.models import OrderDetails
    
    try:
        # Récupérer les IDs des produits boostés actifs
        from accounts.models import ProductBoostRequest
        now = timezone.now()
        active_boosted_product_ids = list(
            ProductBoostRequest.objects.filter(
                status=ProductBoostRequest.ACTIVE,
                start_date__lte=now,
                end_date__gte=now,
                payment_status=True
            ).values_list('product_id', flat=True)
        )
        
        # Annoter avec le nombre de commandes (via OrderDetails)
        # Filtrer les OrderDetails avec des commandes terminées
        from django.db.models import Coalesce, Value
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
        
        # Calculer le score de popularité après annotation
        # Score = vues + (commandes * 10) pour donner plus de poids aux commandes
        popular_products_queryset = popular_products_queryset.annotate(
            popularity_score=F('view_count_safe') + (F('order_count') * 10)
        ).order_by(
            '-is_boosted',  # Prioriser les produits boostés
            '-popularity_score',  # Puis par score de popularité
            '-view_count_safe',  # Puis par nombre de vues
            '-order_count',  # Puis par nombre de commandes
            '-date'  # Enfin par date
        )[:12]
    except Exception as e:
        # Fallback en cas d'erreur
        import traceback
        print(f"Erreur dans la récupération des produits populaires: {e}")
        print(traceback.format_exc())
        popular_products_queryset = Product.objects.filter(
            PRDISactive=True, 
            PRDISDeleted=False
        ).order_by('-date')[:12]
    
    # Récupérer les nouveaux produits (par date)
    new_products_queryset = Product.objects.filter(
        PRDISactive=True, 
        PRDISDeleted=False
    ).order_by('-date')[:12]
    
    # Préparer les données des produits populaires avec images multiples
    popular_products_data = []
    for product in popular_products_queryset:
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
            like_count = getattr(product, 'like_count', 0)
            if like_count is None:
                like_count = 0
        except:
            try:
                from products.models import ProductFavorite
                like_count = ProductFavorite.objects.filter(product=product).count()
            except:
                like_count = 0
        
        # Récupérer les statistiques du produit
        order_count = getattr(product, 'order_count', 0) or 0
        view_count = getattr(product, 'view_count', 0) or 0
        is_boosted = getattr(product, 'is_boosted', 0) == 1
        
        popular_products_data.append({
            'product': product,
            'product_images': json.dumps(product_images),
            'like_count': like_count,
            'order_count': order_count,
            'view_count': view_count,
            'is_boosted': is_boosted,
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
        
        new_products_data.append({
            'product': product,
            'product_images': json.dumps(product_images),
            'like_count': like_count,
        })
    
    context = {
        "super_category": super_category,
        "carousels": carousels,
        "home_ads_left": home_ads_left,
        "home_ads_right": home_ads_right,
        "main_category": main_category,
        "home_ad_middlebar": home_ad_middlebar,
        "popular_products_data": popular_products_data,
        "new_products_data": new_products_data,
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
