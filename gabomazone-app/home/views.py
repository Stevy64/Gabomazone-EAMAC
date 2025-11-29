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
    
    # Récupérer les produits les plus populaires (par nombre de favoris)
    try:
        popular_products_queryset = Product.objects.filter(
            PRDISactive=True, 
            PRDISDeleted=False
        ).annotate(
            like_count=Count('favorites')
        ).order_by('-like_count', '-date')[:12]
    except:
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
        
        popular_products_data.append({
            'product': product,
            'product_images': json.dumps(product_images),
            'like_count': like_count,
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
