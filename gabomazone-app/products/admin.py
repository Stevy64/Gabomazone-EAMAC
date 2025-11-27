from django.contrib import admin
from .models import Product, ProductImage, ProductRating, ProductSize
# Register your models here.


class Inline_ProductSize(admin.StackedInline):
    model = ProductSize
    extra = 1
    fields = ("name_variation",)


class ProductAdmin(admin.ModelAdmin):
    inlines = [Inline_ProductSize]
    fields = ("product_vendor",  "product_name", "product_description", "digital_file", ("product_photo", "product_image"),
              ("product_supercategory", "product_maincategory",
               "product_subcategory", "product_minicategor"), "content",
              ("PRDPrice", "PRDDiscountPrice", ),
              ("preview_image_1", "additional_image_1"),
              ("preview_image_2", "additional_image_2"),
              ("preview_image_3", "additional_image_3"),
              ("preview_image_4", "additional_image_4"),
              ("feedbak_average", "feedbak_number"),
              ("width", "height", "PRDWeight", "pieces", "available", "PRDSKU"),
              ("PRDISSale", "promotional"),
              ("PRDISactive", "PRDISDeleted"),
              ("PRDtags", "PRDSlug",),
              )
    list_display = ("id", "product_photo", "product_name",
                    "product_vendor", "PRDPrice", "available", "PRDISDeleted")
    list_display_links = ("id", "product_name",)
    # list_editable = ("PRDISactive",)
    # list_filter = ("PRDCategory", "PRDISactive",
    #                "PRDISdeal", "PRDISNew", "PRDISSale")
    # search_fields = ("PRDName", "PRDPrice")
    list_per_page = 10
    readonly_fields = ('product_photo', "preview_image_1",
                       "preview_image_2", "preview_image_3", "preview_image_4",)


class RatingAdmin(admin.ModelAdmin):
    # inlines = [Inline_ProductImage, Inline_ProductAlternative]
    fields = ("PRDIProduct", "vendor", "rate",  "client_name",
              "client_comment", "active")
    list_display = ("id", "PRDIProduct", "vendor", "rate",
                    "client_name", "client_comment", "active")
    list_display_links = ("id", "rate", "client_comment")

    search_fields = ("client_comment", )
    list_per_page = 10


admin.site.register(Product, ProductAdmin)
# admin.site.register(ProductImage)
admin.site.register(ProductRating, RatingAdmin)
# admin.site.register(ProductSize)
