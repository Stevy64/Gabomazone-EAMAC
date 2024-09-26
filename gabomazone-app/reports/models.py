from django.db import models
from django.utils.translation import gettext_lazy as _
import datetime
from blog.models import Post
from django.contrib.auth.models import User
# Create your models here.

class PostView(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,blank=True , null=True, )
    ip = models.CharField(max_length=50, blank=True , null=True)
    session = models.CharField(max_length=200,blank=True , null=True)
    referral = models.CharField(max_length=500,blank=True , null=True)
    user_agent = models.CharField(max_length=500,blank=True , null=True)
    # Accessing user agent's browser attributes
    user_agent_browser  = models.CharField(max_length=500,blank=True , null=True)
    # Operating System properties
    user_agent_os = models.CharField(max_length=500,blank=True , null=True)
    # Device properties
    user_agent_device = models.CharField(max_length=500,blank=True , null=True)

    is_mobile = models.BooleanField(default=False,blank=True , null=True)
    is_tablet  = models.BooleanField(default=False,blank=True , null=True)
    is_touch_capable  = models.BooleanField(default=False,blank=True , null=True)
    is_pc  = models.BooleanField(default=False,blank=True , null=True)
    is_bot = models.BooleanField(default=False,blank=True , null=True)

    created = models.DateField(auto_now_add=False, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)
    
    def __str__(self):
        return str(self.ip)


class PostReport(models.Model):

    impressions = models.IntegerField(default=0 ,blank=True , null=True)

    created = models.DateField(auto_now_add=False, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True , null=True)
    date_update = models.DateTimeField(auto_now=True , blank=True , null=True)
    
    publisher = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, blank=True, null=True)
   

    # def __str__(self):
    #     return f"{self.publisher}-{self.revenues}$ - {self.date}"

    # def get_absolute_url(self):

     #   return '/link/{}'.format(self.slug)

        # return reverse('urlpast:note_detail',kwargs={'slug':self.note_slug})

    class Meta:
        ordering = ('-date',)                       