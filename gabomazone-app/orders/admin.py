from django.contrib import admin
from django.utils.html import format_html

# Register your models here.
from .models import Order, OrderDetails, Payment, Coupon, OrderSupplier, OrderDetailsSupplier, B2CDeliveryVerification


class PaymentMethodLifecycleFilter(admin.SimpleListFilter):
    title = "Méthode paiement (cycle)"
    parameter_name = "cycle_payment_method"

    def lookups(self, request, model_admin):
        values = (
            Payment.objects.exclude(payment_method__isnull=True)
            .exclude(payment_method__exact="")
            .values_list("payment_method", flat=True)
            .distinct()
            .order_by("payment_method")
        )
        return [(v, v) for v in values]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(payment__payment_method=self.value())
        return queryset


class DeliveryTraceabilityStatusFilter(admin.SimpleListFilter):
    title = "Statut traçabilité livraison"
    parameter_name = "delivery_traceability_status"

    def lookups(self, request, model_admin):
        return B2CDeliveryVerification.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            if queryset.model is OrderSupplier:
                return queryset.filter(order__b2c_delivery_verification__status=self.value())
            return queryset.filter(b2c_delivery_verification__status=self.value())
        return queryset


class DeliveryCodesProgressFilter(admin.SimpleListFilter):
    title = "Validation codes (V/C)"
    parameter_name = "delivery_codes_progress"

    def lookups(self, request, model_admin):
        return (
            ("both", "Vendeur + Client validés"),
            ("seller_only", "Vendeur validé seulement"),
            ("buyer_only", "Client validé seulement"),
            ("none", "Aucun code validé"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "both":
            return queryset.filter(
                b2c_delivery_verification__seller_code_verified=True,
                b2c_delivery_verification__buyer_code_verified=True,
            )
        if value == "seller_only":
            return queryset.filter(
                b2c_delivery_verification__seller_code_verified=True,
                b2c_delivery_verification__buyer_code_verified=False,
            )
        if value == "buyer_only":
            return queryset.filter(
                b2c_delivery_verification__seller_code_verified=False,
                b2c_delivery_verification__buyer_code_verified=True,
            )
        if value == "none":
            return queryset.filter(
                b2c_delivery_verification__seller_code_verified=False,
                b2c_delivery_verification__buyer_code_verified=False,
            )
        return queryset


class ActiveDisputeFilter(admin.SimpleListFilter):
    title = "Litige actif"
    parameter_name = "active_dispute"

    def lookups(self, request, model_admin):
        return (("yes", "Oui"), ("no", "Non"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            if queryset.model is OrderSupplier:
                return queryset.filter(order__b2c_delivery_verification__status=B2CDeliveryVerification.DISPUTED)
            return queryset.filter(b2c_delivery_verification__status=B2CDeliveryVerification.DISPUTED)
        if value == "no":
            if queryset.model is OrderSupplier:
                return queryset.exclude(order__b2c_delivery_verification__status=B2CDeliveryVerification.DISPUTED)
            return queryset.exclude(b2c_delivery_verification__status=B2CDeliveryVerification.DISPUTED)
        return queryset


class Inline_OrderDetails(admin.StackedInline):
    model = OrderDetails
    readonly_fields = ("order_photo",)
    extra = 0


class Inline_PaymentAdmin(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = ("first_name", 'last_name',
                       'order', 'Email_Address', 'payment_method',)


class Inline_B2CDeliveryVerification(admin.StackedInline):
    model = B2CDeliveryVerification
    extra = 0
    max_num = 1
    readonly_fields = ('seller_code', 'buyer_code', 'created_at', 'completed_at',
                       'seller_code_verified_at', 'buyer_code_verified_at')


class OrderAdmin(admin.ModelAdmin):
    inlines = [Inline_PaymentAdmin, Inline_OrderDetails, Inline_B2CDeliveryVerification]
    list_display = (
        'id',
        'order_date',
        'store_count',
        'user',
        'vendor_names',
        'status',
        'is_finished',
        'payment_method_display',
        'delivery_verification_status',
        'delivery_codes_progress',
        'is_disputed',
        'amount',
    )
    list_filter = (
        "status",
        "is_finished",
        "coupon",
        PaymentMethodLifecycleFilter,
        DeliveryTraceabilityStatusFilter,
        DeliveryCodesProgressFilter,
        ActiveDisputeFilter,
    )
    list_editable = ("status",)
    list_display_links = ("id", "amount")
    list_per_page = 10
    list_select_related = ('user', 'coupon')
    search_fields = (
        'id',
        'tracking_no',
        'user__username',
        'user__email',
        'email_client',
        'ordersupplier__vendor__shop_name',
        'ordersupplier__vendor__company_name',
    )

    readonly_fields = ('lifecycle_traceability',)
    fieldsets = (
        ('Commande', {
            'fields': (
                'user', 'email_client', 'order_date', 'date_update',
                'status', 'is_finished', 'tracking_no',
            )
        }),
        ('Montants', {
            'fields': ('sub_total', 'discount', 'shipping', 'amount', 'weight', 'coupon'),
        }),
        ('Traçabilité cycle de vie', {
            'classes': ('collapse',),
            'fields': ('lifecycle_traceability',),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            'ordersupplier_set__vendor',
            'payment_set',
            'b2c_delivery_verification',
        )

    @admin.display(description='Nb magasins')
    def store_count(self, obj):
        return obj.ordersupplier_set.count()

    @admin.display(description='Magasin(s)')
    def vendor_names(self, obj):
        names = []
        for order_supplier in obj.ordersupplier_set.all():
            vendor = order_supplier.vendor
            if not vendor:
                continue
            label = vendor.shop_name or vendor.company_name or (vendor.user.username if vendor.user else None)
            if label:
                names.append(label)
        if not names:
            return "-"
        return ", ".join(dict.fromkeys(names))

    @admin.display(description='Méthode paiement')
    def payment_method_display(self, obj):
        payment = obj.payment_set.first()
        return payment.payment_method if payment else "-"

    @admin.display(description='Statut traçabilité livraison')
    def delivery_verification_status(self, obj):
        verification = getattr(obj, 'b2c_delivery_verification', None)
        if not verification:
            return "-"
        return verification.get_status_display()

    @admin.display(description='Codes validés (V/C)')
    def delivery_codes_progress(self, obj):
        verification = getattr(obj, 'b2c_delivery_verification', None)
        if not verification:
            return "-"
        seller_ok = "OK" if verification.seller_code_verified else "KO"
        buyer_ok = "OK" if verification.buyer_code_verified else "KO"
        return f"{seller_ok} / {buyer_ok}"

    @admin.display(description='Litige actif')
    def is_disputed(self, obj):
        verification = getattr(obj, 'b2c_delivery_verification', None)
        return bool(verification and verification.status == B2CDeliveryVerification.DISPUTED)

    @admin.display(description="Traçabilité complète")
    def lifecycle_traceability(self, obj):
        payment = obj.payment_set.first()
        verification = getattr(obj, 'b2c_delivery_verification', None)
        stores = self.vendor_names(obj)
        payment_label = payment.payment_method if payment else "Non renseigné"
        payment_contact = payment.Email_Address if payment else (obj.email_client or "Non renseigné")
        verification_status = verification.get_status_display() if verification else "Non démarrée"
        seller_code_at = verification.seller_code_verified_at.strftime('%d/%m/%Y %H:%M') if verification and verification.seller_code_verified_at else "-"
        buyer_code_at = verification.buyer_code_verified_at.strftime('%d/%m/%Y %H:%M') if verification and verification.buyer_code_verified_at else "-"
        completed_at = verification.completed_at.strftime('%d/%m/%Y %H:%M') if verification and verification.completed_at else "-"
        dispute = "Oui" if verification and verification.status == B2CDeliveryVerification.DISPUTED else "Non"

        return format_html(
            "<ul style='margin:0; padding-left:18px;'>"
            "<li><strong>Soumission:</strong> {order_date}</li>"
            "<li><strong>Validation commande:</strong> {status} (terminée: {is_finished})</li>"
            "<li><strong>Magasin(s):</strong> {stores}</li>"
            "<li><strong>Paiement:</strong> {payment_method} ({payment_contact})</li>"
            "<li><strong>Vérification livraison:</strong> {verification_status}</li>"
            "<li><strong>Code vendeur vérifié:</strong> {seller_code_at}</li>"
            "<li><strong>Code client vérifié:</strong> {buyer_code_at}</li>"
            "<li><strong>Clôture:</strong> {completed_at}</li>"
            "<li><strong>Litige:</strong> {dispute}</li>"
            "<li><strong>Point de retrait:</strong> N/A B2C (livraison standard)</li>"
            "</ul>",
            order_date=obj.order_date.strftime('%d/%m/%Y %H:%M'),
            status=obj.status,
            is_finished="Oui" if obj.is_finished else "Non",
            stores=stores,
            payment_method=payment_label,
            payment_contact=payment_contact,
            verification_status=verification_status,
            seller_code_at=seller_code_at,
            buyer_code_at=buyer_code_at,
            completed_at=completed_at,
            dispute=dispute,
        )


class OrderDetailsAdmin(admin.ModelAdmin):
    #fields = ("","")
    list_display = ('id', "order_photo", 'product',
                    'order', 'price', 'quantity',)
    list_filter = ('order', )
    search_fields = ("order__id", )
    list_per_page = 10
    list_display_links = ("product",)


class CouponAdmin(admin.ModelAdmin):
    #fields = ("","")
    list_display = ('id', 'code', 'valid_form',
                    'valid_to', 'discount', 'active')
    list_filter = ('id', 'code', 'valid_form',
                   'valid_to', 'discount', 'active')
    list_per_page = 10


class PaymentAdmin(admin.ModelAdmin):
    #fields = ("","")
    list_display = ("first_name", 'last_name',
                    'order', 'Email_Address', 'payment_method', 'service_fee_amount')
    list_filter = ('order', )
    search_fields = ("order__id", )
    list_per_page = 10
    list_display_links = ("first_name", 'payment_method',)


admin.site.register(Order, OrderAdmin)
# admin.site.register(OrderDetails, OrderDetailsAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Coupon, CouponAdmin)


class Inline_OrderDetailsSupplier(admin.StackedInline):
    model = OrderDetailsSupplier
    #readonly_fields = ("order_supplier",)
    extra = 0


# class Inline_PaymentAdminSupplier(admin.StackedInline):
#     model = Payment
#     extra = 0
#     readonly_fields = ("first_name", 'last_name',
#                        'order_supplier', 'Email_Address', 'payment_method',)


class OrderAdminSupplier(admin.ModelAdmin):
    inlines = [Inline_OrderDetailsSupplier, ]
    list_display = (
        'id',
        'order_date',
        'vendor',
        'user',
        'status',
        'is_finished',
        'amount',
        'parent_order_id',
        'parent_delivery_status',
    )
    list_filter = (
        'vendor',
        'status',
        'is_finished',
        'coupon',
        DeliveryTraceabilityStatusFilter,
        ActiveDisputeFilter,
    )
    list_editable = ("status",)
    list_display_links = ("id", "amount")
    list_per_page = 10
    list_select_related = ('user', 'vendor', 'order')
    search_fields = (
        'id',
        'order__id',
        'user__username',
        'user__email',
        'email_client',
        'vendor__shop_name',
        'vendor__company_name',
    )

    @admin.display(description='Commande cycle (ID)')
    def parent_order_id(self, obj):
        return obj.order_id or "-"

    @admin.display(description='Traçabilité livraison')
    def parent_delivery_status(self, obj):
        order = obj.order
        if not order:
            return "-"
        verification = getattr(order, 'b2c_delivery_verification', None)
        if not verification:
            return "-"
        return verification.get_status_display()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('order__b2c_delivery_verification')


admin.site.register(OrderSupplier, OrderAdminSupplier)


class B2CDeliveryVerificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'seller_code_verified', 'buyer_code_verified', 'status', 'created_at')
    list_filter = ('status', 'seller_code_verified', 'buyer_code_verified')
    readonly_fields = ('seller_code', 'buyer_code', 'created_at', 'completed_at',
                      'seller_code_verified_at', 'buyer_code_verified_at')
    search_fields = ('order__id',)


admin.site.register(B2CDeliveryVerification, B2CDeliveryVerificationAdmin)
