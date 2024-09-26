from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save
from .utils import code_generator, create_shortcode
from categories.models import SuperCategory
from ckeditor.fields import RichTextField
from accounts.models import Profile
# Create your models here.


class Post(models.Model):
    title = models.CharField(max_length=500)
    content = RichTextField(blank=True, null=True,
                            verbose_name=_("Content"))                      
    post_date = models.DateTimeField(default=timezone.now)
    post_update = models.DateTimeField(auto_now=True)
    post_supercategory = models.ForeignKey(
        SuperCategory, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Super Category"))
    author = models.ForeignKey(Profile, on_delete=models.CASCADE , related_name="author")
    # publisher = models.ForeignKey(
    #     User, on_delete=models.CASCADE, blank=True, null=True , related_name="publisher")
    post_image = models.ImageField(
        upload_to='blog/posts/', verbose_name=_("Post Image"), blank=True, null=True)
    views = models.IntegerField(default=0 ,  blank=True, null=True)    
    posttags = models.CharField(
        max_length=500, verbose_name=_("Tags"), blank=True, null=True)
    post_Slug = models.SlugField(max_length=500,
        blank=True, null=True, allow_unicode=True, unique=True, verbose_name=_("Slugfiy"))

    def __str__(self):

        return str(self.title)

    # def save(self, *args, **kwargs):
    #     if not self.post_Slug:
    #         self.post_Slug = slugify(self.title)
    #     super(Post, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:postdetail', kwargs={'slug': self.post_Slug})

    # def get_absolute_url(self):
    #     # return 'detail/{}'.format(self.pk)
    #     return reverse('blog:postdetail', args=[self.pk])

    class Meta:
        ordering = ('-post_date',)


def pre_save_post_receiver(sender, instance, *args, **kwargs):

    if not instance.post_Slug or instance.post_Slug is None or instance.post_Slug == "":
        instance.post_Slug = slugify(instance.title , allow_unicode=True)
        qs_exists = Post.objects.filter(post_Slug=instance.post_Slug).exists()
        if qs_exists:
            instance.post_Slug = create_shortcode(instance)


pre_save.connect(pre_save_post_receiver, sender=Post)


class Comment (models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    body = models.TextField(verbose_name='Enter Comment')
    comment_date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments')
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, blank=True, null=True)    

    def __str__(self):
        return 'Commented {} on {}.'.format(self.name, self.post)

    class Meta:
        ordering = ('-comment_date',)



