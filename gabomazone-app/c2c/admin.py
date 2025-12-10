"""
Interface d'administration pour le module C2C
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    PlatformSettings, PurchaseIntent, Negotiation, C2COrder,
    DeliveryVerification, ProductBoost, SellerBadge
)


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    """Administration des paramètres de la plateforme"""
    list_display = ('id', 'c2c_buyer_commission_rate', 'c2c_seller_commission_rate',
                   'b2c_buyer_commission_rate', 'b2c_seller_commission_rate', 'is_active', 'updated_at')
    list_editable = ('is_active',)
    fieldsets = (
        ('Commissions C2C', {
            'fields': ('c2c_buyer_commission_rate', 'c2c_seller_commission_rate')
        }),
        ('Commissions B2C', {
            'fields': ('b2c_buyer_commission_rate', 'b2c_seller_commission_rate')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
    )
    
    def has_add_permission(self, request):
        """Un seul objet de paramètres peut exister"""
        return not PlatformSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Ne pas permettre la suppression"""
        return False


@admin.register(PurchaseIntent)
class PurchaseIntentAdmin(admin.ModelAdmin):
    """Administration des intentions d'achat"""
    list_display = ('id', 'product_link', 'buyer', 'seller', 'initial_price',
                   'negotiated_price', 'final_price', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'seller', 'buyer')
    search_fields = ('product__product_name', 'buyer__username', 'seller__username')
    readonly_fields = ('created_at', 'updated_at', 'agreed_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('product', 'buyer', 'seller', 'status')
        }),
        ('Prix', {
            'fields': ('initial_price', 'negotiated_price', 'final_price')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'agreed_at', 'expires_at')
        }),
        ('Notifications', {
            'fields': ('seller_notified',)
        }),
    )
    
    def product_link(self, obj):
        """Lien vers le produit"""
        if obj.product:
            url = reverse('admin:accounts_peertopeerproduct_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.product_name)
        return '-'
    product_link.short_description = 'Article'


@admin.register(Negotiation)
class NegotiationAdmin(admin.ModelAdmin):
    """Administration des négociations"""
    list_display = ('id', 'purchase_intent', 'proposer', 'proposed_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('purchase_intent__product__product_name', 'proposer__username')
    readonly_fields = ('created_at', 'responded_at')
    date_hierarchy = 'created_at'


@admin.register(C2COrder)
class C2COrderAdmin(admin.ModelAdmin):
    """Administration des commandes C2C"""
    list_display = ('id', 'product_link', 'buyer', 'seller', 'final_price',
                   'buyer_total', 'platform_commission', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'paid_at')
    search_fields = ('product__product_name', 'buyer__username', 'seller__username')
    readonly_fields = ('created_at', 'paid_at', 'delivered_at', 'completed_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('purchase_intent', 'product', 'buyer', 'seller', 'status')
        }),
        ('Prix et commissions', {
            'fields': ('final_price', 'buyer_commission', 'seller_commission',
                      'platform_commission', 'seller_net', 'buyer_total')
        }),
        ('Paiement', {
            'fields': ('payment_transaction', 'paid_at')
        }),
        ('Livraison', {
            'fields': ('delivered_at', 'completed_at')
        }),
        ('Dates', {
            'fields': ('created_at',)
        }),
    )
    
    def product_link(self, obj):
        """Lien vers le produit"""
        if obj.product:
            url = reverse('admin:accounts_peertopeerproduct_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.product_name)
        return '-'
    product_link.short_description = 'Article'


@admin.register(DeliveryVerification)
class DeliveryVerificationAdmin(admin.ModelAdmin):
    """Administration des vérifications de livraison"""
    list_display = ('id', 'c2c_order_link', 'seller_code_verified', 'buyer_code_verified',
                   'status', 'created_at')
    list_filter = ('status', 'seller_code_verified', 'buyer_code_verified', 'created_at')
    readonly_fields = ('seller_code', 'buyer_code', 'created_at', 'completed_at',
                      'seller_code_verified_at', 'buyer_code_verified_at')
    
    fieldsets = (
        ('Commande', {
            'fields': ('c2c_order',)
        }),
        ('Codes de vérification', {
            'fields': ('seller_code', 'buyer_code')
        }),
        ('Vérifications', {
            'fields': ('seller_code_verified', 'seller_code_verified_at',
                      'buyer_code_verified', 'buyer_code_verified_at')
        }),
        ('Statut', {
            'fields': ('status',)
        }),
        ('Dates', {
            'fields': ('created_at', 'completed_at')
        }),
    )
    
    def c2c_order_link(self, obj):
        """Lien vers la commande C2C"""
        if obj.c2c_order:
            url = reverse('admin:c2c_c2corder_change', args=[obj.c2c_order.id])
            return format_html('<a href="{}">Commande #{}</a>', url, obj.c2c_order.id)
        return '-'
    c2c_order_link.short_description = 'Commande C2C'


@admin.register(ProductBoost)
class ProductBoostAdmin(admin.ModelAdmin):
    """Administration des boosts de produits"""
    list_display = ('id', 'product_link', 'buyer', 'duration', 'status',
                   'start_date', 'end_date', 'is_active_display', 'price')
    list_filter = ('status', 'duration', 'start_date', 'end_date')
    search_fields = ('product__product_name', 'buyer__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'start_date'
    
    def product_link(self, obj):
        """Lien vers le produit"""
        if obj.product:
            url = reverse('admin:accounts_peertopeerproduct_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.product_name)
        return '-'
    product_link.short_description = 'Article'
    
    def is_active_display(self, obj):
        """Affiche si le boost est actif"""
        if obj.is_active():
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    is_active_display.short_description = 'Statut'


@admin.register(SellerBadge)
class SellerBadgeAdmin(admin.ModelAdmin):
    """Administration des badges vendeurs"""
    list_display = ('id', 'seller', 'badge_type', 'assignment_type', 'is_active',
                   'assigned_at', 'expires_at')
    list_filter = ('badge_type', 'assignment_type', 'is_active', 'assigned_at')
    search_fields = ('seller__username', 'seller__email')
    readonly_fields = ('assigned_at',)
    date_hierarchy = 'assigned_at'
    
    fieldsets = (
        ('Vendeur', {
            'fields': ('seller',)
        }),
        ('Badge', {
            'fields': ('badge_type', 'assignment_type')
        }),
        ('Critères (automatique)', {
            'fields': ('min_rating', 'min_successful_transactions')
        }),
        ('Statut', {
            'fields': ('is_active', 'expires_at')
        }),
        ('Dates', {
            'fields': ('assigned_at',)
        }),
    )

