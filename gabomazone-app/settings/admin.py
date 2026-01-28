from django.contrib import admin
from .models import SocailLinks, ContactInfo, SupportNumber, SiteSetting, HomePageTheme
# Register your models here.


class ContactInfoAdmin(admin.ModelAdmin):
    #fields = ("","")
    # inlines = [ ]
    list_display = ('id', 'description', 'full_address',
                    'phone', 'email', 'Work_time', 'active')
    # list_filter = ()
    list_editable = ('description', 'full_address', 'phone',
                     'email', 'Work_time', 'active')
    list_display_links = ("id",)
    list_per_page = 10
    search_fields = ('full_address', 'phone', 'email', 'Work_time')


class SocaillinksAdmin(admin.ModelAdmin):
    #fields = ("","")
    # inlines = [ ]
    list_display = ('id', 'facebook', 'twitter',
                    'youtube', 'pinterest', 'instagram',)
    # list_filter = ()
    list_editable = ('facebook', 'twitter',
                     'youtube', 'pinterest', 'instagram',)
    list_display_links = ("id",)
    list_per_page = 10
    search_fields = ('facebook', 'twitter',
                     'youtube', 'pinterest', 'instagram',)


class SupportNumberAdmin(admin.ModelAdmin):
    #fields = ("","")
    # inlines = [ ]
    list_display = ('id', 'number', 'Work_time',)
    # list_filter = ()
    list_editable = ('number', 'Work_time',)
    list_display_links = ("id",)
    list_per_page = 10
    search_fields = ('number', 'Work_time', )


class HomePageThemeAdmin(admin.ModelAdmin):
    #fields = ("","")
    # inlines = [ ]
    list_display = ('id', 'page_name', 'active',)
    # list_filter = ()
    list_editable = ('active',)
    list_display_links = ("id",)
    list_per_page = 10
    search_fields = ('page_name',)

admin.site.register(ContactInfo, ContactInfoAdmin)
admin.site.register(SocailLinks, SocaillinksAdmin)
admin.site.register(SupportNumber, SupportNumberAdmin)
admin.site.register(SiteSetting)
admin.site.register(HomePageTheme, HomePageThemeAdmin)
