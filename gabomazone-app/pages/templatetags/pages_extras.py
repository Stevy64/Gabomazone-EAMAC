import re
from django import template

register = template.Library()


@register.filter
def phone_to_whatsapp(value):
    """Convertit un numéro de téléphone en URL WhatsApp (wa.me). Garde uniquement les chiffres."""
    if not value:
        return ''
    digits = re.sub(r'\D', '', str(value))
    if not digits:
        return ''
    return f'https://wa.me/{digits}'
