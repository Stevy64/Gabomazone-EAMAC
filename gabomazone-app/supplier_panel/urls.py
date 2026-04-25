from django.urls import path
from . import views


app_name = 'supplier_dashboard'
urlpatterns = [
    path('supplier-panel/', views.supplier_dashboard, name='supplier-panel'),
    path('chart-ajax/', views.chartJsonListView.as_view(), name="chart-ajax"),
    path('chart-ajax-admin/', views.chartJsonListViewAdmin.as_view(), name="chart-ajax-admin"),
    path('supplier-login/', views.supplier_login, name="supplier-login"),
    path('supplier-register/', views.supplier_register, name="supplier-register"),
    path('verify-vendor-email/<str:token>/', views.verify_vendor_email, name="verify-vendor-email"),
    path('supplier-add-product/', views.supplier_add_product,
         name="supplier-add-product"),
    path('supplier-categories-ajax/', views.CategoriesJsonListView.as_view(),
         name="get-categories"),
    path('supplier-products-list-ajax/', views.SupplierProductsJsonListView.as_view(),
         name="supplier-products-list-ajax"),
    path('supplier-products/remove-product/<int:id>/',
         views.remove_product, name="remove-product"),
    # Redirection permanente pour l'ancienne URL (compatibilité liens existants)
    path('supplier-products/remeve-product/<int:id>/',
         views.remove_product, name="remove-item"),
    path('supplier-edit-product/<int:id>/', views.supplier_edit_product,
         name="supplier-edit-product"),
    path('supplier-orders-list/', views.supplier_orders_list,
         name="supplier-orders-list"),
    path('supplier-reviews/', views.supplier_reviews, name="supplier-reviews"),
    path('settings/store-settings/', views.store_settings, name="store-settings"),
    path('settings/subscriptions/', views.subscriptions, name="subscriptions"),
    path('subscriptions/success/', views.subscription_success, name="subscription-success"),
    path('subscriptions/boost-success/<int:boost_request_id>/', views.boost_success, name="boost-success"),
    path('settings/delete-account/', views.delete_account, name="delete-account"),
    path('supplier-orders-list-ajax/', views.SupplierOrdersJsonListView.as_view(),
         name="supplier-orders-list-ajax"),
    path('order-details/<int:id>/',
         views.supplier_orders_detail, name='order-details'),
    path('payments/', views.payments, name="payments"),
    path('request_payment/', views.request_payment, name="request-payment"),
    path('notifications/', views.get_notifications, name="notifications"),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name="mark-notification-read"),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name="mark-all-notifications-read"),
    path('messagerie-b2c/', views.vendor_b2c_messages, name='vendor-b2c-messages'),
]
