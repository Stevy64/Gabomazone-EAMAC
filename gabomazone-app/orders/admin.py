from django.contrib import admin

# Register your models here.
from .models import Order, OrderDetails, Payment, Coupon, OrderSupplier, OrderDetailsSupplier


class Inline_OrderDetails(admin.StackedInline):
    model = OrderDetails
    readonly_fields = ("order_photo",)
    extra = 0


class Inline_PaymentAdmin(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = ("first_name", 'last_name',
                       'order', 'Email_Address', 'payment_method',)


class OrderAdmin(admin.ModelAdmin):
    #fields = ("","")
    inlines = [Inline_PaymentAdmin, Inline_OrderDetails, ]
    list_display = ('id', 'user', 'order_date', 'coupon', 'sub_total',
                    'discount', 'amount', 'is_finished', 'status')
    list_filter = ('coupon', 'is_finished', 'status')
    list_editable = ("status",)
    list_display_links = ("id",
                          "amount", )
    list_per_page = 10
    search_fields = ('user__username', )


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
                    'order', 'Email_Address', 'payment_method',)
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
    #fields = ("","")
    inlines = [Inline_OrderDetailsSupplier, ]
    list_display = ('id', 'user', 'order_date', 'coupon', 'sub_total',
                    'discount', 'amount', 'is_finished', 'status')
    list_filter = ('coupon', 'is_finished', 'status')
    list_editable = ("status",)
    list_display_links = ("id",
                          "amount", )
    list_per_page = 10
    search_fields = ('user__username', )


admin.site.register(OrderSupplier, OrderAdminSupplier)
