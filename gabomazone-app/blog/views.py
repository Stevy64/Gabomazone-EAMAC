from random import random
from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
# from django.views.generic import CreateView, UpdateView, DeleteView, View, TemplateView
# from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# from django.http import JsonResponse
from django.contrib import messages
from categories.models import SuperCategory
import datetime
from reports.models import PostReport, PostView
from django_user_agents.utils import get_user_agent
# import requests
from accounts.models import Profile
# Create your views here.


def get_ip(request):
    try:
        x_forward = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forward:
            ip=x_forward.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
    except:
        ip = ""

    return ip

def home(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, 16)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_page)
    context = {
        'title': 'home page',
        'posts': posts,
        'page': page,

    }
    return render(request, 'blog/blog-fullwidth.html', context)



def super_category(request, slug):

    super_category_obj = SuperCategory.objects.get(slug=slug)
    posts = Post.objects.all().filter(post_supercategory = super_category_obj)
    paginator = Paginator(posts, 16)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_page)

    context = {
        "super_category_obj": super_category_obj,
        "slug": slug,
        'posts': posts,
        'page': page,

    }
    return render(request, "blog/blog-category-fullwidth.html", context)  


def post_detail(request, slug):
    post = get_object_or_404(Post, post_Slug=slug)
    random_posts = Post.objects.all().order_by("-post_date").order_by("?")[0:4]
    user_agent = get_user_agent(request)  
    try:

        view_report = PostView(post=post,
                            ip=get_ip(request),
                            created=datetime.date.today(),
                            session=request.session.session_key,
                            referral = request.META.get('HTTP_REFERER'),
                            user_agent = request.META['HTTP_USER_AGENT'] ,
                            user_agent_browser = user_agent.browser , 
                            user_agent_os =user_agent.os ,
                            user_agent_device = user_agent.device,
                            is_mobile = user_agent.is_mobile ,
                            is_tablet = user_agent.is_tablet,
                            is_touch_capable = user_agent.is_touch_capable,
                            is_pc = user_agent.is_pc,
                            is_bot = user_agent.is_bot,
                            )


        if not PostView.objects.filter(post=post,ip=get_ip(request)).exists() and user_agent.is_bot != True :

            post.views = post.views + 1
            post.save()
            view_report.save()

            try:
                post_report_obj = PostReport.objects.all().filter(created = datetime.date.today() ,post = post)
                
            except:
                post_report_obj = False 

            if post_report_obj :
                old_post_report = PostReport.objects.get(created = datetime.date.today(), post = post)
                old_post_report.impressions = old_post_report.impressions + 1
                #old_post_report.publisher = post.publisher
                old_post_report.save() 

            else:    
                post_report = PostReport(
                    impressions = 1,
                    created = datetime.date.today(),
                    post = post,
                    publisher = post.author,)
                post_report.save() 

                           
    except:
        pass

                  
    comments = post.comments.filter(active=True)
    print(comments)
    # check before save data from comment form
    if request.method == 'POST':
        if  request.user.is_authenticated and not request.user.is_anonymous:
            profile = Profile.objects.get(user = request.user)      
            name = request.POST['name']
            email = request.POST['email']
            comment = request.POST['comment']

            new_comment =  Comment(
                        name = name,
                        email =email,
                        body = comment,
                        post = post,
                        profile = profile)
            new_comment.save() 
            messages.success(
                request, f'Your comment has been sent')

        else:
             messages.warning(
                request, f'Please login to be able to comment')   
    
    context = {
        'post': post,
        'random_posts':random_posts,
        'comments': comments,
  
    }

    return render(request, 'blog/blog-post-fullwidth.html', context)
   