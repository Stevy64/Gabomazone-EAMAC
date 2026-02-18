from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from .models import VendorPayments, SingPayTransaction, SingPayWebhookLog
from .services.singpay import singpay_service
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
        'transaction_type', 'escrow_status', 'customer_name', 'customer_email', 'created_at'
    )
    list_filter = ('status', 'transaction_type', 'escrow_status', 'currency', 'created_at')
    search_fields = ('transaction_id', 'internal_order_id', 'customer_email', 'customer_phone', 'customer_name')
    readonly_fields = (
        'transaction_id', 'reference', 'payment_url', 'created_at', 'updated_at',
        'paid_at', 'expires_at', 'escrow_released_at', 'disbursement_id'
    )
    fieldsets = (
        ('Informations SingPay', {
            'fields': ('transaction_id', 'reference', 'internal_order_id', 'status')
        }),
        ('Paiement', {
            'fields': ('amount', 'currency', 'transaction_type', 'payment_method', 'paid_at')
        }),
        ('Escrow (séquestre)', {
            'fields': ('escrow_status', 'escrow_released_at', 'disbursement_id'),
            'description': 'Pour C2C: fonds bloqués jusqu\'à double vérification des codes.'
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
    actions = [
        'cancel_selected_transactions',
        'refund_selected_transactions',
        'verify_selected_transactions',
        'release_escrow_c2c_selected',
        'refund_c2c_cancel_keep_fees_selected',
    ]
    
    def cancel_selected_transactions(self, request, queryset):
        """Action admin pour annuler des transactions sélectionnées"""
        cancelled = 0
        errors = 0
        
        for transaction in queryset:
            if transaction.can_be_cancelled():
                success, response = singpay_service.cancel_payment(
                    transaction_id=transaction.transaction_id,
                    reason='Annulé par l\'administrateur'
                )
                if success:
                    transaction.status = SingPayTransaction.CANCELLED
                    transaction.save()
                    cancelled += 1
                else:
                    errors += 1
            else:
                errors += 1
        
        if cancelled > 0:
            self.message_user(request, f'{cancelled} transaction(s) annulée(s) avec succès', messages.SUCCESS)
        if errors > 0:
            self.message_user(request, f'{errors} transaction(s) n\'ont pas pu être annulée(s)', messages.WARNING)
    cancel_selected_transactions.short_description = "Annuler les transactions sélectionnées"
    
    def refund_selected_transactions(self, request, queryset):
        """Action admin pour rembourser des transactions sélectionnées"""
        refunded = 0
        errors = 0
        
        for transaction in queryset:
            if transaction.can_be_refunded():
                success, response = singpay_service.refund_payment(
                    transaction_id=transaction.transaction_id,
                    reason='Remboursement par l\'administrateur'
                )
                if success:
                    transaction.status = SingPayTransaction.REFUNDED
                    transaction.save()
                    refunded += 1
                else:
                    errors += 1
            else:
                errors += 1
        
        if refunded > 0:
            self.message_user(request, f'{refunded} transaction(s) remboursée(s) avec succès', messages.SUCCESS)
        if errors > 0:
            self.message_user(request, f'{errors} transaction(s) n\'ont pas pu être remboursée(s)', messages.WARNING)
    refund_selected_transactions.short_description = "Rembourser les transactions sélectionnées"
    
    def verify_selected_transactions(self, request, queryset):
        """Action admin pour vérifier le statut des transactions sélectionnées"""
        updated = 0
        
        for transaction in queryset:
            if transaction.status == transaction.PENDING:
                success, response = singpay_service.verify_payment(transaction.transaction_id)
                if success:
                    api_status = response.get('status', '').lower()
                    if api_status == 'success' and transaction.status != transaction.SUCCESS:
                        transaction.status = transaction.SUCCESS
                        transaction.paid_at = timezone.now()
                        transaction.save()
                        updated += 1
        
        if updated > 0:
            self.message_user(request, f'{updated} transaction(s) mise(s) à jour', messages.SUCCESS)
    verify_selected_transactions.short_description = "Vérifier le statut des transactions sélectionnées"

    def release_escrow_c2c_selected(self, request, queryset):
        """Libère l'escrow pour les transactions C2C sélectionnées (versement au vendeur)."""
        from payments.escrow_service import EscrowService
        from .models import SingPayTransaction
        released = 0
        errors = 0
        q = queryset.filter(
            transaction_type=SingPayTransaction.C2C_PAYMENT,
            status=SingPayTransaction.SUCCESS,
            escrow_status=SingPayTransaction.ESCROW_PENDING,
        )
        for transaction in q:
            c2c_order = transaction.c2c_orders.first()
            if not c2c_order:
                errors += 1
                continue
            success, response = EscrowService.release_escrow_for_c2c_order(c2c_order)
            if success:
                released += 1
            else:
                errors += 1
        if released:
            self.message_user(request, f'{released} escrow C2C libéré(s) avec succès', messages.SUCCESS)
        if errors:
            self.message_user(request, f'{errors} échec(s)', messages.WARNING)
    release_escrow_c2c_selected.short_description = "Libérer l'escrow (C2C) - verser au vendeur"

    def refund_c2c_cancel_keep_fees_selected(self, request, queryset):
        """Rembourse l'acheteur (montant - frais) et garde les frais plateforme (annulation C2C)."""
        from payments.escrow_service import EscrowService
        from .models import SingPayTransaction
        done = 0
        errors = 0
        q = queryset.filter(
            transaction_type=SingPayTransaction.C2C_PAYMENT,
            status=SingPayTransaction.SUCCESS,
            escrow_status=SingPayTransaction.ESCROW_PENDING,
        )
        for transaction in q:
            c2c_order = transaction.c2c_orders.first()
            if not c2c_order:
                errors += 1
                continue
            success, response = EscrowService.refund_escrow_c2c_cancel(
                c2c_order, reason='Annulation par l\'administrateur', initiated_by='admin'
            )
            if success:
                done += 1
            else:
                errors += 1
        if done:
            self.message_user(request, f'{done} remboursement(s) C2C (frais gardés) effectué(s)', messages.SUCCESS)
        if errors:
            self.message_user(request, f'{errors} échec(s)', messages.WARNING)
    refund_c2c_cancel_keep_fees_selected.short_description = "Rembourser C2C (annulation, garder frais)"


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