from django import template

register = template.Library()


@register.filter
def condition_slug(value):
    """Convertit la valeur d'état C2C en slug pour les classes CSS (ex. 'BON ETAT' -> 'bon_etat')."""
    if not value:
        return ''
    return str(value).lower().replace(' ', '_')
