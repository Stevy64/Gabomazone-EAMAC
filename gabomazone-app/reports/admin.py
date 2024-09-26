from django.contrib import admin
from .models import PostView, PostReport 
# Register your models here.




class PostReportAdmin(admin.ModelAdmin):
    #fields = ("","")
    #inlines = [Inline_PaymentAdmin, Inline_OrderDetails, ]
    list_display = ('id', 'impressions', 'created', 'date',
                    'date_update','post', 'publisher')
    # list_filter = ('coupon', 'is_finished', 'status')
    # list_editable = ("status",)
    # list_display_links = ("id",
    #                       "amount", )
    # list_per_page = 10
    # search_fields = ('user__username', )

class PostViewAdmin(admin.ModelAdmin):
    fields = ( 'post','ip', 'referral', 'user_agent', 'user_agent_browser',
                    'user_agent_os', 'user_agent_device','is_mobile','is_tablet','is_touch_capable','is_pc','is_bot','created' , )
    #inlines = [Inline_PaymentAdmin, Inline_OrderDetails, ]
    list_display = ('id', 'post','ip', 'referral', 'user_agent', 'user_agent_browser',
                    'user_agent_os', 'user_agent_device','is_bot','created')
    readonly_fields = ('date','date_update')                
    # list_filter = ('coupon', 'is_finished', 'status')
    # list_editable = ("status",)
    # list_display_links = ("id",
    #                       "amount", )
    # list_per_page = 10
    # search_fields = ('user__username', )

admin.site.register(PostView , PostViewAdmin)
admin.site.register(PostReport,PostReportAdmin)