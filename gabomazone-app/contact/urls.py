from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name = 'contact'
urlpatterns = [
    path('', views.contact, name='contact'),
]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
