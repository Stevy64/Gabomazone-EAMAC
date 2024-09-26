from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import reverse_lazy


app_name = 'newsletters'
urlpatterns = [

    path('letter/', views.letter, name='newsletter'),    

]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
