from django.contrib import admin
from .models import SuperCategory, MainCategory, SubCategory, MiniCategory

# Register your models here.


# class Inline_OrderDetails(admin.StackedInline):
#     model = OrderDetails
#     readonly_fields = ("order_photo",)
#     extra = 0


class Inline_MainCategoryAdmin(admin.StackedInline):
    model = MainCategory
    extra = 0
    #readonly_fields = ("name",)
    list_display = ('id', 'name',)
    list_filter = ('name',)
    list_editable = ("name",)
    list_display_links = ("id", )
    list_per_page = 10
    search_fields = ('name', )


class SuperCategoryAdmin(admin.ModelAdmin):
    #fields = ("","")
    inlines = [Inline_MainCategoryAdmin, ]
    list_display = ('id', 'name',)
    list_filter = ('name',)
    #list_editable = ("name",)
    list_display_links = ("id", )
    list_per_page = 10
    search_fields = ('name', )


class Inline_SubCategoryAdmin(admin.StackedInline):
    model = SubCategory
    extra = 0
    #readonly_fields = ("name",)
    list_display = ('id', 'name',)
    list_filter = ('name',)
    list_editable = ("name",)
    list_display_links = ("id", )
    list_per_page = 10
    search_fields = ('name', )


class MainCategoryAdmin(admin.ModelAdmin):
    #fields = ("","")
    inlines = [Inline_SubCategoryAdmin, ]
    list_display = ('id', 'name',)
    list_filter = ('name',)
    #list_editable = ("name",)
    list_display_links = ("id", )
    list_per_page = 10
    search_fields = ('name', )


class Inline_MiniCategoryAdmin(admin.StackedInline):
    model = MiniCategory
    extra = 0
    #readonly_fields = ("name",)
    list_display = ('id', 'name',)
    list_filter = ('name',)
    list_editable = ("name",)
    list_display_links = ("id", )
    list_per_page = 10
    search_fields = ('name', )


class SubCategoryAdmin(admin.ModelAdmin):
    #fields = ("","")
    inlines = [Inline_MiniCategoryAdmin, ]
    list_display = ('id', 'name',)
    list_filter = ('name',)
    #list_editable = ("name",)
    list_display_links = ("id", )
    list_per_page = 10
    search_fields = ('name', )


admin.site.register(SuperCategory, SuperCategoryAdmin,)
admin.site.register(MainCategory, MainCategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(MiniCategory)
