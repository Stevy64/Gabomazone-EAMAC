from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import Profile
# Create your models here.


class Carousel(models.Model):
    CARImage = models.ImageField(
        upload_to='carousel/', verbose_name=_("Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 1372px X 830px"))
    CARtitle = models.CharField(
        max_length=100, verbose_name=_("Title"), blank=True, null=True)

    CARURL = models.URLField(blank=True, null=True)

    class meta:
        verbose_name = _("Carousel")
        verbose_name_plural = _("Carousels")

    def __str__(self):
        return self.CARtitle


class HomeAdSidebar(models.Model):
    ad_mage = models.ImageField(
        upload_to='ads/sidebar/', verbose_name=_("Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 760px x 596px, 250 KB MAX"))
    ad_title = models.CharField(
        max_length=100, verbose_name=_("Title"), blank=True, null=True)

    ad_URL = models.URLField(blank=True, null=True)

    Left = 'Left'
    Right = 'Right'
    image_position_select = [
        (Left, 'Left'),
        (Right, 'Right'),
    ]
    image_position = models.CharField(
        max_length=13,
        choices=image_position_select,
        default=Left,
    )

    class meta:
        verbose_name = _("Home Ad Sidebar")
        verbose_name_plural = _("Home Ads Sidebar")

    def __str__(self):
        return self.ad_title


class HomeAdMiddlebar(models.Model):
    ad_mage = models.ImageField(
        upload_to='ads/middlebar/', verbose_name=_("Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 768px x 450px, 250 KB MAX"))
    ad_title = models.CharField(
        max_length=100, verbose_name=_("Title"), blank=True, null=True)

    ad_URL = models.URLField(blank=True, null=True)

    Right = 'Right'
    image_position_select = [

        (Right, 'Right'),
    ]
    image_position = models.CharField(
        max_length=13,
        choices=image_position_select,
        default=Right,
    )

    class meta:
        verbose_name = _("Home Ad Middlebar")
        verbose_name_plural = _("Home Ads Middlebar")

    def __str__(self):
        return self.ad_title


class HomeAdSupplier(models.Model):
    ad_mage = models.ImageField(
        upload_to='ads/suppliers/', verbose_name=_("Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 756px x 332px, 250 KB MAX"))
    ad_title = models.CharField(
        max_length=100, verbose_name=_("Title"), blank=True, null=True)

    ad_URL = models.URLField(verbose_name=_("Supplier"), blank=True, null=True)

    Left = 'Left'
    image_position_select = [

        (Left, 'Left'),
    ]
    image_position = models.CharField(
        max_length=13,
        choices=image_position_select,
        default=Left,
    )

    class meta:
        verbose_name = _("Home Ad Supplier")
        verbose_name_plural = _("Home Ads Suppliers")

    def __str__(self):
        return self.ad_title


class HomeAdDaily(models.Model):
    ad_mage = models.ImageField(
        upload_to='ads/daily/', verbose_name=_("Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 540px x 769px, 250 KB MAX"))
    ad_title = models.CharField(
        max_length=100, verbose_name=_("Title"), blank=True, null=True)

    ad_URL = models.URLField(blank=True, null=True)

    Right = 'Right'
    image_position_select = [

        (Right, 'Right'),
    ]
    image_position = models.CharField(
        max_length=13,
        choices=image_position_select,
        default=Right,
    )

    class meta:
        verbose_name = _("Home Ad Daily")
        verbose_name_plural = _("Home Ads Daily")

    def __str__(self):
        return self.ad_title


class HomeAdDealTime(models.Model):
    ad_mage = models.ImageField(
        upload_to='ads/deal-time/', verbose_name=_("Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 568px x 503px, 250 KB MAX"))
    ad_title = models.CharField(
        max_length=100, verbose_name=_("Title"), blank=True, null=True)
    supplier = models.ForeignKey(
        Profile, on_delete=models.CASCADE, verbose_name=_("Supplier"))
    supplier_URL = models.URLField(blank=True, null=True,
                             verbose_name=_("supplier URL"))    
    ad_URL = models.URLField(blank=True, null=True,
                             verbose_name=_("Product URL"))
    PRDPrice = models.FloatField(
        blank=True, null=True, verbose_name=_("Price"))

    PRDDiscountPrice = models.FloatField(
        blank=True, null=True,  verbose_name=_("Discount"))

    PRDdealtime = models.DateTimeField(
        verbose_name=_("Deal Time"), blank=True, null=True)

    class meta:
        verbose_name = _("Home Ad Daily")
        verbose_name_plural = _("Home Ads Daily")

    def __str__(self):
        return self.ad_title


class VendorDetailsAdImage(models.Model):
    ad_mage = models.ImageField(
        upload_to='ads/vendor-page/', verbose_name=_("Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 360px x 250px, 250 KB MAX"))

    ad_URL = models.URLField(blank=True, null=True,
                             verbose_name=_("Product URL"))

    class meta:
        verbose_name = _("Vendor Details Ad Image")
        verbose_name_plural = _("Vendors Details Ad Image")

    def __str__(self):
        return str(self.id)


class ShopAdSidebar(models.Model):
    ad_mage = models.ImageField(
        upload_to='ads/shop-ad/', verbose_name=_("Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 1024px x 1076px, 250 KB MAX"))
    ad_title = models.CharField(
        max_length=100, verbose_name=_("Title"), blank=True, null=True)
    supplier = models.ForeignKey(
        Profile, on_delete=models.CASCADE, verbose_name=_("Supplier"))

    ad_URL = models.URLField(blank=True, null=True)

    Right = 'Right'
    image_position_select = [

        (Right, 'Right'),
    ]
    image_position = models.CharField(
        max_length=13,
        choices=image_position_select,
        default=Right,
    )

    class meta:
        verbose_name = _("Shop Ad Sidebar")
        verbose_name_plural = _("Shop Ads Sidebar")

    def __str__(self):
        return self.ad_title


class HotDealAd(models.Model):
    ad_mage = models.ImageField(
        upload_to='ads/hot-deal-ad/', verbose_name=_("Image"), blank=True, null=True, help_text=_("Please use our recommended dimensions: 508px x 332px, 250 KB MAX"))
    rate = models.PositiveIntegerField(
        default=0, blank=True, null=True,  verbose_name=_("Discount Percentage"))

    ad_URL = models.URLField(blank=True, null=True)

    Right = 'Right'
    image_position_select = [

        (Right, 'Right'),
    ]
    image_position = models.CharField(
        max_length=13,
        choices=image_position_select,
        default=Right,
    )

    class meta:
        verbose_name = _("Hot Deal Ad")
        verbose_name_plural = _("Hot Deal Ads")

    def __str__(self):
        return str(self.rate)



class HeadTextAd(models.Model):
    ad_title = models.CharField(
        max_length=40, verbose_name=_("Title"), blank=True, null=True)
    ad_URL = models.URLField(blank=True, null=True)
    class meta:
        verbose_name = _("Head Text Ad")
        verbose_name_plural = _("Head Text Ads")

    def __str__(self):
        return str(self.id)