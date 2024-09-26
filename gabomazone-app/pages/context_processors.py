
from .models import PagesList


def pages_list_obj(request):
    pages_list = PagesList.objects.all().filter(active = True)
  
    return {
        'pages_list': pages_list,
         }
