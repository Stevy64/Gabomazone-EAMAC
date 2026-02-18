from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import reverse_lazy
# from .forms import CaptchaPasswordResetForm

app_name = 'orders'
urlpatterns = [
     path('add_to_cart/', views.add_to_cart, name='add-to-cart'),
     path('cart/', views.cart, name='cart'),
     path('cart/<str:country>/', views.StatesJsonListView.as_view(), name="get-states"),
     path('order/remeve-product/<int:productdeatails_id>',
          views.remove_item, name="remove-item"),
     path('payment/', views.payment, name="payment"),
     path('payment_blance/', views.payment_blance, name="payment-blance"),
     path('payment_cash/', views.payment_cash, name="payment-cash"),
     path('payment_cash_fee/', views.payment_cash_fee, name="payment-cash-fee"),
     path('order/cancel/', views.CancelView.as_view(), name='cancel'),
     path('order/success/', views.success, name='success'),
     # path('create_payment/', views.create_payment, name='create-payment'),
     # #     path('mob/', views.my_MOB_view, name='my-mob')
     # path('tracking/', views.tracking, name='tracking'),
    path('api/cart-count/', views.get_cart_count, name="get-cart-count"),
    path('invoice-print/<int:order_id>/', views.invoice_print, name="invoice-print"),
    path('order/<int:order_id>/verify-b2c-buyer/', views.verify_b2c_buyer_code, name='verify-b2c-buyer'),
    path('order/<int:order_id>/verify-b2c-seller/', views.verify_b2c_seller_code, name='verify-b2c-seller'),
]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
