from django.db import models
from django.db.models.signals import pre_save
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from .utils import code_generator, create_shortcode

# Create your models here.


class SuperCategory(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    # parent = models.ForeignKey(
    #     'self', null=True, blank=True, on_delete=models.CASCADE)
    category_image = models.ImageField(
        upload_to='categories/super/imgs/', verbose_name=_("Category Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 120px X 120px"))
    slug = models.SlugField(
        blank=True, null=True,  allow_unicode=True, unique=True, verbose_name=_("Slugfiy"))
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "1.SuperCategory"

    def save(self, *args, **kwargs):

        if not self.slug or self.slug is None or self.slug == "":
            self.slug = slugify(self.name, allow_unicode=True)
            qs_exists = SuperCategory.objects.filter(
                slug=self.slug).exists()
            if qs_exists:
                self.slug = create_shortcode(self)
        # allow_unicode=True for support utf-8 languages
        #self.slug = slugify(title, allow_unicode=True)

        super(SuperCategory, self).save(*args, **kwargs)


# def pre_save_post_receiver(sender, instance, *args, **kwargs):

#     if not instance.slug or instance.slug is None or instance.slug == "":
#         instance.slug = slugify(instance.name, allow_unicode=True)
#         qs_exists = SuperCategory.objects.filter(
#             slug=instance.slug).exists()
#         if qs_exists:
#             instance.slug = create_shortcode(instance)


# pre_save.connect(pre_save_post_receiver, sender=SuperCategory)


class MainCategory(models.Model):
    super_category = models.ForeignKey(
        SuperCategory, on_delete=models.SET_NULL,  blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    category_image = models.ImageField(
        upload_to='categories/main/imgs/', verbose_name=_("Category Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 120px X 120px"))
    slug = models.SlugField(
        blank=True, null=True,  allow_unicode=True, unique=True, verbose_name=_("Slugfiy"))
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "2.MainCategory"

    def save(self, *args, **kwargs):

        if not self.slug or self.slug is None or self.slug == "":
            self.slug = slugify(self.name, allow_unicode=True)
            qs_exists = MainCategory.objects.filter(
                slug=self.slug).exists()
            if qs_exists:
                self.slug = create_shortcode(self)

        super(MainCategory, self).save(*args, **kwargs)


class SubCategory(models.Model):
    main_category = models.ForeignKey(
        MainCategory, on_delete=models.SET_NULL,  blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    category_image = models.ImageField(
        upload_to='categories/sub/imgs/', verbose_name=_("Category Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 120px X 120px"))
    slug = models.SlugField(
        blank=True, null=True,  allow_unicode=True, unique=True, verbose_name=_("Slugfiy"))
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "3.SubCategory"

    def save(self, *args, **kwargs):

        if not self.slug or self.slug is None or self.slug == "":
            self.slug = slugify(self.name, allow_unicode=True)
            qs_exists = SubCategory.objects.filter(
                slug=self.slug).exists()
            if qs_exists:
                self.slug = create_shortcode(self)

        super(SubCategory, self).save(*args, **kwargs)


class MiniCategory(models.Model):
    sub_category = models.ForeignKey(
        SubCategory, on_delete=models.SET_NULL,  blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    category_image = models.ImageField(
        upload_to='categories/mini/imgs/', verbose_name=_("Category Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 120px X 120px"))
    slug = models.SlugField(
        blank=True, null=True,  allow_unicode=True, unique=True, verbose_name=_("Slugfiy"))
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "4.MiniCategory"

    def save(self, *args, **kwargs):

        if not self.slug or self.slug is None or self.slug == "":
            self.slug = slugify(self.name, allow_unicode=True)
            qs_exists = MiniCategory.objects.filter(
                slug=self.slug).exists()
            if qs_exists:
                self.slug = create_shortcode(self)

        super(MiniCategory, self).save(*args, **kwargs)
