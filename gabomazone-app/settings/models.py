from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.


class SocailLinks(models.Model):

    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    youtube = models.URLField(blank=True, null=True)
    pinterest = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    date_created = models.DateTimeField(
        auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return 'id: {}'.format(self.id)

    class Meta:
        ordering = ('-date_created',)

        verbose_name = _("Socail links")
        verbose_name_plural = _("Socail links")


class ContactInfo(models.Model):
    description = models.CharField(max_length=150)
    full_address = models.CharField(max_length=500)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    Work_time = models.CharField(max_length=150)
    contact_date = models.DateTimeField(auto_now_add=True)
    map_link = models.URLField(blank=True, null=True)
    active = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return 'id: {} email {}.'.format(self.id, self.email)

    class Meta:
        ordering = ('-contact_date',)

        verbose_name = _("Contact Us")
        verbose_name_plural = _("Contact Us")


class SupportNumber(models.Model):
    number = models.CharField(max_length=150)
    Work_time = models.CharField(max_length=150)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return 'id: {} number {}.'.format(self.id, self.number)

    class Meta:
        ordering = ('id',)

        verbose_name = _("Support Number")
        verbose_name_plural = _("Support Numbers")


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=150, verbose_name=_("Site Name"))
    site_title = models.CharField(max_length=500, verbose_name=_("Site Title"))
    description = models.TextField(
        max_length=500, verbose_name=_("Site Description"))
    site_url = models.URLField(
        blank=True, null=True, verbose_name=_("Site URL"))
    site_logo = models.ImageField(
        upload_to='site_logo/imgs/', blank=True, null=True, max_length=1000, verbose_name=_("Site Logo"), help_text=_("Please use our recommended dimensions: width='215' height='66'"))
    favicon = models.ImageField(
        upload_to='site_logo/imgs/', blank=True, null=True, max_length=1000, verbose_name=_("Site favicon"), help_text=_("Please use our recommended dimensions: width='78' height='60'"))
    login_image = models.ImageField(
        upload_to='site_logo/imgs/', blank=True, null=True, max_length=1000, verbose_name=_("Login screen"), help_text=_("Please use our recommended dimensions: width='768' height='901'"))

    footer_image = models.ImageField(
        upload_to='site_logo/imgs/', blank=True, null=True, max_length=1000, verbose_name=_("Footer Image"), help_text=_("Please use our recommended dimensions: width='978' height='533'"))
    shipping = models.FloatField(
        blank=True, null=True, verbose_name=_("Shipping fee"))
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return 'id: {} site name {}.'.format(self.id, self.site_name)

    class Meta:
        ordering = ('id',)

        verbose_name = _("Site Setting")
        verbose_name_plural = _("Site Settings")

# class StripeSetting(models.Model):
#     stripe_public_key = models.CharField(max_length=150 , verbose_name=_("Stripe Public Key"))
#     stripe_secret_key = models.CharField(max_length=500 , verbose_name=_("Stripe Secret Key"))
#     stripe_webhook_secret   = models.CharField(max_length=500 , verbose_name=_("Stripe Webhook Secret "))
#     domain = models.URLField(blank=True, null=True , verbose_name=_("Your Domain"))


class HomePageTheme(models.Model):
    page_name = models.CharField(max_length=150, verbose_name=_("Page Name"))
    active = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.page_name

    class Meta:
        ordering = ('id',)

        verbose_name = _("Home Page Theme")
        verbose_name_plural = _("Home Pages Theme ")
