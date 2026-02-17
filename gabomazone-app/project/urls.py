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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url
from django.views.static import serve
from django.views.generic import RedirectView
from django.http import HttpResponse
from pages.views import faq as faq_view

# Vue de diagnostic : si /_urls_ok/ répond "OK", Django reçoit bien les requêtes (vérifier Nginx si /contact/ 404)
def _urls_ok(request):
    return HttpResponse("OK", content_type="text/plain")

# Routes footer / pages légales en tout premier (avant media/static) pour éviter 404 en prod
footer_urls = [
    path('_urls_ok/', _urls_ok),
    re_path(r'^_urls_ok$', _urls_ok),  # sans slash (prod envoie parfois sans slash)
    path('faq/', faq_view, name='faq'),
    re_path(r'^faq$', RedirectView.as_view(url='/faq/', permanent=True)),
    path('contact/', include(('contact.urls', 'contact'), namespace='contact')),
    re_path(r'^contact$', RedirectView.as_view(url='/contact/', permanent=True)),
    path('pages/', include(('pages.urls', 'pages'), namespace='pages')),
    re_path(r'^pages$', RedirectView.as_view(url='/pages/', permanent=False)),
]

urlpatterns = footer_urls + [
    url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),
    path('', include('home.urls', namespace='home')),
    path('products/', include('products.urls', namespace='products')),
    path('', include('accounts.urls', namespace='accounts')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('', include('categories.urls', namespace='categories')),
    path('', include('suppliers.urls', namespace='suppliers')),
    path('', include('supplier_panel.urls', namespace='supplier_dashboard')),
    #path('', include('newsletters.urls', namespace='newsletters')),
    #path('', include('blog.urls', namespace='blog')),
    path('currencies/', include('currencies.urls')),
    path('c2c/', include('c2c.urls', namespace='c2c')),

]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
