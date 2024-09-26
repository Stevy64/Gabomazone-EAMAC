from django.shortcuts import render,get_object_or_404
from .models import PagesList
# Create your views here.
def pages(request , slug):
    page = get_object_or_404(PagesList, slug=slug, active=True)
    context = {
        "page": page,
        }
    return render(request , 'pages/pages.html' , context)