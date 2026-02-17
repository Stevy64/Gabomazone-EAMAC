from django.shortcuts import render, get_object_or_404


def faq(request):
    """Page FAQ dédiée."""
    return render(request, 'pages/faq.html')


def pages(request, slug):
    from .models import PagesList
    page = get_object_or_404(PagesList, slug=slug, active=True)
    context = {"page": page}
    return render(request, 'pages/pages.html', context)