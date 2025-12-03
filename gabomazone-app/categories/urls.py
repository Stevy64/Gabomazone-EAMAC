from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import reverse_lazy


app_name = 'categories'
urlpatterns = [
    path("category-list/", views.category_list, name="category-list"),
    path('shop/', views.shop, name='shop'),
    path('shop/super/<str:slug>', views.super_category, name='super-category'),
    path('shop/main/<str:slug>', views.main_category, name='main-category'),
    path('shop/sub/<str:slug>', views.sub_category, name='sub-category'),

    # CategoryJsonListView supprimé - utilisation exclusive de HTMX
    # path('shop-ajax/', views.CategoryJsonListView.as_view(), name='shop-ajax'),
    
    # Vue HTMX pour scroll infini
    path('shop-htmx/', views.ProductListHTMXView.as_view(),
         name='shop-htmx'),
    
    # Endpoints AJAX pour les catégories
    path('get-main-categories/', views.get_main_categories, name='get-main-categories'),
    path('get-sub-categories/', views.get_sub_categories, name='get-sub-categories'),

]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
