import imp
from django.shortcuts import render
from categories.models import SuperCategory, MainCategory
from .models import (Carousel, HomeAdSidebar, HomeAdMiddlebar,
                     HomeAdSupplier, HomeAdDaily, HomeAdDealTime)
from products.models import Product
from django.http import HttpResponseRedirect
from django.conf import settings
from settings.models import HomePageTheme
import random
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
    products = Product.objects.all().filter(PRDISactive=True).order_by("?")
    home_ad_suppliers = HomeAdSupplier.objects.all().order_by("?")
    home_ad_daily = HomeAdDaily.objects.all().order_by("?")
    home_ads_deal_time = HomeAdDealTime.objects.all().order_by("?")
    index = str(HomePageTheme.objects.all().filter(active=True).first())
    context = {
        "super_category": super_category,
        "carousels": carousels,
        "home_ads_left": home_ads_left,
        "home_ads_right": home_ads_right,
        "main_category": main_category,
        "home_ad_middlebar": home_ad_middlebar,
        "products": products,
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
