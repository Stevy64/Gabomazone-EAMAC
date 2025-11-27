from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from .utils import code_generator, create_shortcode
from ckeditor.fields import RichTextField
# Create your models here.
class PagesList(models.Model):
    name = models.CharField(max_length=150 , verbose_name=_("Page Name"))
    content = RichTextField(blank=True, null=True,
                            verbose_name=_("Content"))  
    slug = models.SlugField(
        blank=True, null=True,  allow_unicode=True, unique=True, verbose_name=_("Slugfiy"))
    active = models.BooleanField(default=True)    
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return 'Page Name: {}'.format(self.name)

    class Meta:
        ordering = ('id',)

        verbose_name = _("Pages List")
        verbose_name_plural = _("Pages List")

    def save(self, *args, **kwargs):

        if not self.slug or self.slug is None or self.slug == "":
            self.slug = slugify(self.name, allow_unicode=True)
            qs_exists = PagesList.objects.filter(
                slug=self.slug).exists()
            if qs_exists:
                self.slug = create_shortcode(self)

        super(PagesList, self).save(*args, **kwargs)
    