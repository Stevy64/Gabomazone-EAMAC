"""
URLs pour le module C2C
"""
from django.urls import path
from . import views
from . import views_seller_reviews

app_name = 'c2c'

urlpatterns = [
    # Intentions d'achat
    path('purchase-intent/', views.get_purchase_intent_for_conversation, name='get-purchase-intent'),
    path('purchase-intent/<int:product_id>/', views.create_purchase_intent, name='create-purchase-intent'),
    path('purchase-intent/<int:intent_id>/accept/', views.accept_purchase_intent, name='accept-purchase-intent'),
    path('purchase-intent/<int:intent_id>/reject/', views.reject_purchase_intent, name='reject-purchase-intent'),
    path('purchase-intent/<int:intent_id>/cancel/', views.cancel_purchase_intent, name='cancel-purchase-intent'),
    path('negotiation/<int:intent_id>/make-offer/', views.create_negotiation, name='make-offer'),
    path('negotiation/<int:negotiation_id>/accept/', views.accept_negotiation, name='accept-negotiation'),
    path('negotiation/<int:negotiation_id>/reject/', views.reject_negotiation, name='reject-negotiation'),
    path('purchase-intent/<int:intent_id>/accept-price/', views.accept_final_price, name='accept-final-price'),
    
    # Commandes C2C
    path('order/<int:order_id>/', views.c2c_order_detail, name='order-detail'),
    path('order/<int:order_id>/payment/', views.init_c2c_payment, name='init-payment'),
    path('order/<int:order_id>/payment-success/', views.payment_success, name='payment-success'),
    
    # Vérification de livraison
    path('order/<int:order_id>/verify-seller-code/', views.verify_seller_code, name='verify-seller-code'),
    path('order/<int:order_id>/verify-buyer-code/', views.verify_buyer_code, name='verify-buyer-code'),
    
    # Boosts
    path('boost/<int:product_id>/', views.boost_product, name='boost-product'),
    path('boost/<int:product_id>/purchase/', views.purchase_boost, name='purchase-boost'),
    path('boost/<int:product_id>/success/', views.boost_success, name='boost-success'),
    path('boost/<int:product_id>/simulate/', views.simulate_boost_payment, name='simulate-boost'),
    
    # Dashboard vendeur
    path('seller/dashboard/', views.seller_dashboard, name='seller-dashboard'),
    path('seller/orders/', views.seller_orders, name='seller-orders'),
    path('seller/intents/', views.seller_intents, name='seller-intents'),
    
    # Dashboard acheteur
    path('buyer/orders/', views.buyer_orders, name='buyer-orders'),
    path('buyer/intents/', views.buyer_intents, name='buyer-intents'),
    
    # Avis et notes vendeurs
    path('seller/<int:seller_id>/profile/', views_seller_reviews.seller_profile, name='seller-profile'),
    path('review/<int:order_id>/create/', views_seller_reviews.create_review, name='create-review'),
    path('review/<int:review_id>/delete/', views_seller_reviews.delete_review, name='delete-review'),
    path('seller/<int:seller_id>/stats/', views_seller_reviews.get_seller_stats, name='seller-stats'),
]

