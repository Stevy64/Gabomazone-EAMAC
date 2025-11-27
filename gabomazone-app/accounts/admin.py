from django.contrib import admin
from .models import Profile,BankAccount ,SocialLink
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



class BankAccountAdmin(admin.ModelAdmin):
    # inlines = [Inline_ProductImage, Inline_ProductAlternative]
    fields = ("vendor_profile","bank_name", "account_number",  "swift_code",
              "account_name", "country","paypal_email","description",)
    list_display = ("id", "vendor_profile", "bank_name","account_number",
                    "swift_code", "account_name","country","paypal_email",)
    list_display_links = ("id", "bank_name", "paypal_email")

    search_fields = ("account_name", )
    list_per_page = 10

class SocialLinkAdmin(admin.ModelAdmin):
    # inlines = [Inline_ProductImage, Inline_ProductAlternative]
    fields = ("vendor_profile","facebook", "twitter",  "instagram",
              "pinterest",)
    list_display = ("id", "vendor_profile", "facebook","twitter",
                    "instagram", "pinterest",)
    list_display_links = ("id", "vendor_profile", )
    

    search_fields = ("id", )
    list_per_page = 10    

admin.site.register(Profile,ProfileAdmin)
admin.site.register(BankAccount,BankAccountAdmin)
admin.site.register(SocialLink,SocialLinkAdmin)