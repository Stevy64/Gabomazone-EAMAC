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
     path('order/cancel/', views.CancelView.as_view(), name='cancel'),
     path('order/success/', views.success, name='success'),
     # path('create_payment/', views.create_payment, name='create-payment'),
     path('create_checkout_session/',
          views.create_checkout_session, name='create_checkout_session'),
     path('orders/webhook/', views.my_webhook_view, name='my-webhook'),
     # #     path('mob/', views.my_MOB_view, name='my-mob')
     # path('tracking/', views.tracking, name='tracking'),
     path('verify-payment/', views.verify_payment_razorpay, name="verify-payment"),
     path('verify-payment-paypal/', views.verify_payment_paypal,
          name="verify-payment-paypal"),
     path('checkout-paymob/<int:id>',
          views.checkout_payment_paymob, name="checkout-paymob"),
     path('api/callbacks/', views.my_webhook_view_paymob,
          name="webhook-view-paymob"),
          
     path('checkout-fatoorah/<int:id>',
         views.send_payment_fatoorah, name="checkout-fatoorah"),

     path('api/callbacks-myfatoorah/', views.callback_url_fatoorah,
          name="callbacks-myfatoorah"),
     
]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
