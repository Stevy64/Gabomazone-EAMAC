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
    vendor_detail = Profile.objects.filter( slug=slug).first()
    vendor_social_links = SocialLink.objects.filter( vendor_profile=vendor_detail).first()
    context = {
        "vendor_detail": vendor_detail,
        "vendor_social_links":vendor_social_links,
    }
    return render(request, 'suppliers/vendor-details.html', context)


class VendorDetailsJsonListView(View):
    def get(self, *args, **kwargs):

        upper = int(self.request.GET.get("num_products"))
        order_by = self.request.GET.get("order_by")
        product_vendor = int(self.request.GET.get("vendor_slug"))
        lower = upper - 10
        products = list(Product.objects.all(
        ).filter(product_vendor=product_vendor , PRDISDeleted = False , PRDISactive = True).values().order_by(order_by)[lower:upper])
        products_size = len(
            Product.objects.all().filter(product_vendor=product_vendor ,PRDISDeleted = False , PRDISactive = True))

        max_size = True if upper >= products_size else False
        return JsonResponse({"data": products,  "max": max_size, "products_size": products_size, }, safe=False)
