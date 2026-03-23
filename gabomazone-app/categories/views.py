import logging

from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from django.db.models import Count
from django.db import OperationalError
from django.utils import timezone

from .models import SubCategory, MainCategory, SuperCategory, MiniCategory
from products.models import Product
from accounts.models import PeerToPeerProduct, ProductBoostRequest

logger = logging.getLogger(__name__)


def get_active_boosted_product_ids():
    """
    Récupère les IDs des produits ayant un boost actif.
    Un boost est actif si :
    - Le statut est ACTIVE
    - La date actuelle est entre start_date et end_date
    """
    try:
        now = timezone.now()
        active_boosts = ProductBoostRequest.objects.filter(
            status=ProductBoostRequest.ACTIVE,
            start_date__lte=now,
            end_date__gte=now
        ).select_related('product')
        
        # Retourner un set d'IDs pour une recherche rapide
        return set(boost.product.id for boost in active_boosts if boost.product)
    except (OperationalError, AttributeError):
        # Si la table n'existe pas encore
        return set()


def add_boost_flag_to_products(products_list):
    """Ajoute le flag is_boosted à chaque produit dans la liste"""
    boosted_ids = get_active_boosted_product_ids()
    for product_dict in products_list:
        if not product_dict.get('is_peer_to_peer', False):
            product_dict['is_boosted'] = product_dict.get('id', 0) in boosted_ids
    return products_list


def sort_products_with_boost_priority(products_list, order_by):
    """Trie les produits en priorisant ceux qui sont boostés"""
    boosted_ids = get_active_boosted_product_ids()
    
    if order_by == '-date':
        products_list.sort(key=lambda x: (
            x.get('id', 0) in boosted_ids if not x.get('is_peer_to_peer', False) else False,
            x.get('view_count', 0) if not x.get('is_peer_to_peer', False) else 0
        ), reverse=True)
    elif order_by == '-PRDPrice':
        products_list.sort(key=lambda x: (
            x.get('id', 0) in boosted_ids if not x.get('is_peer_to_peer', False) else False,
            x.get('PRDPrice', 0)
        ), reverse=True)
    elif order_by == 'PRDPrice':
        products_list.sort(key=lambda x: (
            not (x.get('id', 0) in boosted_ids if not x.get('is_peer_to_peer', False) else False),
            x.get('PRDPrice', 0)
        ))
    else:
        # Par défaut, trier par boost puis par date
        products_list.sort(key=lambda x: (
            x.get('id', 0) in boosted_ids if not x.get('is_peer_to_peer', False) else False,
            x.get('view_count', 0) if not x.get('is_peer_to_peer', False) else 0
        ), reverse=True)
    
    return products_list


class PeerToPeerProductWrapper:
    """Wrapper pour rendre un PeerToPeerProduct compatible avec le template Product"""
    def __init__(self, peer_product):
        from accounts.models import PeerToPeerProductFavorite
        self.id = peer_product.id  # ID sans préfixe (le préfixe sera ajouté dans le template)
        self.product_name = peer_product.product_name
        self.PRDPrice = peer_product.PRDPrice
        self.PRDDiscountPrice = 0
        self.product_image = peer_product.product_image
        self.PRDSlug = peer_product.PRDSlug
        self.view_count = getattr(peer_product, 'view_count', 0) or 0
        self.like_count = PeerToPeerProductFavorite.objects.filter(product=peer_product).count()
        self.is_peer_to_peer = True
        self._peer_product = peer_product
        self.date = getattr(peer_product, 'date', None)
        self.seller_city = getattr(peer_product, 'seller_city', None)
        self.condition = getattr(peer_product, 'condition', None) or ''
        self.condition_display = peer_product.get_condition_display() if getattr(peer_product, 'condition', None) else ''
    
    def get_additional_images(self):
        """Récupère les images supplémentaires"""
        images = []
        if self._peer_product.additional_image_1:
            images.append(self._peer_product.additional_image_1)
        if self._peer_product.additional_image_2:
            images.append(self._peer_product.additional_image_2)
        if self._peer_product.additional_image_3:
            images.append(self._peer_product.additional_image_3)
        return images


def shop(request):
    """Page grille produits (shop principal)."""
    return render(request, "categories/shop-grid-left.html")


def super_category(request, slug):
    """Affiche les sous-catégories principales d'une super-catégorie."""
    super_category_obj = SuperCategory.objects.get(slug=slug)
    main_category_obj = MainCategory.objects.all().filter(
        super_category=super_category_obj)

    context = {
        "main_category_obj": main_category_obj,
        "super_category_obj": super_category_obj,
        "slug": slug,

    }
    return render(request, "categories/shop-super-category.html", context)


def main_category(request, slug):
    """Affiche les sous-catégories d'une catégorie principale."""
    main_category_obj = MainCategory.objects.get(slug=slug)
    sub_category_obj = SubCategory.objects.all().filter(
        main_category=main_category_obj)

    context = {
        "sub_category_obj": sub_category_obj,
        "main_category_obj": main_category_obj,
        "slug": slug,
    }
    return render(request, "categories/shop-main-category.html", context)


def sub_category(request, slug):
    """Affiche les mini-catégories d'une sous-catégorie."""
    sub_category_obj = SubCategory.objects.get(slug=slug)
    mini_category_obj = MiniCategory.objects.all().filter(
        sub_category=sub_category_obj)

    context = {
        "mini_category_obj": mini_category_obj,
        "sub_category_obj": sub_category_obj,
        "slug": slug,
    }
    return render(request, "categories/shop-sub-category.html", context)


def category_list(request):
    """Page listant toutes les catégories avec compteurs de produits."""
    supercategory = SuperCategory.objects.all().order_by('name')
    maincategory = MainCategory.objects.all().order_by('name')
    subcategory = SubCategory.objects.all().order_by('name')
    minicategory = MiniCategory.objects.all().order_by('name')
    
    # Préparer les données pour le template
    super_categories_data = []
    for super in supercategory:
        main_cats = maincategory.filter(super_category=super)
        # Ajouter le compteur de sous-catégories à chaque catégorie principale
        for main in main_cats:
            sub_count = subcategory.filter(main_category=main).count()
            main.sub_count = sub_count  # Ajouter directement à l'objet
        
        # Compter les produits (Product + PeerToPeerProduct) pour cette super catégorie
        product_count = 0
        try:
            product_count += Product.objects.filter(
                product_supercategory=super,
                PRDISDeleted=False,
                PRDISactive=True
            ).count()
        except (OperationalError, Exception) as e:
            logger.debug("Product count query failed for super %s: %s", super.name, e)
        
        try:
            product_count += PeerToPeerProduct.objects.filter(
                product_supercategory=super,
                status=PeerToPeerProduct.APPROVED
            ).count()
        except (OperationalError, Exception) as e:
            logger.debug("PeerToPeerProduct count query failed for super %s: %s", super.name, e)
        
        # Ajouter le compteur à l'objet super
        super.product_count = product_count
        
        super_categories_data.append({
            'super': super,
            'main_categories': main_cats,
        })
    
    context = {
        'supercategory': supercategory,
        'maincategory': maincategory,
        'subcategory': subcategory,
        'minicategory': minicategory,
        'super_categories_data': super_categories_data,
    }

    return render(request, "categories/category-list.html", context)


def get_main_categories(request):
    """Endpoint AJAX pour récupérer les catégories principales d'une super catégorie"""
    super_category_id = request.GET.get('super_category_id')
    if not super_category_id:
        return JsonResponse({'categories': []})
    
    try:
        super_category = SuperCategory.objects.get(id=super_category_id)
        main_categories = MainCategory.objects.filter(super_category=super_category).order_by('name')
        categories_data = [{'id': cat.id, 'name': cat.name} for cat in main_categories]
        return JsonResponse({'categories': categories_data})
    except SuperCategory.DoesNotExist:
        return JsonResponse({'categories': []})


def get_sub_categories(request):
    """Endpoint AJAX pour récupérer les sous-catégories d'une catégorie principale"""
    main_category_id = request.GET.get('main_category_id')
    if not main_category_id:
        return JsonResponse({'categories': []})
    
    try:
        main_category = MainCategory.objects.get(id=main_category_id)
        sub_categories = SubCategory.objects.filter(main_category=main_category).order_by('name')
        categories_data = [{'id': cat.id, 'name': cat.name} for cat in sub_categories]
        return JsonResponse({'categories': categories_data})
    except MainCategory.DoesNotExist:
        return JsonResponse({'categories': []})


def convert_peer_to_peer_to_dict(peer_product):
    """Convertit un PeerToPeerProduct en dictionnaire compatible avec les produits normaux"""
    from accounts.models import PeerToPeerProductFavorite
    
    product_images = [str(peer_product.product_image)] if peer_product.product_image else []
    if peer_product.additional_image_1:
        product_images.append(str(peer_product.additional_image_1))
    if peer_product.additional_image_2:
        product_images.append(str(peer_product.additional_image_2))
    if peer_product.additional_image_3:
        product_images.append(str(peer_product.additional_image_3))
    
    # Compter les favoris pour cet article C2C
    like_count = PeerToPeerProductFavorite.objects.filter(product=peer_product).count()
    
    return {
        'id': peer_product.id,  # ID sans préfixe (le préfixe sera ajouté dans le template)
        'product_name': peer_product.product_name,
        'PRDPrice': peer_product.PRDPrice,
        'PRDDiscountPrice': 0,  # Pas de prix réduit pour les articles C2C
        'product_image': str(peer_product.product_image),
        'product_images': product_images,
        'PRDSlug': peer_product.PRDSlug,
        'view_count': peer_product.view_count or 0,  # Utiliser le compteur de vues réel
        'like_count': like_count,
        'is_peer_to_peer': True,  # Flag pour identifier les articles C2C
        'condition': getattr(peer_product, 'condition', None) or '',
        'condition_display': peer_product.get_condition_display() if getattr(peer_product, 'condition', None) else '',
    }


def get_peer_to_peer_products(cat_type, cat_id, order_by, lower, upper):
    """Récupère les articles C2C approuvés selon les filtres"""
    try:
        peer_products = PeerToPeerProduct.objects.filter(status=PeerToPeerProduct.APPROVED)
        
        # Appliquer les filtres de catégorie
        if cat_type == "super" and cat_id:
            peer_products = peer_products.filter(product_supercategory_id=int(cat_id))
        elif cat_type == "main" and cat_id:
            peer_products = peer_products.filter(product_maincategory_id=int(cat_id))
        elif cat_type == "sub" and cat_id:
            peer_products = peer_products.filter(product_subcategory_id=int(cat_id))
        
        # Trier selon order_by (convertir -date en -date pour PeerToPeerProduct)
        if order_by == '-date':
            peer_products = peer_products.order_by('-date')
        elif order_by == 'date':
            peer_products = peer_products.order_by('date')
        elif order_by == '-PRDPrice':
            peer_products = peer_products.order_by('-PRDPrice')
        elif order_by == 'PRDPrice':
            peer_products = peer_products.order_by('PRDPrice')
        else:
            peer_products = peer_products.order_by('-date')
        
        # Appliquer la pagination
        peer_products = peer_products[lower:upper]
        
        # Convertir en dictionnaires
        return [convert_peer_to_peer_to_dict(p) for p in peer_products]
    except (OperationalError, AttributeError):
        # Si la table n'existe pas encore ou erreur
        return []




class ProductListHTMXView(View):
    """
    Vue HTMX pour le scroll infini avec pagination Django
    Retourne du HTML partiel pour HTMX
    """
    PAGE_SIZE = 12  # 12 produits par page
    
    def get_queryset(self, cat_type, cat_id, order_by):
        """Construit le queryset selon les filtres"""
        base_filter = {'PRDISDeleted': False, 'PRDISactive': True}
        
        # Ajouter le filtre de catégorie
        if cat_type and cat_id:
            try:
                cat_id_int = int(cat_id)
                logger.debug("get_queryset - cat_type: '%s', cat_id_int: %s", cat_type, cat_id_int)
                if cat_type == "super":
                    base_filter['product_supercategory'] = cat_id_int
                elif cat_type == "main":
                    base_filter['product_maincategory'] = cat_id_int
                elif cat_type == "sub":
                    base_filter['product_subcategory'] = cat_id_int
                elif cat_type == "mini":
                    base_filter['product_minicategor'] = cat_id_int
                logger.debug("get_queryset - base_filter: %s", base_filter)
            except (ValueError, TypeError) as e:
                # Si cat_id n'est pas un entier valide, ignorer le filtre
                logger.debug("get_queryset - Erreur conversion cat_id: %s, cat_id reçu: '%s'", e, cat_id)
                pass
        
        # Construire le queryset avec annotation pour like_count et select_related pour le lieu (product_vendor)
        try:
            queryset = Product.objects.filter(**base_filter).select_related('product_vendor').annotate(
                like_count=Count('favorites')
            ).order_by(order_by)
            logger.debug("get_queryset - queryset count: %s", queryset.count())
        except Exception as e:
            logger.debug("get_queryset - Exception avec favorites: %s", e)
            queryset = Product.objects.filter(**base_filter).select_related('product_vendor').order_by(order_by)
            logger.debug("get_queryset - queryset count (sans favorites): %s", queryset.count())
        
        return queryset
    
    def get_peer_to_peer_queryset(self, cat_type, cat_id, order_by):
        """Construit le queryset pour les articles C2C"""
        try:
            peer_products = PeerToPeerProduct.objects.filter(status=PeerToPeerProduct.APPROVED)
            
            # Appliquer les filtres de catégorie
            if cat_type and cat_id:
                try:
                    cat_id_int = int(cat_id)
                    if cat_type == "super":
                        peer_products = peer_products.filter(product_supercategory_id=cat_id_int)
                    elif cat_type == "main":
                        peer_products = peer_products.filter(product_maincategory_id=cat_id_int)
                    elif cat_type == "sub":
                        peer_products = peer_products.filter(product_subcategory_id=cat_id_int)
                except (ValueError, TypeError):
                    # Si cat_id n'est pas un entier valide, ignorer le filtre
                    pass
            
            # Trier selon order_by
            if order_by == '-date':
                peer_products = peer_products.order_by('-date')
            elif order_by == 'date':
                peer_products = peer_products.order_by('date')
            elif order_by == '-PRDPrice':
                peer_products = peer_products.order_by('-PRDPrice')
            elif order_by == 'PRDPrice':
                peer_products = peer_products.order_by('PRDPrice')
            else:
                peer_products = peer_products.order_by('-date')
            
            return peer_products
        except (OperationalError, AttributeError):
            return PeerToPeerProduct.objects.none()
    
    def get(self, request, *args, **kwargs):
        """Retourne un fragment HTML de produits paginés pour scroll infini HTMX."""
        page = int(request.GET.get('page', 1))
        order_by = request.GET.get('order_by', '-date')
        cat_type = request.GET.get('cat_type', 'all')
        cat_id = request.GET.get('cat_id', '')
        product_type = request.GET.get('product_type', 'all')  # 'all', 'shop', 'peer'
        
        # Debug: imprimer les paramètres reçus
        logger.debug("ProductListHTMXView - cat_type: '%s', cat_id: '%s', order_by: '%s', page: %s", cat_type, cat_id, order_by, page)
        
        # Construire le queryset pour les produits de magasin
        shop_queryset = None
        if product_type in ['all', 'shop']:
            # Si cat_type est "all" ou vide, ou si cat_id est vide, récupérer tous les produits
            if cat_type == "all" or not cat_type or (cat_id == '' or cat_id is None):
                logger.debug("Récupération de tous les produits (cat_type='%s', cat_id='%s')", cat_type, cat_id)
                try:
                    shop_queryset = Product.objects.filter(
                        PRDISDeleted=False, 
                        PRDISactive=True
                    ).select_related('product_vendor').annotate(
                        like_count=Count('favorites')
                    ).order_by(order_by)
                except Exception:
                    shop_queryset = Product.objects.filter(
                        PRDISDeleted=False, 
                        PRDISactive=True
                    ).select_related('product_vendor').order_by(order_by)
            else:
                # Filtrer par catégorie
                logger.debug("Filtrage par catégorie (cat_type='%s', cat_id='%s')", cat_type, cat_id)
                shop_queryset = self.get_queryset(cat_type, cat_id, order_by)
                logger.debug("shop_queryset count after get_queryset: %s", shop_queryset.count() if shop_queryset else 0)
        else:
            shop_queryset = Product.objects.none()
        
        # Récupérer les articles C2C
        peer_queryset = None
        if product_type in ['all', 'peer']:
            try:
                peer_queryset = self.get_peer_to_peer_queryset(cat_type, cat_id, order_by)
            except Exception:
                peer_queryset = PeerToPeerProduct.objects.none()
        else:
            peer_queryset = PeerToPeerProduct.objects.none()
        
        # Combiner les deux querysets en listes pour la pagination
        all_products = []
        if shop_queryset is not None:
            all_products.extend(list(shop_queryset))
        if peer_queryset is not None:
            all_products.extend([PeerToPeerProductWrapper(p) for p in peer_queryset])
        
        # Récupérer les IDs des produits boostés pour le tri
        boosted_ids = get_active_boosted_product_ids()
        
        # Trier tous les produits ensemble avec priorité aux boostés
        if order_by == '-date':
            all_products.sort(key=lambda x: (
                getattr(x, 'id', 0) in boosted_ids if not getattr(x, 'is_peer_to_peer', False) else False,
                getattr(x, 'date', getattr(x, '_peer_product', None) and getattr(x._peer_product, 'date', None) or None)
            ), reverse=True)
        elif order_by == '-PRDPrice':
            all_products.sort(key=lambda x: (
                getattr(x, 'id', 0) in boosted_ids if not getattr(x, 'is_peer_to_peer', False) else False,
                getattr(x, 'PRDPrice', 0)
            ), reverse=True)
        elif order_by == 'PRDPrice':
            all_products.sort(key=lambda x: (
                not (getattr(x, 'id', 0) in boosted_ids if not getattr(x, 'is_peer_to_peer', False) else False),
                getattr(x, 'PRDPrice', 0)
            ))
        else:
            # Par défaut, trier par boost puis par date
            all_products.sort(key=lambda x: (
                getattr(x, 'id', 0) in boosted_ids if not getattr(x, 'is_peer_to_peer', False) else False,
                getattr(x, 'date', getattr(x, '_peer_product', None) and getattr(x._peer_product, 'date', None) or None)
            ), reverse=True)
        
        # Pagination manuelle
        total_count = len(all_products)
        start = (page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_products = all_products[start:end]
        has_next = end < total_count
        next_page = page + 1 if has_next else None
        
        # Préparer les produits avec leurs images
        import json
        products_data = []
        for product in page_products:
            # Collecter toutes les images avec le préfixe /media/
            product_images = []
            if hasattr(product, 'is_peer_to_peer') and product.is_peer_to_peer:
                # Article C2C
                if product.product_image:
                    img_path = str(product.product_image)
                    if not img_path.startswith('/media/'):
                        img_path = '/media/' + img_path
                    product_images.append(img_path)
                for img in product.get_additional_images():
                    img_path = str(img)
                    if not img_path.startswith('/media/'):
                        img_path = '/media/' + img_path
                    product_images.append(img_path)
            else:
                # Produit normal
                if product.product_image:
                    img_path = str(product.product_image)
                    if not img_path.startswith('/media/'):
                        img_path = '/media/' + img_path
                    product_images.append(img_path)
                if product.additional_image_1:
                    img_path = str(product.additional_image_1)
                    if not img_path.startswith('/media/'):
                        img_path = '/media/' + img_path
                    product_images.append(img_path)
                if product.additional_image_2:
                    img_path = str(product.additional_image_2)
                    if not img_path.startswith('/media/'):
                        img_path = '/media/' + img_path
                    product_images.append(img_path)
                if product.additional_image_3:
                    img_path = str(product.additional_image_3)
                    if not img_path.startswith('/media/'):
                        img_path = '/media/' + img_path
                    product_images.append(img_path)
                if product.additional_image_4:
                    img_path = str(product.additional_image_4)
                    if not img_path.startswith('/media/'):
                        img_path = '/media/' + img_path
                    product_images.append(img_path)
            
            # Vérifier si le produit est boosté
            is_boosted = False
            if not getattr(product, 'is_peer_to_peer', False):
                is_boosted = getattr(product, 'id', 0) in boosted_ids
            
            products_data.append({
                'product': product,
                'product_images': json.dumps(product_images),  # JSON stringifié pour le template
                'like_count': getattr(product, 'like_count', 0),
                'is_peer_to_peer': getattr(product, 'is_peer_to_peer', False),
                'is_boosted': is_boosted,
            })
        
        # Contexte pour le template
        context = {
            'products_data': products_data,
            'page_obj': type('Page', (), {'has_next': lambda: has_next, 'next_page_number': lambda: next_page})(),
            'has_next': has_next,
            'next_page': next_page,
            'order_by': order_by,
            'cat_type': cat_type,
            'cat_id': cat_id,
            'product_type': product_type,
            'total_products': total_count,  # Total de produits pour le compteur
        }
        
        # Rendre le template partiel
        return render(request, 'categories/product_list_partial.html', context)
