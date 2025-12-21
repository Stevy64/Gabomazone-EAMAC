# from msilib.schema import Class
from django import views
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from accounts.models import Profile ,SocialLink
from django.views.generic import View
from products.models import Product 
# Create your views here.


def supplier_list(request):
    return render(request, "suppliers/vendors-grid.html")


class VendorsJsonListView(View):
    def get(self, *args, **kwargs):

        upper = int(self.request.GET.get("num_vendors", 12))
        lower = upper - 12
        # Filtrer uniquement les vendors approuvés (admission=True)
        vendors_queryset = Profile.objects.filter(status="vendor", admission=True).order_by("-date")
        vendors = list(vendors_queryset.values()[lower:upper])
        vendors_size = vendors_queryset.count()
        max_size = True if upper >= vendors_size else False
        return JsonResponse({"data": vendors, "max": max_size, "vendors_size": vendors_size}, safe=False)


def vendor_details(request, slug):
    from home.models import HomeAdDealTime, VendorDetailsAdImage, ShopAdSidebar
    from django.db.models import Count
    
    vendor_detail = Profile.objects.filter(slug=slug, status="vendor", admission=True).first()
    
    if not vendor_detail:
        from django.http import Http404
        raise Http404("Vendeur introuvable")
    
    # Récupérer les liens sociaux (optionnel, peut ne pas exister)
    vendor_social_links = None
    try:
        from accounts.models import SocialLink
        vendor_social_links = SocialLink.objects.filter(vendor_profile=vendor_detail).first()
    except:
        pass
    
    # Vérifier si le vendeur a un abonnement premium actif
    is_premium = False
    try:
        from accounts.models import PremiumSubscription
        premium_sub = PremiumSubscription.objects.filter(vendor=vendor_detail).first()
        if premium_sub and premium_sub.is_active():
            is_premium = True
    except:
        pass
    
    # Récupérer les produits du vendeur
    vendor_products = Product.objects.filter(
        product_vendor=vendor_detail,
        PRDISDeleted=False,
        PRDISactive=True
    ).order_by('-date')[:8]
    
    # Calculer la note moyenne du vendeur basée sur les ratings de ses produits
    from products.models import ProductRating
    from django.db.models import Avg, Count
    vendor_ratings = ProductRating.objects.filter(
        vendor=vendor_detail,
        active=True
    )
    vendor_rating_stats = vendor_ratings.aggregate(
        average_rating=Avg('rate'),
        total_ratings=Count('id')
    )
    average_rating = vendor_rating_stats['average_rating'] or 0
    total_ratings = vendor_rating_stats['total_ratings'] or 0
    
    # Récupérer les nouveaux produits (pour la sidebar)
    new_products = Product.objects.filter(
        PRDISDeleted=False,
        PRDISactive=True
    ).order_by('-date')[:5]
    
    # Récupérer les publicités
    try:
        home_ads_deal_time_obj = HomeAdDealTime.objects.filter(supplier=vendor_detail).order_by("?")[:4]
    except:
        home_ads_deal_time_obj = []
    
    try:
        vendor_page_ad_image = VendorDetailsAdImage.objects.all().order_by("?")[:1]
    except:
        vendor_page_ad_image = []
    
    try:
        shop_page_ad = ShopAdSidebar.objects.filter(supplier=vendor_detail).order_by("?")[:1]
    except:
        shop_page_ad = []
    
    context = {
        "vendor_detail": vendor_detail,
        "vendor_social_links": vendor_social_links,
        "vendor_products": vendor_products,
        "new_products": new_products,
        "home_ads_deal_time_obj": home_ads_deal_time_obj,
        "vendor_page_ad_image": vendor_page_ad_image,
        "shop_page_ad": shop_page_ad,
        "is_premium": is_premium,
        "average_rating": round(average_rating, 1) if average_rating else 0,
        "total_ratings": total_ratings,
    }
    return render(request, 'suppliers/vendor-details.html', context)


class VendorDetailsJsonListView(View):
    def get(self, *args, **kwargs):

        upper = int(self.request.GET.get("num_products"))
        order_by = self.request.GET.get("order_by")
        product_vendor = int(self.request.GET.get("vendor_slug"))
        lower = upper - 10
        products = list(Product.objects.all(
        ).filter(product_vendor=product_vendor , PRDISDeleted = False , PRDISactive = True).values(
            'id', 'product_name', 'PRDPrice', 'PRDDiscountPrice', 'product_image', 'PRDSlug', 'view_count'
        ).order_by(order_by)[lower:upper])
        products_size = len(
            Product.objects.all().filter(product_vendor=product_vendor ,PRDISDeleted = False , PRDISactive = True))

        max_size = True if upper >= products_size else False
        return JsonResponse({"data": products,  "max": max_size, "products_size": products_size, }, safe=False)
