from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.db.models import Q


def faq(request):
    """Page FAQ dédiée."""
    return render(request, 'pages/faq.html')


# Alias de slugs : si l'URL demande un de ces slugs et qu'il n'existe pas,
# on cherche une page avec l'un des slugs alternatifs (ex. about-us -> a-propos).
SLUG_ALIASES = {
    "about-us": ["a-propos", "about", "about-us", "qui-sommes-nous"],
    "a-propos": ["about-us", "about", "a-propos", "qui-sommes-nous"],
    "terms": ["conditions-utilisation", "conditions", "terms-of-use", "terms", "cgv", "conditions-generales"],
    "conditions-utilisation": ["terms", "conditions", "terms-of-use", "cgv", "conditions-generales"],
    "conditions": ["conditions-utilisation", "terms", "terms-of-use", "cgv"],
    "refund-policy": ["politique-remboursement", "refund", "remboursement"],
    "politique-remboursement": ["refund-policy", "refund", "remboursement"],
    "remboursement": ["politique-remboursement", "refund-policy", "refund"],
    "contact-us": ["contact", "nous-contacter"],
    "nous-contacter": ["contact", "contact-us"],
}

# Fallback : mots-clés dans le nom (icontains) pour retrouver une page si aucun slug ne matche.
SLUG_NAME_KEYWORDS = {
    "about-us": ["propos", "about", "qui sommes", "présentation"],
    "a-propos": ["propos", "about", "qui sommes", "présentation"],
    "about": ["propos", "about", "qui sommes", "présentation"],
    "terms": ["condition", "utilisation", "cgv", "legal"],
    "conditions-utilisation": ["condition", "utilisation", "cgv", "legal"],
    "conditions": ["condition", "utilisation", "cgv", "legal"],
    "refund-policy": ["remboursement", "refund", "politique"],
    "politique-remboursement": ["remboursement", "refund", "politique"],
    "remboursement": ["remboursement", "refund", "politique"],
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
    # Si toujours rien : chercher par mots-clés dans le nom de la page
    if not page and slug in SLUG_NAME_KEYWORDS:
        keywords = SLUG_NAME_KEYWORDS[slug]
        for kw in keywords:
            page = PagesList.objects.filter(active=True).filter(
                Q(name__icontains=kw) | Q(slug__icontains=kw)
            ).first()
            if page:
                break
    if not page:
        raise Http404("Page non trouvée")
    context = {"page": page}
    return render(request, "pages/pages.html", context)