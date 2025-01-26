"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url
from django.views.static import serve
urlpatterns = [
    url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),

    url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),
    path('', include('home.urls', namespace='home')),
    path('', include('products.urls', namespace='products')),
    path('', include('accounts.urls', namespace='accounts')),
    path('', include('orders.urls', namespace='orders')),
    path('', include('categories.urls', namespace='categories')),
    path('', include('suppliers.urls', namespace='suppliers')),
    path('', include('supplier_panel.urls', namespace='supplier_dashboard')),
    #path('', include('newsletters.urls', namespace='newsletters')),
    #path('', include('blog.urls', namespace='blog')),
    path('', include('contact.urls', namespace='contact')),
    path('', include('pages.urls', namespace='pages')),
    path('currencies/', include('currencies.urls')),

]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
