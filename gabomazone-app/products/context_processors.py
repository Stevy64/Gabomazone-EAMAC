from .models import ProductFavorite, Product
from django.db import connection


def new_products_obj(request):
    """Context processor pour les nouveaux produits"""
    try:
        new_products = Product.objects.all().filter(PRDISactive=True).order_by('-date')[:10]
        return {
            'new_products': new_products,
        }
    except Exception as e:
        return {
            'new_products': [],
        }


def wishlist_count(request):
    """Context processor pour le compteur de la liste à souhaits"""
    try:
        # Vérifier si la table existe
        table_name = ProductFavorite._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            return {'wishlist_count': 0}
        
        if request.user.is_authenticated:
            wishlist_count = ProductFavorite.objects.filter(user=request.user).count()
        else:
            session_key = request.session.session_key
            if session_key:
                wishlist_count = ProductFavorite.objects.filter(session_key=session_key).count()
            else:
                wishlist_count = 0
        
        return {'wishlist_count': wishlist_count}
    except Exception as e:
        # En cas d'erreur, retourner 0
        return {'wishlist_count': 0}
