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
    path('rating/', views.product_rating, name="product_rating"),
    path('toggle-favorite/', views.toggle_favorite, name="toggle-favorite"),
    path('wishlist/', views.wishlist, name="wishlist"),
    path('api/wishlist-count/', views.get_wishlist_count, name="get-wishlist-count"),

]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
