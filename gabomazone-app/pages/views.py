from django.shortcuts import render, get_object_or_404
from django.http import Http404


def faq(request):
    """Page FAQ dédiée."""
    return render(request, 'pages/faq.html')


# Alias de slugs : si l'URL demande un de ces slugs et qu'il n'existe pas,
# on cherche une page avec l'un des slugs alternatifs (ex. about-us -> a-propos).
SLUG_ALIASES = {
    "about-us": ["a-propos", "about", "about-us"],
    "a-propos": ["about-us", "about", "a-propos"],
    "terms": ["conditions-utilisation", "conditions", "terms-of-use", "terms"],
    "conditions-utilisation": ["terms", "conditions", "terms-of-use"],
    "conditions": ["conditions-utilisation", "terms", "terms-of-use"],
    "refund-policy": ["politique-remboursement", "refund", "remboursement"],
    "politique-remboursement": ["refund-policy", "refund", "remboursement"],
    "remboursement": ["politique-remboursement", "refund-policy", "refund"],
    "contact-us": ["contact", "nous-contacter"],
    "nous-contacter": ["contact", "contact-us"],
}


def pages(request, slug):
    from .models import PagesList
    slugs_to_try = [slug]
    if slug in SLUG_ALIASES:
        slugs_to_try = list(dict.fromkeys(SLUG_ALIASES[slug] + [slug]))
    page = None
    for s in slugs_to_try:
        page = PagesList.objects.filter(slug=s, active=True).first()
        if page:
            break
    if not page:
        raise Http404("Page non trouvée")
    context = {"page": page}
    return render(request, "pages/pages.html", context)