from django.contrib import admin
from .models import Profile, PeerToPeerProduct, DeliveryCode, PremiumSubscription, ProductBoostRequest, ProductConversation, ProductMessage, AdminNotification
from django.utils import timezone
# Register your models here.

class ProfileAdmin(admin.ModelAdmin):
    #fields = ("","")
    # inlines = [ ]
    list_display = ('id', 'user', 'mobile_number', 'country', 'blance',"status" , "admission")
    list_filter = ("status",)
    # list_editable = ()
    list_display_links = ("id", 'user', )
    list_per_page = 10
    search_fields = ("id", 'user__username',)

admin.site.register(Profile,ProfileAdmin)


class PeerToPeerProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_name', 'seller', 'PRDPrice', 'status', 'date')
    list_filter = ('status', 'date')
    list_display_links = ('id', 'product_name')
    search_fields = ('product_name', 'seller__username')
    readonly_fields = ('commission_amount', 'seller_amount', 'date', 'date_update', 'approved_date')
    list_per_page = 20

admin.site.register(PeerToPeerProduct, PeerToPeerProductAdmin)


class DeliveryCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'buyer', 'seller', 'peer_to_peer_product', 'status', 'created_date')
    list_filter = ('status', 'created_date')
    list_display_links = ('code',)
    search_fields = ('code', 'buyer__username', 'seller__username')
    readonly_fields = ('code', 'created_date', 'verified_date')
    list_per_page = 20

admin.site.register(DeliveryCode, DeliveryCodeAdmin)


class PremiumSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'status', 'start_date', 'end_date', 'price', 'payment_status', 'is_active_display', 'created_date')
    list_filter = ('status', 'payment_status', 'created_date')
    list_display_links = ('id', 'vendor')
    search_fields = ('vendor__user__username', 'vendor__display_name')
    readonly_fields = ('created_date', 'updated_date')
    list_per_page = 20
    
    fieldsets = (
        ('Informations du vendeur', {
            'fields': ('vendor',)
        }),
        ('Détails de l\'abonnement', {
            'fields': ('status', 'start_date', 'end_date', 'price', 'payment_status')
        }),
        ('Dates', {
            'fields': ('created_date', 'updated_date')
        }),
    )
    
    def is_active_display(self, obj):
        """Affiche si l'abonnement est actif"""
        if obj.is_active():
            return "✓ Actif"
        return "✗ Inactif"
    is_active_display.short_description = 'Statut actuel'
    
    actions = ['activate_subscription', 'deactivate_subscription', 'mark_as_paid']
    
    def activate_subscription(self, request, queryset):
        """Activer les abonnements sélectionnés"""
        now = timezone.now()
        updated = queryset.update(status=PremiumSubscription.ACTIVE, start_date=now)
        self.message_user(request, f'{updated} abonnement(s) activé(s).')
    activate_subscription.short_description = 'Activer les abonnements sélectionnés'
    
    def deactivate_subscription(self, request, queryset):
        """Désactiver les abonnements sélectionnés"""
        updated = queryset.update(status=PremiumSubscription.EXPIRED)
        self.message_user(request, f'{updated} abonnement(s) désactivé(s).')
    deactivate_subscription.short_description = 'Désactiver les abonnements sélectionnés'
    
    def mark_as_paid(self, request, queryset):
        """Marquer comme payé"""
        updated = queryset.update(payment_status=True)
        self.message_user(request, f'{updated} abonnement(s) marqué(s) comme payé(s).')
    mark_as_paid.short_description = 'Marquer comme payé'

admin.site.register(PremiumSubscription, PremiumSubscriptionAdmin)


class ProductBoostRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'vendor', 'status', 'duration_days', 'price', 'payment_status', 'start_date', 'end_date', 'is_active_display', 'created_date')
    list_filter = ('status', 'payment_status', 'created_date', 'duration_days')
    list_display_links = ('id', 'product')
    search_fields = ('product__product_name', 'vendor__user__username', 'vendor__display_name')
    readonly_fields = ('created_date', 'updated_date', 'approved_date')
    list_per_page = 20
    
    fieldsets = (
        ('Informations', {
            'fields': ('vendor', 'product')
        }),
        ('Détails du boost', {
            'fields': ('status', 'duration_days', 'boost_percentage', 'price', 'payment_status', 'start_date', 'end_date')
        }),
        ('Notes administrateur', {
            'fields': ('admin_notes',)
        }),
        ('Dates', {
            'fields': ('created_date', 'updated_date', 'approved_date')
        }),
    )
    
    def is_active_display(self, obj):
        """Affiche si le boost est actif"""
        if obj.is_active():
            return "✓ Actif"
        return "✗ Inactif"
    is_active_display.short_description = 'Statut actuel'
    
    actions = ['approve_boost', 'reject_boost', 'activate_boost', 'mark_as_paid']
    
    def approve_boost(self, request, queryset):
        """Approuver les boosts sélectionnés"""
        now = timezone.now()
        for boost in queryset.filter(status=ProductBoostRequest.PENDING):
            from datetime import timedelta
            boost.status = ProductBoostRequest.APPROVED
            boost.approved_date = now
            boost.start_date = now
            boost.end_date = now + timedelta(days=boost.duration_days)
            boost.save()
        self.message_user(request, f'{queryset.filter(status=ProductBoostRequest.PENDING).count()} boost(s) approuvé(s).')
    approve_boost.short_description = 'Approuver les boosts sélectionnés'
    
    def reject_boost(self, request, queryset):
        """Rejeter les boosts sélectionnés"""
        updated = queryset.filter(status=ProductBoostRequest.PENDING).update(status=ProductBoostRequest.REJECTED)
        self.message_user(request, f'{updated} boost(s) rejeté(s).')
    reject_boost.short_description = 'Rejeter les boosts sélectionnés'
    
    def activate_boost(self, request, queryset):
        """Activer les boosts approuvés"""
        now = timezone.now()
        updated = 0
        for boost in queryset.filter(status=ProductBoostRequest.APPROVED):
            from datetime import timedelta
            boost.status = ProductBoostRequest.ACTIVE
            boost.start_date = now
            boost.end_date = now + timedelta(days=boost.duration_days)
            boost.save()
            updated += 1
        self.message_user(request, f'{updated} boost(s) activé(s).')
    activate_boost.short_description = 'Activer les boosts approuvés'
    
    def mark_as_paid(self, request, queryset):
        """Marquer comme payé"""
        updated = queryset.update(payment_status=True)
        self.message_user(request, f'{updated} boost(s) marqué(s) comme payé(s).')
    mark_as_paid.short_description = 'Marquer comme payé'

admin.site.register(ProductBoostRequest, ProductBoostRequestAdmin)


class ProductMessageInline(admin.TabularInline):
    model = ProductMessage
    extra = 0
    readonly_fields = ('created_at', 'read_at')
    fields = ('sender', 'message', 'is_read', 'created_at', 'read_at')


class ProductConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'seller', 'buyer', 'last_message_at', 'unread_count_display')
    list_filter = ('last_message_at',)
    list_display_links = ('id', 'product')
    search_fields = ('product__product_name', 'seller__username', 'buyer__username')
    readonly_fields = ('created_at', 'updated_at', 'last_message_at')
    inlines = [ProductMessageInline]
    list_per_page = 20
    
    def unread_count_display(self, obj):
        """Affiche le nombre de messages non lus pour le vendeur"""
        return obj.get_unread_count_for_seller()
    unread_count_display.short_description = 'Messages non lus (vendeur)'


class ProductMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    list_display_links = ('id',)
    search_fields = ('message', 'sender__username', 'conversation__product__product_name')
    readonly_fields = ('created_at', 'read_at')
    list_per_page = 50

admin.site.register(ProductConversation, ProductConversationAdmin)
admin.site.register(ProductMessage, ProductMessageAdmin)


class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'notification_type', 'title', 'is_read', 'is_resolved', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_resolved', 'created_at')
    list_display_links = ('id', 'title')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at', 'read_at', 'resolved_at')
    list_per_page = 50
    
    fieldsets = (
        ('Informations', {
            'fields': ('notification_type', 'title', 'message')
        }),
        ('Lien', {
            'fields': ('related_object_type', 'related_object_id', 'related_url')
        }),
        ('Statut', {
            'fields': ('is_read', 'is_resolved', 'created_at', 'read_at', 'resolved_at')
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_resolved']
    
    def mark_as_read(self, request, queryset):
        """Marquer les notifications sélectionnées comme lues"""
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notification(s) marquée(s) comme lue(s).')
    mark_as_read.short_description = "Marquer comme lues"
    
    def mark_as_resolved(self, request, queryset):
        """Marquer les notifications sélectionnées comme résolues"""
        updated = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{updated} notification(s) marquée(s) comme résolue(s).')
    mark_as_resolved.short_description = "Marquer comme résolues"

admin.site.register(AdminNotification, AdminNotificationAdmin)