from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import reverse_lazy


app_name = 'products'
urlpatterns = [
    path('product-details/<str:slug>',
         views.product_details, name='product-details'),
    path('product-search/',views.product_search , name="product-search"),
    path('rating/', views.product_rating, name="product_rating")     

]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
