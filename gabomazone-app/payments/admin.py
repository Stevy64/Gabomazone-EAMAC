from django.contrib import admin
from .models import VendorPayments, SingPayTransaction, SingPayWebhookLog
from accounts.models import BankAccount


# Register your models here.
# class Inline_BankAccount(admin.StackedInline):
#     model = BankAccount
#     # readonly_fields = ("",)
#     extra = 0

@admin.register(VendorPayments)
class VendorPaymentsAdmin(admin.ModelAdmin):
    #fields = ("","")
    # inlines = [Inline_BankAccount, ]
    list_display = ('id', 'vendor_profile', 'request_amount', 'fee',
                    'method', 'date', 'status', )
    list_filter = ('status', 'method', )
    list_editable = ("status",)
    list_display_links = ("id","request_amount",'method', )
    list_per_page = 10
    search_fields = ("request_amount", )
    readonly_fields = ('date', 'date_update')


@admin.register(SingPayTransaction)
class SingPayTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'internal_order_id', 'amount', 'currency', 'status',
        'transaction_type', 'customer_name', 'customer_email', 'created_at'
    )
    list_filter = ('status', 'transaction_type', 'currency', 'created_at')
    search_fields = ('transaction_id', 'internal_order_id', 'customer_email', 'customer_phone', 'customer_name')
    readonly_fields = (
        'transaction_id', 'reference', 'payment_url', 'created_at', 'updated_at',
        'paid_at', 'expires_at'
    )
    fieldsets = (
        ('Informations SingPay', {
            'fields': ('transaction_id', 'reference', 'internal_order_id', 'status')
        }),
        ('Paiement', {
            'fields': ('amount', 'currency', 'transaction_type', 'payment_method', 'paid_at')
        }),
        ('Client', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('URLs', {
            'fields': ('payment_url', 'callback_url', 'return_url', 'expires_at')
        }),
        ('Relations', {
            'fields': ('user', 'order', 'product', 'peer_product')
        }),
        ('Métadonnées', {
            'fields': ('description', 'metadata')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    list_per_page = 25
    date_hierarchy = 'created_at'


@admin.register(SingPayWebhookLog)
class SingPayWebhookLogAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'transaction', 'is_valid', 'processed', 'created_at'
    )
    list_filter = ('is_valid', 'processed', 'created_at')
    search_fields = ('transaction__transaction_id', 'transaction__internal_order_id', 'error_message')
    readonly_fields = ('transaction', 'payload', 'signature', 'timestamp', 'created_at')
    fieldsets = (
        ('Webhook', {
            'fields': ('transaction', 'payload', 'signature', 'timestamp')
        }),
        ('Statut', {
            'fields': ('is_valid', 'processed', 'error_message')
        }),
        ('Date', {
            'fields': ('created_at',)
        }),
    )
    list_per_page = 25
    date_hierarchy = 'created_at'