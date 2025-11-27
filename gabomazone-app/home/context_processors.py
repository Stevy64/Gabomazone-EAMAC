
from .models import (HeadTextAd, HomeAdDealTime, VendorDetailsAdImage,
                     ShopAdSidebar, HotDealAd)


def DealTime_obj(request):
    home_ads_deal_time_obj = HomeAdDealTime.objects.all().order_by("?")
    return {
        'home_ads_deal_time_obj': home_ads_deal_time_obj,
    }


def vendor_details_ad_image(request):
    vendor_page_ad_image = VendorDetailsAdImage.objects.all().order_by("?")
    return{
        'vendor_page_ad_image': vendor_page_ad_image,
    }


def shop_ad_sidebar(request):
    shop_page_ad = ShopAdSidebar.objects.all().order_by("?")
    return {
        "shop_page_ad": shop_page_ad,
    }


def hot_deal_ad(request):
    hot_dael = HotDealAd.objects.all().order_by("?")
    return{
        "hot_dael": hot_dael,
    }

def head_text_ad(request):
    head_text = HeadTextAd.objects.all().order_by("?")
    return{
        "head_text": head_text,
    }    
