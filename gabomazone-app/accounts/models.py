from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from PIL import Image
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from .utils import code_generator, create_shortcode


class Profile(models.Model):
    image = models.ImageField(
        upload_to='profile_pic/', blank=True, null=True, )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, blank=True, null=True, )
    display_name = models.CharField(max_length=100, blank=True, null=True, )
    bio = models.TextField(blank=True, null=True)
    mobile_number = models.CharField(max_length=100, blank=True, null=True, )
    address = models.CharField(max_length=100, blank=True, null=True, )
    city = models.CharField(max_length=100, blank=True, null=True, )
    post_code = models.CharField(max_length=100, blank=True, null=True, )
    country = models.CharField(max_length=100, blank=True, null=True, )
    state = models.CharField(max_length=100, blank=True, null=True, )

    customer = 'customer'
    vendor = 'vendor'
    account_select = [
        (customer, 'customer'),
        (vendor, 'vendor'),
    ]
    status = models.CharField(
        max_length=13,
        choices=account_select,
        default=customer,
        blank=True, null=True,
    )
    admission = models.BooleanField(default=False, verbose_name=_("admission") , blank=True, null=True)
    code = models.CharField(max_length=250, blank=True, null=True)
    recommended_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recommended_by", blank=True, null=True)
    referrals = models.IntegerField(default=0, blank=True, null=True)
    blance = models.FloatField(default=0.00, blank=True, null=True)
    requested = models.FloatField(default=0.00, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)
    slug = models.SlugField(
        blank=True, null=True, allow_unicode=True, unique=True, verbose_name=_("Slugfiy"))

    def __str__(self):
        return self.user.username

    # def save(self, *args, **kwargs):
    #     return super().save(*args, **kwargs)

    def get_recommended_profiles(self):
        qs = Profile.objects.all()
        my_recs = []
        for profile in qs:
            if profile.recommended_by == self.user:
                my_recs.append(profile)
        return my_recs

    def save(self, *args, **kwargs):
        if not self.slug or self.slug is None or self.slug == "":
            self.slug = slugify(self.user.username, allow_unicode=True)
            qs_exists = Profile.objects.filter(
                slug=self.slug).exists()
            if qs_exists:
                self.slug = create_shortcode(self)

        if self.code is None or self.code == "":
            # code = generate_ref_code()
            # self.code = code
            self.code = f'{self.user}'

        # img = Image.open(self.image.path)
        # if img.width > 300 or img.height > 300:
        #     out_size = (300, 300)
        #     img.thumbnail(out_size)
        #     img.save(self.image.path)

        super().save(*args, **kwargs)


def create_profile(sender, **kwargs):
    if kwargs['created']:
        user_profile = Profile.objects.create(
            user=kwargs['instance'], )


post_save.connect(create_profile, sender=User)



class BankAccount(models.Model):
    vendor_profile = models.OneToOneField(
        Profile, on_delete=models.SET_NULL, blank=True, null=True)
    bank_name = models.CharField(max_length=200, blank=True, null=True, )
    account_number = models.CharField(max_length=200, blank=True, null=True, )
    swift_code = models.CharField(max_length=200, blank=True, null=True, )
    account_name = models.CharField(max_length=200, blank=True, null=True, )
    country = models.CharField(max_length=200, blank=True, null=True, )
    paypal_email = models.CharField(max_length=200, blank=True, null=True, )
    description = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    # def __str__(self):
    #      return str(self.account_number)



class SocialLink(models.Model):
    vendor_profile = models.OneToOneField(
        Profile, on_delete=models.SET_NULL, blank=True, null=True)
    facebook = models.CharField(max_length=200, blank=True, null=True, )
    twitter = models.CharField(max_length=200, blank=True, null=True, )
    instagram = models.CharField(max_length=200, blank=True, null=True, )
    pinterest = models.CharField(max_length=200, blank=True, null=True, )
