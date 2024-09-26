from django.urls import path, re_path
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name = 'blog'
urlpatterns = [
    path('blog/', views.home, name='home-blog'),
    #path('', views.MainView.as_view(), name='home-blog-view'),
    # path('posts-json/<int:num_posts>/',
    #      views.PostJsonListView.as_view(), name='posts-json-view'),
    # path('about/', views.about, name='about'),
    path('category/<str:slug>/', views.super_category, name='category'),
    # path('detail/<str:slug>', views.post_detail, name='postdetail'),
    re_path(r'^detail/(?P<slug>[^/]+)/?$',
            views.post_detail, name='postdetail'),
    # path('detail/<str:slug>/download/', views.post_detail, name='postdetail'),
    #url(r'tag/(?P<input_tag>\w+)$', views.tag_view, name='tag'),
    # path('new_post/', views.PostCreateView.as_view(), name='new_post'),
    # path('detail/<slug:pk>/update/',
    #      views.PostUpdateView.as_view(), name='update_post'),
    # path('detail/<slug:pk>/delete/',
    #      views.PostDeleteView.as_view(), name='delete_post'),


]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
