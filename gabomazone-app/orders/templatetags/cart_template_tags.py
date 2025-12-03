from django import template
#from orders.views import Order, OrderDetails
from orders.models import Order, OrderDetails
from products.models import Product 
from django.contrib.auth.models import User
from decimal import Decimal

register = template.Library()


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