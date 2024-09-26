from django.contrib import admin
from .models import (
    Carousel, HomeAdSidebar, HomeAdMiddlebar, HomeAdSupplier,
    HomeAdDaily, HomeAdDealTime, VendorDetailsAdImage, ShopAdSidebar, HotDealAd , HeadTextAd
)
# Register your models here.

admin.site.register(Carousel)
admin.site.register(HomeAdSidebar)
admin.site.register(HomeAdMiddlebar)
admin.site.register(HomeAdSupplier)
admin.site.register(HomeAdDaily)
admin.site.register(HomeAdDealTime)
admin.site.register(VendorDetailsAdImage)
admin.site.register(ShopAdSidebar)
admin.site.register(HotDealAd)
admin.site.register(HeadTextAd)