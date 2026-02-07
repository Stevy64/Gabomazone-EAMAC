from datetime import datetime
from django import template
from django.utils import timezone

#from orders.views import Order, OrderDetails
from orders.models import Order, OrderDetails
from products.models import Product
from django.contrib.auth.models import User
from decimal import Decimal

register = template.Library()


@register.filter(name='relative_date')
def relative_date(value):
    """
    Affiche une date en temps relatif en français (il y a 5h, Hier, il y a 1 mois, etc.).
    """
    if value is None:
        return ""
    try:
        now = timezone.now()
        if hasattr(value, 'date') and not hasattr(value, 'hour'):
            value = datetime.combine(value, datetime.min.time())
            if timezone.is_aware(now):
                value = timezone.make_aware(value)
        elif timezone.is_naive(value) and timezone.is_aware(now):
            value = timezone.make_aware(value)
        delta = now - value
        total_seconds = int(delta.total_seconds())
        if total_seconds < 0:
            return "À l'instant"
        if total_seconds < 60:
            return "À l'instant"
        if total_seconds < 3600:
            m = total_seconds // 60
            return f"il y a {m} min"
        if total_seconds < 86400:
            h = total_seconds // 3600
            return f"il y a {h}h" if h < 24 else "Hier"
        if total_seconds < 172800:
            return "Hier"
        if total_seconds < 604800:
            j = total_seconds // 86400
            return f"il y a {j} jour{'s' if j > 1 else ''}"
        if total_seconds < 2592000:
            s = total_seconds // 604800
            return f"il y a {s} sem." if s == 1 else f"il y a {s} sem."
        if total_seconds < 31536000:
            mo = total_seconds // 2592000
            return f"il y a {mo} mois"
        y = total_seconds // 31536000
        return f"il y a {y} an{'s' if y > 1 else ''}"
    except (TypeError, AttributeError):
        return ""


@register.filter
def cart_items_count(user):
    if user.is_authenticated and not user.is_anonymous:
        if Order.objects.all().filter(user=user, is_finished=False):
            order = Order.objects.get(user=user, is_finished=False)
            return OrderDetails.objects.all().filter(order=order).count()

        else:
            return 0



@register.filter
def underway_orders_count(user):
    if user.is_authenticated and not user.is_anonymous:
        if Order.objects.all().filter(status="Underway"):
            underway_orders = Order.objects.all().filter(status="Underway").count()
            return underway_orders

        else:
            return 0


@register.filter
def all_orders_count(user):
    if user.is_authenticated and not user.is_anonymous:
        if Order.objects.all():
            all_order = Order.objects.all().count()
            return all_order

        else:
            return 0


@register.filter
def all_users_count(user):
    if user.is_authenticated and not user.is_anonymous:
        if User.objects.all():
            all_users = User.objects.all().count()
            return all_users

        else:
            return 0


@register.filter
def all_products_count(user):
    if user.is_authenticated and not user.is_anonymous:
        if Product.objects.all():
            all_products = Product.objects.all().count()
            return all_products

        else:
            return 0


@register.filter(name='format_price')
def format_price(value):
    """
    Formate un prix avec des espaces pour la lisibilité.
    Exemple: 100000 -> "100 000"
    """
    if value is None:
        return "0"
    
    try:
        # Convertir en entier pour enlever les décimales
        if isinstance(value, Decimal):
            int_value = int(value)
        elif isinstance(value, float):
            int_value = int(value)
        else:
            int_value = int(float(str(value)))
        
        # Formater avec des espaces tous les 3 chiffres (format français)
        formatted = f"{int_value:,}".replace(",", " ")
        return formatted
    except (ValueError, TypeError):
        return str(value)


@register.filter(name='multiply_and_format')
def multiply_and_format(price, quantity):
    """
    Multiplie un prix par une quantité et formate le résultat.
    Exemple: multiply_and_format(100000, 2) -> "200 000"
    """
    try:
        if price is None or quantity is None:
            return "0"
        
        # Convertir en Decimal pour la précision
        if isinstance(price, Decimal):
            price_decimal = price
        else:
            price_decimal = Decimal(str(price))
        
        if isinstance(quantity, (int, float)):
            quantity_decimal = Decimal(str(quantity))
        else:
            quantity_decimal = Decimal(str(quantity))
        
        total = price_decimal * quantity_decimal
        int_total = int(total)
        
        # Formater avec des espaces
        formatted = f"{int_total:,}".replace(",", " ")
        return formatted
    except (ValueError, TypeError):
        return "0"