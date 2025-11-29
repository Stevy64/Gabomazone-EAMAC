from django.db import models
from categories.models import SubCategory, MainCategory, SuperCategory, MiniCategory
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from .utils import code_generator, create_shortcode
from django.db.models.signals import pre_save

from django.utils.safestring import mark_safe
from django.core import validators
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from io import BytesIO
from PIL import Image
from django.core.files import File
# Create your models here.

try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping

from django.utils.translation import gettext_lazy as _
from django.utils.deconstruct import deconstructible
from ckeditor.fields import RichTextField
from accounts.models import Profile
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User


def compress(image):
    im = Image.open(image)
    # create a BytesIO object
    im_io = BytesIO()
    if im.mode in ("RGBA", "P"):
        im = im.convert("RGB")
    if im.width > 1100 or im.height > 1100:
        out_size = (1100, 1100)
        im.thumbnail(out_size)
    # save image to BytesIO object
    im.save(im_io, format="webp", quality=20, optimize=True)
    # create a django-friendly Files object
    new_image = File(im_io, name=image.name)
    return new_image


class Product(models.Model):
    product_vendor = models.ForeignKey(
        Profile, on_delete=models.CASCADE, verbose_name=_("Product Vendor"), blank=True, null=True,)
    product_name = models.CharField(max_length=150, verbose_name=_("Name"))
    digital_file = models.FileField(
        upload_to='products/files/', verbose_name=_("Digital File"), blank=True, null=True, help_text=_("Please use our recommended allowed extension are zip , rar"), validators=[FileExtensionValidator(allowed_extensions=['zip', 'rar'])])
    # DESCRIPTION
    product_description = models.TextField(verbose_name=_("Short Description"))
    product_image = models.ImageField(
        upload_to='products/imgs/', default='products/product.jpg', max_length=500, verbose_name=_("Product Image"))
    product_minicategor = models.ForeignKey(
        MiniCategory, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Mini Category"))

    product_subcategory = models.ForeignKey(
        SubCategory, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Sub Category"))

    product_maincategory = models.ForeignKey(
        MainCategory, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Main Category"))

    product_supercategory = models.ForeignKey(
        SuperCategory, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Super Category"))
    content = RichTextField(blank=True, null=True,
                            verbose_name=_("Full Description"))
    PRDPrice = models.FloatField(
        blank=True, null=True, verbose_name=_("Price"))
    PRDDiscountPrice = models.FloatField(default=0,
                                         blank=True, null=True,  verbose_name=_("Discount"))

    additional_image_1 = models.ImageField(
        upload_to='products/imgs/product_imgs/', blank=True, null=True, max_length=500, verbose_name=_("Additional  Image_1"), )

    additional_image_2 = models.ImageField(
        upload_to='products/imgs/product_imgs/', blank=True, null=True, max_length=500, verbose_name=_("Additional  Image_2"), )

    additional_image_3 = models.ImageField(
        upload_to='products/imgs/product_imgs/', blank=True, null=True, max_length=500, verbose_name=_("Additional  Image_3"), )

    additional_image_4 = models.ImageField(
        upload_to='products/imgs/product_imgs/', blank=True, null=True, max_length=500, verbose_name=_("Additional  Image_4"),)

    # PRDCost = models.FloatField(verbose_name=_("Cost"), blank=True, null=True)

    # Dimensions = models.CharField(
    #     max_length=100, blank=True, null=True,  verbose_name=_("Dimensions"))

    feedbak_average = models.PositiveIntegerField(default=0,
                                                  blank=True, null=True, verbose_name=_("Feedbak average"))
    feedbak_number = models.PositiveIntegerField(
        default=0, blank=True, null=True, verbose_name=_("Feedbak number"))

    # start_1 = models.PositiveIntegerField(default=0,
    #     blank=True, null=True, verbose_name=_("start_1"))
    # start_2 = models.PositiveIntegerField(default=0,
    #     blank=True, null=True, verbose_name=_("start_2"))
    # start_3 = models.PositiveIntegerField(default=0,
    #     blank=True, null=True, verbose_name=_("start_3"))
    # start_4 = models.PositiveIntegerField(default=0,
    #     blank=True, null=True, verbose_name=_("start_4"))
    # start_5 = models.PositiveIntegerField(default=0,
    #     blank=True, null=True, verbose_name=_("start_5"))

    width = models.FloatField(
        blank=True, null=True, verbose_name=_("Width"))
    height = models.FloatField(
        blank=True, null=True, verbose_name=_("Height"))

    PRDProduct_condition = models.PositiveIntegerField(
        default=0, blank=True, null=True, verbose_name=_("Neuf"))

    # PRDWeight_oz = models.DecimalField(default=0,
    #                                    max_digits=10, decimal_places=3,  blank=True, null=True,  verbose_name=_("SET WEIGHT_OZ"))

    # piece_weight = models.DecimalField(default=0,
    #                                    max_digits=10, decimal_places=3, blank=True, null=True,  verbose_name=_("Piece WEIGHT_GM"))
    # piece_weight_oz = models.DecimalField(default=0,
    #                                       max_digits=10, decimal_places=3,  blank=True, null=True,  verbose_name=_("Piece WEIGHT_OZ"))

    pieces = models.PositiveIntegerField(
        default=0, blank=True, null=True,  verbose_name=_("pieces/set"))

    available = models.PositiveIntegerField(
        default=0, blank=True, null=True, verbose_name=_("available"))

    PRDSKU = models.CharField(
        max_length=100,  blank=True, null=True,  verbose_name=_("SKU"))

    PRDISSale = models.BooleanField(
        default=False,  verbose_name=_("Sale"))

    New = 'New'
    Hot = 'Hot'

    promotional_select = [
        (New, 'New'),
        (Hot, 'Hot'),

    ]
    promotional = models.CharField(
        max_length=13,
        choices=promotional_select,
        default=New, blank=True, null=True,
    )

    # PRDISNew = models.BooleanField(
    #     default=True,  verbose_name=_("New"))
    # PRDISHot = models.BooleanField(
    #     default=False, verbose_name=_("Hot"))

    # PRDISactive = models.BooleanField(default=True, verbose_name=_("Active"))
    Active = True
    Inactive = False

    Status_select = [
        (Active, True),
        (Inactive, False),

    ]
    PRDISactive = models.BooleanField(
        max_length=13,
        choices=Status_select,
        default=True, blank=True, null=True,
    )

    PRDISDeleted = models.BooleanField(
        default=False, verbose_name=_("Product Deleted"))
    PRDtags = models.CharField(
        max_length=100, verbose_name=_("Tags"), blank=True, null=True)

    PRDSlug = models.SlugField(max_length=150,
                               blank=True, null=True, allow_unicode=True, unique=True, verbose_name=_("Slugfiy"))
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)
    __original_product_image_name = None
    __original_additional_image_1_name = None
    __original_additional_image_2_name = None
    __original_additional_image_3_name = None
    __original_additional_image_4_name = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_product_image_name = self.product_image
        self.__original_additional_image_1_name = self.additional_image_1
        self.__original_additional_image_2_name = self.additional_image_2
        self.__original_additional_image_3_name = self.additional_image_3
        self.__original_additional_image_4_name = self.additional_image_4

    class meta:

        ordering = ('-date',)
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.PRDSlug})

    def __str__(self):
        return self.product_name

    def product_photo(self):
        return mark_safe('<img src="{}" width="100" />'.format(self.product_image.url))
    product_photo.short_description = "image"
    product_photo.allow_tags = True

    def preview_image_1(self):
        return mark_safe('<img src="{}" width="100" />'.format(self.additional_image_1.url))
    preview_image_1.short_description = "image 1"
    preview_image_1.allow_tags = True

    def preview_image_2(self):
        return mark_safe('<img src="{}" width="100" />'.format(self.additional_image_2.url))
    preview_image_2.short_description = "image 2"
    preview_image_2.allow_tags = True

    def preview_image_3(self):
        return mark_safe('<img src="{}" width="100" />'.format(self.additional_image_3.url))
    preview_image_3.short_description = "image 3"
    preview_image_3.allow_tags = True

    def preview_image_4(self):
        return mark_safe('<img src="{}" width="100" />'.format(self.additional_image_4.url))
    preview_image_4.short_description = "image 4"
    preview_image_4.allow_tags = True

    def save(self, *args, **kwargs):
        # main image
        if self.product_image != self.__original_product_image_name:

            # call the compress function
            new_image = compress(self.product_image)
            # set self.image to new_image
            self.product_image = new_image

        if self.pk is None and self.product_image:

            # call the compress function
            new_image = compress(self.product_image)
            # set self.image to new_image
            self.product_image = new_image

        # additional_image_1
        if self.additional_image_1 != self.__original_additional_image_1_name:

            # call the compress function
            new_image_1 = compress(self.additional_image_1)
            # set self.image to new_image
            self.additional_image_1 = new_image_1

        if self.pk is None and self.additional_image_1:

            # call the compress function
            new_image_1 = compress(self.additional_image_1)
            # set self.image to new_image
            self.additional_image_1 = new_image_1

        # additional_image_2
        if self.additional_image_2 != self.__original_additional_image_2_name:
            # call the compress function
            new_image_2 = compress(self.additional_image_2)
            # set self.image to new_image
            self.additional_image_2 = new_image_2

        if self.pk is None and self.additional_image_2:
            # call the compress function
            new_image_2 = compress(self.additional_image_2)
            # set self.image to new_image
            self.additional_image_2 = new_image_2

        # additional_image_3
        if self.additional_image_3 != self.__original_additional_image_3_name:
            # call the compress function
            new_image_3 = compress(self.additional_image_3)
            # set self.image to new_image
            self.additional_image_3 = new_image_3

        if self.pk is None and self.additional_image_3:
            # call the compress function
            new_image_3 = compress(self.additional_image_3)
            # set self.image to new_image
            self.additional_image_3 = new_image_3

        # additional_image_4
        if self.additional_image_4 != self.__original_additional_image_4_name:
            # call the compress function
            new_image_4 = compress(self.additional_image_4)
            # set self.image to new_image
            self.additional_image_4 = new_image_4

        if self.pk is None and self.additional_image_4:
            # call the compress function
            new_image_4 = compress(self.additional_image_4)
            # set self.image to new_image
            self.additional_image_4 = new_image_4

        super().save(*args, **kwargs)
        self.__original_product_image_name = self.product_image
        self.__original_additional_image_1_name = self.additional_image_1
        self.__original_additional_image_2_name = self.additional_image_2
        self.__original_additional_image_3_name = self.additional_image_3
        self.__original_additional_image_4_name = self.additional_image_4


def pre_save_post_receiver(sender, instance, *args, **kwargs):
    if not instance.PRDSlug or instance.PRDSlug is None or instance.PRDSlug == "":
        instance.PRDSlug = slugify(instance.product_name, allow_unicode=True)
        qs_exists = Product.objects.filter(PRDSlug=instance.PRDSlug).exists()
        if qs_exists:
            instance.PRDSlug = create_shortcode(instance)


pre_save.connect(pre_save_post_receiver, sender=Product)


class ProductImage(models.Model):
    def upload_file_name(self, filename):
        return f'products/imgs/{self.PRDIProduct.PRDSlug}/'
    PRDIProduct = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name=_("product"))
    PRDIImage = models.ImageField(
        upload_to='products/imgs/product_imgs/', max_length=500,  verbose_name=_("Image"))

    def __str__(self):
        return str(self.PRDIProduct)

    class Meta:
        ordering = ('id',)

    def save(self, *args, **kwargs):
        # call the compress function
        new_image = compress(self.PRDIImage)
        # set self.image to new_image
        self.PRDIImage = new_image
        # save
        super().save(*args, **kwargs)


class ProductRating(models.Model):
    PRDIProduct = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name=_("Product"), blank=True, null=True,)
    vendor = models.ForeignKey(
        Profile, on_delete=models.CASCADE, verbose_name=_("Supplier"), related_name='vendor', blank=True, null=True,)
    rate = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], blank=True, null=True,)
    client_name = models.ForeignKey(
        Profile, on_delete=models.CASCADE, blank=True, null=True, related_name='Customer', verbose_name=_("Client"))
    client_comment = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Comment"))
    active = models.BooleanField(default=True, )
    rating_date = models.DateTimeField(
        auto_now_add=True, blank=True, null=True,)
    rating_update = models.DateTimeField(auto_now=True, blank=True, null=True,)

    def __str__(self):
        return str(self.PRDIProduct)


class ProductSize(models.Model):
    PRDIProduct = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name=_("Product"), blank=True, null=True,)

    name_variation = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Name Variation"), help_text=_("Please enter only one of these values 'XXS ,XS , S , M , L , XL . XXL' "))

    date = models.DateTimeField(
        auto_now_add=True, blank=True, null=True,)
    update = models.DateTimeField(auto_now=True, blank=True, null=True,)

    def __str__(self):
        return str(self.PRDIProduct)


class ProductFavorite(models.Model):
    """Modèle pour gérer les favoris/likes des produits"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name=_("Product"), related_name='favorites')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("User"), blank=True, null=True, related_name='product_favorites')
    session_key = models.CharField(
        max_length=40, blank=True, null=True, verbose_name=_("Session Key"), help_text=_("Pour les utilisateurs non authentifiés"))
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        unique_together = [['product', 'user'], ['product', 'session_key']]
        verbose_name = _("Product Favorite")
        verbose_name_plural = _("Product Favorites")

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.product.product_name}"
        return f"Session {self.session_key} - {self.product.product_name}"