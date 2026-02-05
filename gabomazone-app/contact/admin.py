from django.contrib import admin
from .models import MessagesList
# Register your models here.
class MessagesListAdmin(admin.ModelAdmin):
    #fields = ("","")
    # inlines = [ ]
    list_display = ('id', 'name', 'email',
                    'phone', 'subject', 'date',)
    # list_filter = ()
    # list_editable = ()
    list_display_links = ("id","subject")
    list_per_page = 10
    search_fields = ('name', 'email',
                     'phone', 'subject', )

admin.site.register(MessagesList, MessagesListAdmin)