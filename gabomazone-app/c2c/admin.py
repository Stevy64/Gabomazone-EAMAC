"""
Interface d'administration pour le module C2C
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    PlatformSettings, PurchaseIntent, Negotiation, C2COrder,
    DeliveryVerification, ProductBoost, SellerBadge, SellerReview, BuyerReview,
    C2CPaymentEvent, DisputeCase, SafeZone,
)


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    """Administration des paramètres de la plateforme"""
    list_display = ('id', 'c2c_seller_commission_rate',
                   'popular_meeting_min_uses', 'b2c_buyer_commission_rate', 'b2c_seller_commission_rate', 'is_active', 'updated_at')
    list_editable = ('is_active',)
    fieldsets = (
        ('Commissions C2C', {
            'fields': ('c2c_seller_commission_rate',)
        }),
        ('Carte C2C (points de rencontre)', {
            'fields': ('popular_meeting_min_uses',)
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
    readonly_fields = ('created_at', 'updated_at', 'agreed_at', 'availability_confirmed_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('product', 'buyer', 'seller', 'status')
        }),
        ('Prix', {
            'fields': ('initial_price', 'negotiated_price', 'final_price')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'agreed_at', 'expires_at', 'availability_confirmed_at')
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


class C2CPaymentEventInline(admin.TabularInline):
    model = C2CPaymentEvent
    extra = 0
    readonly_fields = ('event_type', 'transaction', 'amount_refunded', 'commission_retained', 'metadata', 'created_at')
    can_delete = False
    max_num = 0
    ordering = ('-created_at',)


@admin.register(C2COrder)
class C2COrderAdmin(admin.ModelAdmin):
    """Administration des commandes C2C avec traçabilité complète et pilotage escrow"""
    list_display = ('id', 'product_link', 'buyer', 'seller', 'final_price',
                   'buyer_total', 'platform_commission', 'status_badge', 'escrow_status_display', 'created_at', 'view_details')
    list_filter = ('status', 'created_at', 'paid_at', 'buyer', 'seller')
    inlines = [C2CPaymentEventInline]
    actions = ['action_cancel_and_refund_keep_fees', 'action_release_escrow_manual']
    search_fields = ('product__product_name', 'buyer__username', 'buyer__email', 
                    'seller__username', 'seller__email', 'id')
    date_hierarchy = 'created_at'
    list_select_related = ('buyer', 'seller', 'product', 'payment_transaction', 'purchase_intent')
    ordering = ('-created_at',)
    list_per_page = 30
    save_on_top = True
    show_full_result_count = False
    
    def view_details(self, obj):
        """Lien vers la page de détails"""
        url = reverse('admin:c2c_c2corder_change', args=[obj.id])
        return format_html('<a href="{}" class="button">Voir détails</a>', url)
    view_details.short_description = 'Actions'
    readonly_fields = ('created_at', 'paid_at', 'delivered_at', 'completed_at',
                      'negotiations_history', 'conversation_history', 'verification_details')
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
        ('📊 Historique des négociations', {
            'fields': ('negotiations_history',),
            'classes': ('collapse',)
        }),
        ('💬 Historique des conversations', {
            'fields': ('conversation_history',),
            'classes': ('collapse',)
        }),
        ('🔐 Codes de vérification', {
            'fields': ('verification_details',),
            'classes': ('collapse',)
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

    def escrow_status_display(self, obj):
        """Affiche le statut escrow de la transaction liée"""
        t = getattr(obj, 'payment_transaction', None)
        if not t:
            return '-'
        status = getattr(t, 'escrow_status', None)
        if not status:
            return '-'
        labels = {'none': '-', 'escrow_pending': 'En attente', 'escrow_released': 'Libéré', 'escrow_refunded': 'Remboursé'}
        return labels.get(status, status)
    escrow_status_display.short_description = 'Escrow'

    def status_badge(self, obj):
        labels = {
            C2COrder.PENDING_PAYMENT: ('En attente paiement', '#FEF3C7', '#92400E'),
            C2COrder.PAID: ('Payé', '#DBEAFE', '#1E3A8A'),
            C2COrder.PENDING_DELIVERY: ('Livraison en attente', '#E0E7FF', '#3730A3'),
            C2COrder.DELIVERED: ('Livré', '#ECFCCB', '#3F6212'),
            C2COrder.VERIFIED: ('Vérifié', '#DCFCE7', '#166534'),
            C2COrder.COMPLETED: ('Terminé', '#DCFCE7', '#14532D'),
            C2COrder.CANCELLED: ('Annulé', '#F3F4F6', '#374151'),
            C2COrder.DISPUTED: ('Litige', '#FEE2E2', '#991B1B'),
        }
        label, bg, fg = labels.get(obj.status, (obj.status, '#F3F4F6', '#111827'))
        return format_html('<span style="background:{};color:{};padding:4px 10px;border-radius:999px;font-weight:700;">{}</span>', bg, fg, label)
    status_badge.short_description = 'Statut'

    def action_cancel_and_refund_keep_fees(self, request, queryset):
        """Annuler les commandes C2C sélectionnées : rembourser l'acheteur et garder les frais."""
        from django.contrib import messages
        from payments.escrow_service import EscrowService
        from payments.models import SingPayTransaction
        done = 0
        errors = 0
        for order in queryset:
            if order.status not in (order.PAID, order.PENDING_DELIVERY, order.DELIVERED):
                errors += 1
                continue
            if not getattr(order, 'payment_transaction', None):
                errors += 1
                continue
            if order.payment_transaction.escrow_status != SingPayTransaction.ESCROW_PENDING:
                errors += 1
                continue
            success, _ = EscrowService.refund_escrow_c2c_cancel(
                order, reason='Annulation par l\'administrateur', initiated_by='admin'
            )
            if success:
                done += 1
            else:
                errors += 1
        if done:
            self.message_user(request, f'{done} commande(s) annulée(s) et remboursée(s) (frais gardés)', messages.SUCCESS)
        if errors:
            self.message_user(request, f'{errors} commande(s) non éligibles ou en échec', messages.WARNING)
    action_cancel_and_refund_keep_fees.short_description = "Annuler et rembourser (frais gardés)"

    def action_release_escrow_manual(self, request, queryset):
        """Libérer manuellement l'escrow pour les commandes C2C sélectionnées."""
        from django.contrib import messages
        from payments.escrow_service import EscrowService
        from payments.models import SingPayTransaction
        released = 0
        errors = 0
        for order in queryset:
            t = getattr(order, 'payment_transaction', None)
            if not t or t.escrow_status != SingPayTransaction.ESCROW_PENDING:
                errors += 1
                continue
            success, _ = EscrowService.release_escrow_for_c2c_order(order)
            if success:
                released += 1
            else:
                errors += 1
        if released:
            self.message_user(request, f'{released} escrow libéré(s)', messages.SUCCESS)
        if errors:
            self.message_user(request, f'{errors} non éligibles ou échec', messages.WARNING)
    action_release_escrow_manual.short_description = "Libérer l'escrow (manuel)"
    
    def negotiations_history(self, obj):
        """Affiche l'historique complet des négociations"""
        if not obj.purchase_intent:
            return format_html('<p style="color: #999;">Aucune intention d\'achat associée</p>')
        
        negotiations = obj.purchase_intent.negotiations.all().order_by('created_at')
        if not negotiations.exists():
            return format_html('<p style="color: #999;">Aucune négociation enregistrée</p>')
        
        html = '<div style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #f9f9f9;">'
        html += '<h4 style="margin-top: 0;">Historique des négociations</h4>'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<thead><tr style="background: #e0e0e0;"><th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Date</th>'
        html += '<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Proposé par</th>'
        html += '<th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Prix proposé</th>'
        html += '<th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Statut</th></tr></thead><tbody>'
        
        for neg in negotiations:
            status_color = {
                'pending': '#FFA500',
                'accepted': '#10B981',
                'rejected': '#EF4444'
            }.get(neg.status, '#999')
            
            status_text = {
                'pending': 'En attente',
                'accepted': 'Accepté',
                'rejected': 'Refusé'
            }.get(neg.status, neg.status)
            
            html += f'<tr style="border-bottom: 1px solid #eee;">'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{neg.created_at.strftime("%d/%m/%Y %H:%M")}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{neg.proposer.get_full_name() or neg.proposer.username}</td>'
            html += f'<td style="padding: 8px; text-align: right; border: 1px solid #ddd; font-weight: bold;">{neg.proposed_price:,.0f} FCFA</td>'
            html += f'<td style="padding: 8px; text-align: center; border: 1px solid #ddd;"><span style="color: {status_color}; font-weight: bold;">{status_text}</span></td>'
            html += '</tr>'
            
            if neg.message:
                html += f'<tr><td colspan="4" style="padding: 4px 8px; font-style: italic; color: #666; border: 1px solid #ddd;">💬 {neg.message}</td></tr>'
        
        html += '</tbody></table>'
        html += f'<p style="margin-top: 10px; font-size: 12px; color: #666;">Prix initial: <strong>{obj.purchase_intent.initial_price:,.0f} FCFA</strong> → Prix final: <strong>{obj.final_price:,.0f} FCFA</strong></p>'
        html += '</div>'
        return format_html(html)
    negotiations_history.short_description = 'Historique des négociations'
    
    def conversation_history(self, obj):
        """Affiche l'historique des conversations"""
        from accounts.models import ProductConversation
        
        try:
            conversation = ProductConversation.objects.filter(
                product=obj.product,
                buyer=obj.buyer,
                seller=obj.seller
            ).first()
            
            if not conversation:
                return format_html('<p style="color: #999;">Aucune conversation trouvée</p>')
            
            messages = conversation.messages.all().order_by('created_at')
            if not messages.exists():
                return format_html('<p style="color: #999;">Aucun message dans cette conversation</p>')
            
            html = '<div style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #f9f9f9;">'
            html += '<h4 style="margin-top: 0;">Messages échangés</h4>'
            html += f'<p style="font-size: 12px; color: #666; margin-bottom: 15px;">Conversation #{conversation.id} - {messages.count()} message(s)</p>'
            
            for msg in messages:
                is_sender = msg.sender == obj.buyer
                bg_color = '#E3F2FD' if is_sender else '#F5F5F5'
                align = 'right' if is_sender else 'left'
                
                html += f'<div style="margin-bottom: 10px; text-align: {align};">'
                html += f'<div style="display: inline-block; max-width: 70%; background: {bg_color}; padding: 10px; border-radius: 8px; text-align: left;">'
                html += f'<div style="font-size: 11px; color: #666; margin-bottom: 5px;">{msg.sender.get_full_name() or msg.sender.username} - {msg.created_at.strftime("%d/%m/%Y %H:%M")}</div>'
                html += f'<div style="word-wrap: break-word;">{msg.message}</div>'
                html += '</div></div>'
            
            html += '</div>'
            return format_html(html)
        except Exception as e:
            return format_html(f'<p style="color: red;">Erreur: {str(e)}</p>')
    conversation_history.short_description = 'Historique des conversations'
    
    def verification_details(self, obj):
        """Affiche les détails de vérification avec les codes"""
        try:
            verification = obj.delivery_verification
        except Exception:
            return format_html('<p style="color: #999;">Aucune vérification de livraison</p>')
        
        html = '<div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #f9f9f9;">'
        html += '<h4 style="margin-top: 0;">🔐 Codes de vérification</h4>'
        
        html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">'
        
        # Code vendeur
        html += '<div style="background: white; padding: 15px; border-radius: 8px; border: 2px solid #F59E0B;">'
        html += '<h5 style="margin-top: 0; color: #92400E;">V-CODE (Vendeur)</h5>'
        html += f'<div style="font-size: 24px; font-weight: bold; letter-spacing: 4px; text-align: center; color: #D97706; font-family: monospace; padding: 10px; background: #FEF3C7; border-radius: 5px;">{verification.seller_code}</div>'
        html += f'<p style="font-size: 11px; color: #666; margin: 8px 0 0 0;">Vérifié: <strong>{"✓ Oui" if verification.seller_code_verified else "✗ Non"}</strong></p>'
        if verification.seller_code_verified_at:
            html += f'<p style="font-size: 11px; color: #666; margin: 4px 0 0 0;">Le: {verification.seller_code_verified_at.strftime("%d/%m/%Y %H:%M")}</p>'
        html += '</div>'
        
        # Code acheteur
        html += '<div style="background: white; padding: 15px; border-radius: 8px; border: 2px solid #3B82F6;">'
        html += '<h5 style="margin-top: 0; color: #1E40AF;">A-CODE (Acheteur)</h5>'
        html += f'<div style="font-size: 24px; font-weight: bold; letter-spacing: 4px; text-align: center; color: #2563EB; font-family: monospace; padding: 10px; background: #EFF6FF; border-radius: 5px;">{verification.buyer_code}</div>'
        html += f'<p style="font-size: 11px; color: #666; margin: 8px 0 0 0;">Vérifié: <strong>{"✓ Oui" if verification.buyer_code_verified else "✗ Non"}</strong></p>'
        if verification.buyer_code_verified_at:
            html += f'<p style="font-size: 11px; color: #666; margin: 4px 0 0 0;">Le: {verification.buyer_code_verified_at.strftime("%d/%m/%Y %H:%M")}</p>'
        html += '</div>'
        
        html += '</div>'
        
        # Statut global
        status_colors = {
            'pending': '#FFA500',
            'seller_code_verified': '#3B82F6',
            'buyer_code_verified': '#10B981',
            'completed': '#059669',
            'disputed': '#EF4444'
        }
        status_texts = {
            'pending': 'En attente',
            'seller_code_verified': 'Code vendeur vérifié',
            'buyer_code_verified': 'Code acheteur vérifié',
            'completed': 'Terminé',
            'disputed': 'Litige'
        }
        
        html += f'<div style="background: white; padding: 12px; border-radius: 8px; border-left: 4px solid {status_colors.get(verification.status, "#999")};">'
        html += f'<strong>Statut:</strong> <span style="color: {status_colors.get(verification.status, "#999")}; font-weight: bold;">{status_texts.get(verification.status, verification.status)}</span>'
        if verification.completed_at:
            html += f'<br><small style="color: #666;">Terminé le: {verification.completed_at.strftime("%d/%m/%Y à %H:%M")}</small>'
        html += '</div>'
        
        html += '</div>'
        return format_html(html)
    verification_details.short_description = 'Détails de vérification'


@admin.register(C2CPaymentEvent)
class C2CPaymentEventAdmin(admin.ModelAdmin):
    """Traçabilité des étapes de paiement C2C (escrow, libération, remboursement)."""
    list_display = ('id', 'c2c_order_link', 'event_type', 'amount_refunded', 'commission_retained', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('c2c_order__id', 'metadata')
    readonly_fields = ('c2c_order', 'transaction', 'event_type', 'amount_refunded', 'commission_retained', 'metadata', 'created_at')
    date_hierarchy = 'created_at'

    def c2c_order_link(self, obj):
        if obj.c2c_order:
            url = reverse('admin:c2c_c2corder_change', args=[obj.c2c_order.id])
            return format_html('<a href="{}">Commande #{}</a>', url, obj.c2c_order.id)
        return '-'
    c2c_order_link.short_description = 'Commande C2C'


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
        ('Confirmation remise / réception (avant affichage des codes)', {
            'fields': ('buyer_handover_confirmed_at', 'seller_handover_confirmed_at'),
            'description': 'Rempli depuis la messagerie ; les deux dates débloquent l’affichage des codes aux parties.',
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


@admin.register(SellerReview)
class SellerReviewAdmin(admin.ModelAdmin):
    """Administration des avis vendeurs"""
    list_display = ('id', 'seller', 'reviewer', 'product_link', 'rating', 'is_visible', 'created_at')
    list_filter = ('rating', 'is_visible', 'created_at', 'seller')
    search_fields = ('seller__username', 'reviewer__username', 'product__product_name', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Relations', {
            'fields': ('order', 'seller', 'reviewer', 'product')
        }),
        ('Avis', {
            'fields': ('rating', 'comment')
        }),
        ('Statut', {
            'fields': ('is_visible',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def product_link(self, obj):
        """Lien vers le produit"""
        if obj.product:
            url = reverse('admin:accounts_peertopeerproduct_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.product_name)
        return '-'
    product_link.short_description = 'Article'


@admin.register(BuyerReview)
class BuyerReviewAdmin(admin.ModelAdmin):
    """Administration des avis acheteurs"""
    list_display = ('id', 'buyer', 'reviewer', 'product_link', 'rating', 'is_visible', 'created_at')
    list_filter = ('rating', 'is_visible', 'created_at', 'buyer')
    search_fields = ('buyer__username', 'reviewer__username', 'product__product_name', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Relations', {
            'fields': ('order', 'buyer', 'reviewer', 'product')
        }),
        ('Avis', {
            'fields': ('rating', 'comment')
        }),
        ('Statut', {
            'fields': ('is_visible',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def product_link(self, obj):
        """Lien vers le produit"""
        if obj.product:
            url = reverse('admin:accounts_peertopeerproduct_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.product_name)
        return '-'
    product_link.short_description = 'Article'


@admin.register(DisputeCase)
class DisputeCaseAdmin(admin.ModelAdmin):
    """Administration des litiges C2C"""
    list_display = ('id', 'order_link', 'claimant', 'reason', 'status', 'mediator', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('order__id', 'claimant__username', 'description')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    date_hierarchy = 'created_at'
    actions = ['action_resolve_refund', 'action_resolve_seller']

    fieldsets = (
        ('Commande', {
            'fields': ('order', 'claimant', 'mediator')
        }),
        ('Litige', {
            'fields': ('reason', 'description', 'status')
        }),
        ('Résolution', {
            'fields': ('resolution_notes', 'resolved_at')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def order_link(self, obj):
        if obj.order:
            url = reverse('admin:c2c_c2corder_change', args=[obj.order.id])
            return format_html('<a href="{}">Commande #{}</a>', url, obj.order.id)
        return '-'
    order_link.short_description = 'Commande'

    def action_resolve_refund(self, request, queryset):
        """Résoudre en faveur de l'acheteur : remboursement automatique"""
        from payments.escrow_service import EscrowService
        count = 0
        for dispute in queryset.filter(status__in=[DisputeCase.OPEN, DisputeCase.UNDER_REVIEW]):
            order = dispute.order
            try:
                success, resp = EscrowService.refund_escrow_c2c_cancel(
                    order, reason=f'Litige #{dispute.id} résolu en faveur de l\'acheteur',
                    initiated_by='admin_dispute'
                )
                if success:
                    from django.utils import timezone as tz
                    dispute.status = DisputeCase.RESOLVED_REFUND
                    dispute.mediator = request.user
                    dispute.resolved_at = tz.now()
                    dispute.save()
                    count += 1
                else:
                    self.message_user(request, f"Litige #{dispute.id}: {resp.get('error')}", level='error')
            except Exception as e:
                self.message_user(request, f"Litige #{dispute.id}: {e}", level='error')
        if count:
            self.message_user(request, f"{count} litige(s) résolu(s) avec remboursement.")
    action_resolve_refund.short_description = "Résoudre → Remboursement acheteur"

    def action_resolve_seller(self, request, queryset):
        """Résoudre en faveur du vendeur"""
        from django.utils import timezone as tz
        count = queryset.filter(
            status__in=[DisputeCase.OPEN, DisputeCase.UNDER_REVIEW]
        ).update(
            status=DisputeCase.RESOLVED_SELLER,
            mediator=request.user,
            resolved_at=tz.now(),
        )
        self.message_user(request, f"{count} litige(s) résolu(s) en faveur du vendeur.")
    action_resolve_seller.short_description = "Résoudre → En faveur du vendeur"


@admin.register(SafeZone)
class SafeZoneAdmin(admin.ModelAdmin):
    """Administration des zones d'échange sécurisées (points de rencontre sur la carte)."""
    change_form_template = 'admin/c2c/safezone/change_form.html'
    list_display = ('id', 'name', 'city', 'coords_short', 'status', 'is_featured', 'created_at')
    list_display_links = ('id', 'name')
    list_filter = ('status', 'is_featured', 'city')
    search_fields = ('name', 'address', 'city', 'landmark')
    list_editable = ('status', 'is_featured')
    readonly_fields = ('created_at',)
    ordering = ('-is_featured', 'city', 'name')
    save_on_top = True
    show_full_result_count = False

    @admin.display(description='Coordonnées')
    def coords_short(self, obj):
        if obj.latitude is not None and obj.longitude is not None:
            return format_html(
                '<span class="text-monospace" style="font-size:11px;">{}, {}</span>',
                obj.latitude,
                obj.longitude,
            )
        return format_html('<span class="text-muted">—</span>')

    fieldsets = (
        ('Lieu', {
            'fields': ('name', 'description', 'address', 'city', 'landmark')
        }),
        ('Géolocalisation', {
            'fields': ('latitude', 'longitude'),
            'description': 'Renseignables aussi via la carte sous le formulaire.',
        }),
        ('Informations pratiques', {
            'fields': ('opening_hours',)
        }),
        ('Statut', {
            'fields': ('status', 'is_featured')
        }),
        ('Dates', {
            'fields': ('created_at',)
        }),
    )

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        from c2c.meeting_map_data import get_admin_safezone_map_context

        extra_context = extra_context or {}
        extra_context.update(get_admin_safezone_map_context())
        return super().changeform_view(request, object_id, form_url, extra_context)


