from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import reverse_lazy


app_name = 'suppliers'
urlpatterns = [
    path('supplier-list/', views.supplier_list, name='supplier-list'),
    path('vendors-ajax/', views.VendorsJsonListView.as_view(), name="orders-ajax"),
    path('vendor-details/<str:slug>',
         views.vendor_details, name="vendor-details"),
    path('vendor-details-ajax/',
         views.VendorDetailsJsonListView.as_view(), name="orders-ajax"),

]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
