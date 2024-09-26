from django.contrib import admin
from .models import Newsletter
# Register your models here.

class NewsletterAdmin(admin.ModelAdmin):
    #fields = ("","")
    # inlines = [ ]
    list_display = ('id', 'email', 'created_At', 'subscribed')
    # list_filter = ()
    # list_editable = ( )
    list_display_links = ("id",)
    list_per_page = 10
    search_fields = ('email',)


admin.site.register(Newsletter, NewsletterAdmin)