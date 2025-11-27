from django.contrib import admin
from .models import VendorPayments
from accounts.models import BankAccount
# Register your models here.
# class Inline_BankAccount(admin.StackedInline):
#     model = BankAccount
#     # readonly_fields = ("",)
#     extra = 0
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

admin.site.register(VendorPayments,VendorPaymentsAdmin)