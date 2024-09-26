from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.

class Newsletter (models.Model):

    email = models.EmailField()
    created_At = models.DateTimeField(auto_now_add=True)
    subscribed = models.BooleanField(
        default=True,  verbose_name=_("Subscribed"))

    def __str__(self):
        return 'id: {} email: {}.'.format(self.id, self.email)

    class Meta:
        ordering = ('-created_At',)

        verbose_name = _("News letter")
        verbose_name_plural = _("News letters")