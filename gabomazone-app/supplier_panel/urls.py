from unicodedata import name
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import reverse_lazy


app_name = 'supplier_dashboard'
urlpatterns = [
    path('supplier-panel/', views.supplier_dashboard, name='supplier-panel'),
    path('chart-ajax/', views.chartJsonListView.as_view(), name="chart-ajax"),
    path('chart-ajax-admin/', views.chartJsonListViewAdmin.as_view(), name="chart-ajax-admin"),
    path('supplier-login/', views.supplier_login, name="supplier-login"),
    path('supplier-register/', views.supplier_register, name="supplier-register"),
    path('supplier-add-product/', views.supplier_add_product,
         name="supplier-add-product"),
    path('supplier-categories-ajax/', views.CategoriesJsonListView.as_view(),
         name="get-categories"),
    path('supplier-products-list/', views.supplier_products_list,
         name="supplier-products-list"),

    path('supplier-products-list-ajax/', views.SupplierProductsJsonListView.as_view(),
         name="supplier-products-list-ajax"),
    path('supplier-products/remeve-product/<int:id>/',
         views.remove_product, name="remove-item"),
    path('supplier-edit-product/<int:id>/', views.supplier_edit_product,
         name="supplier-edit-product"),
    path('supplier-orders-list/', views.supplier_orders_list,
         name="supplier-orders-list"),
    #     path('supplier-orders-detail/', views.supplier_orders_detail,
    #          name="supplier-orders-detail"),
#     path('supplier-transactions/', views.supplier_transactions,
#          name="supplier-transactions"),
    path('supplier-reviews/', views.supplier_reviews,  name="supplier-reviews"),

    path('settings/bank-info/', views.bank_info, name="bank-info"),
    path('settings/social-links/', views.social_links, name="social-links"),
#     path('page_settings_2/', views.page_settings_2, name="page-settings-2"),
    path('supplier-orders-list-ajax/', views.SupplierOrdersJsonListView.as_view(),
         name="supplier-orders-list-ajax"),
    path('order-details/<int:id>/',
         views.supplier_orders_detail, name='order-details'),
    path('payments/', views.payments, name="payments"), 
    path('request_payment/', views.request_payment, name="request-payment"),
    path('notifications/', views.get_notifications, name="notifications"),


]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
