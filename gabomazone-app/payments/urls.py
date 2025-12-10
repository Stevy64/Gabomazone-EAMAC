"""
URLs pour les paiements SingPay
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('singpay/init/', views.init_singpay_payment, name='init-singpay'),
    path('singpay/callback/', views.singpay_callback, name='singpay-callback'),
    path('singpay/verify/<str:transaction_id>/', views.verify_singpay_payment, name='verify-singpay'),
    path('singpay/test-payment/<str:transaction_id>/', views.test_singpay_payment, name='test-singpay'),
    path('singpay/details/<str:transaction_id>/', views.get_transaction_details, name='transaction-details'),
]

