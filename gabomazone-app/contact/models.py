from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.
class MessagesList (models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    subject = models.CharField(max_length=150)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        ordering = ('-id',)
            
        verbose_name = _("Message List")
        verbose_name_plural = _("Messages List")

    def __str__(self):
        return str(self.id)