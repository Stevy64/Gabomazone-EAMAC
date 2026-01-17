"""
URLs pour les paiements SingPay
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('singpay/init/', views.init_singpay_payment, name='init-singpay'),
    path('singpay/callback/', views.singpay_callback, name='singpay-callback'),
    path('singpay/return/', views.singpay_return, name='singpay-return'),
    path('singpay/verify/<str:transaction_id>/', views.verify_singpay_payment, name='verify-singpay'),
    path('singpay/test-payment/<str:transaction_id>/', views.test_singpay_payment, name='test-singpay'),
    path('singpay/details/<str:transaction_id>/', views.get_transaction_details, name='transaction-details'),
    path('singpay/transactions/', views.list_singpay_transactions, name='transactions'),
    path('singpay/transactions/cancel/<str:transaction_id>/', views.cancel_transaction, name='cancel-transaction'),
    path('singpay/transactions/refund/<str:transaction_id>/', views.refund_transaction, name='refund-transaction'),
]

