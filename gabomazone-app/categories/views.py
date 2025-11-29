from urllib import request
from django.shortcuts import render
from .models import SubCategory, MainCategory, SuperCategory, MiniCategory
from django.views.generic import View, TemplateView
from products.models import Product
from django.http import JsonResponse
from django.db.models import Count
from django.core.paginator import Paginator
from django.template.loader import render_to_string
# Create your views here.


def shop(request):

    return render(request, "categories/shop-grid-left.html")


def super_category(request, slug):

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


class CategoryJsonListView(View):
    def get(self, *args, **kwargs):

        upper = int(self.request.GET.get("num_products"))
        orderd_by = self.request.GET.get("order_by")
        CAT_id = self.request.GET.get("CAT_id")
        CAT_type = self.request.GET.get("cat_type")

        if CAT_type == "all":
            lower = upper - 10
            # print(lower, upper)
            try:
                products_queryset = Product.objects.all().filter(PRDISDeleted = False , PRDISactive = True ).annotate(
                    like_count=Count('favorites')
                ).order_by(orderd_by)[lower:upper]
            except:
                # Si la table favorites n'existe pas encore, utiliser values() directement
                products_queryset = Product.objects.all().filter(PRDISDeleted = False , PRDISactive = True ).order_by(orderd_by)[lower:upper]
            
            products = []
            for product in products_queryset:
                # Collecter toutes les images du produit
                product_images = [str(product.product_image)] if product.product_image else []
                if product.additional_image_1:
                    product_images.append(str(product.additional_image_1))
                if product.additional_image_2:
                    product_images.append(str(product.additional_image_2))
                if product.additional_image_3:
                    product_images.append(str(product.additional_image_3))
                if product.additional_image_4:
                    product_images.append(str(product.additional_image_4))
                
                product_dict = {
                    'id': product.id,
                    'product_name': product.product_name,
                    'PRDPrice': product.PRDPrice,
                    'PRDDiscountPrice': product.PRDDiscountPrice,
                    'product_image': str(product.product_image),
                    'product_images': product_images,  # Toutes les images
                    'PRDSlug': product.PRDSlug,
                    'view_count': getattr(product, 'view_count', 0),
                    'like_count': getattr(product, 'like_count', 0),
                }
                products.append(product_dict)
            products_size = len(Product.objects.all().filter(PRDISDeleted = False , PRDISactive = True ))
            max_size = True if upper >= products_size else False
            return JsonResponse({"data": products,  "max": max_size, "products_size": products_size, }, safe=False)

        else:      # 3
            lower = upper - 10
            # print(lower, upper)
            if CAT_type == "super":
                try:
                    products_queryset = Product.objects.all().filter(product_supercategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).annotate(
                        like_count=Count('favorites')
                    ).order_by(orderd_by)[lower:upper]
                except:
                    products_queryset = Product.objects.all().filter(product_supercategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).order_by(orderd_by)[lower:upper]
                
                products = []
                for product in products_queryset:
                    # Collecter toutes les images du produit
                    product_images = [str(product.product_image)] if product.product_image else []
                    if product.additional_image_1:
                        product_images.append(str(product.additional_image_1))
                    if product.additional_image_2:
                        product_images.append(str(product.additional_image_2))
                    if product.additional_image_3:
                        product_images.append(str(product.additional_image_3))
                    if product.additional_image_4:
                        product_images.append(str(product.additional_image_4))
                    
                    product_dict = {
                        'id': product.id,
                        'product_name': product.product_name,
                        'PRDPrice': product.PRDPrice,
                        'PRDDiscountPrice': product.PRDDiscountPrice,
                        'product_image': str(product.product_image),
                        'product_images': product_images,  # Toutes les images
                        'PRDSlug': product.PRDSlug,
                        'view_count': getattr(product, 'view_count', 0),
                        'like_count': getattr(product, 'like_count', 0),
                    }
                    products.append(product_dict)
                products_size = len(
                    Product.objects.all().filter(product_supercategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ))
            elif CAT_type == "main":
                try:
                    products_queryset = Product.objects.all().filter(product_maincategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).annotate(
                        like_count=Count('favorites')
                    ).order_by(orderd_by)[lower:upper]
                except:
                    products_queryset = Product.objects.all().filter(product_maincategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).order_by(orderd_by)[lower:upper]
                
                products = []
                for product in products_queryset:
                    # Collecter toutes les images du produit
                    product_images = [str(product.product_image)] if product.product_image else []
                    if product.additional_image_1:
                        product_images.append(str(product.additional_image_1))
                    if product.additional_image_2:
                        product_images.append(str(product.additional_image_2))
                    if product.additional_image_3:
                        product_images.append(str(product.additional_image_3))
                    if product.additional_image_4:
                        product_images.append(str(product.additional_image_4))
                    
                    product_dict = {
                        'id': product.id,
                        'product_name': product.product_name,
                        'PRDPrice': product.PRDPrice,
                        'PRDDiscountPrice': product.PRDDiscountPrice,
                        'product_image': str(product.product_image),
                        'product_images': product_images,  # Toutes les images
                        'PRDSlug': product.PRDSlug,
                        'view_count': getattr(product, 'view_count', 0),
                        'like_count': getattr(product, 'like_count', 0),
                    }
                    products.append(product_dict)
                products_size = len(
                    Product.objects.all().filter(product_maincategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ))
            elif CAT_type == "sub":
                try:
                    products_queryset = Product.objects.all().filter(product_subcategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).annotate(
                        like_count=Count('favorites')
                    ).order_by(orderd_by)[lower:upper]
                except:
                    products_queryset = Product.objects.all().filter(product_subcategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).order_by(orderd_by)[lower:upper]
                
                products = []
                for product in products_queryset:
                    # Collecter toutes les images du produit
                    product_images = [str(product.product_image)] if product.product_image else []
                    if product.additional_image_1:
                        product_images.append(str(product.additional_image_1))
                    if product.additional_image_2:
                        product_images.append(str(product.additional_image_2))
                    if product.additional_image_3:
                        product_images.append(str(product.additional_image_3))
                    if product.additional_image_4:
                        product_images.append(str(product.additional_image_4))
                    
                    product_dict = {
                        'id': product.id,
                        'product_name': product.product_name,
                        'PRDPrice': product.PRDPrice,
                        'PRDDiscountPrice': product.PRDDiscountPrice,
                        'product_image': str(product.product_image),
                        'product_images': product_images,  # Toutes les images
                        'PRDSlug': product.PRDSlug,
                        'view_count': getattr(product, 'view_count', 0),
                        'like_count': getattr(product, 'like_count', 0),
                    }
                    products.append(product_dict)
                products_size = len(
                    Product.objects.all().filter(product_subcategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ))

            else:
                try:
                    products_queryset = Product.objects.all().filter(product_minicategor=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).annotate(
                        like_count=Count('favorites')
                    ).order_by(orderd_by)[lower:upper]
                except:
                    products_queryset = Product.objects.all().filter(product_minicategor=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).order_by(orderd_by)[lower:upper]
                
                products = []
                for product in products_queryset:
                    # Collecter toutes les images du produit
                    product_images = [str(product.product_image)] if product.product_image else []
                    if product.additional_image_1:
                        product_images.append(str(product.additional_image_1))
                    if product.additional_image_2:
                        product_images.append(str(product.additional_image_2))
                    if product.additional_image_3:
                        product_images.append(str(product.additional_image_3))
                    if product.additional_image_4:
                        product_images.append(str(product.additional_image_4))
                    
                    product_dict = {
                        'id': product.id,
                        'product_name': product.product_name,
                        'PRDPrice': product.PRDPrice,
                        'PRDDiscountPrice': product.PRDDiscountPrice,
                        'product_image': str(product.product_image),
                        'product_images': product_images,  # Toutes les images
                        'PRDSlug': product.PRDSlug,
                        'view_count': getattr(product, 'view_count', 0),
                        'like_count': getattr(product, 'like_count', 0),
                    }
                    products.append(product_dict)
                products_size = len(
                    Product.objects.all().filter(product_minicategor=int(CAT_id), PRDISDeleted = False , PRDISactive = True ))

            max_size = True if upper >= products_size else False
            return JsonResponse({"data": products, "max": max_size, "products_size": products_size, }, safe=False)


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
        if cat_type == "super" and cat_id:
            base_filter['product_supercategory'] = int(cat_id)
        elif cat_type == "main" and cat_id:
            base_filter['product_maincategory'] = int(cat_id)
        elif cat_type == "sub" and cat_id:
            base_filter['product_subcategory'] = int(cat_id)
        elif cat_type == "mini" and cat_id:
            base_filter['product_minicategor'] = int(cat_id)
        
        # Construire le queryset avec annotation pour like_count
        try:
            queryset = Product.objects.filter(**base_filter).annotate(
                like_count=Count('favorites')
            ).order_by(order_by)
        except:
            # Si la table favorites n'existe pas encore
            queryset = Product.objects.filter(**base_filter).order_by(order_by)
        
        return queryset
    
    def get(self, request, *args, **kwargs):
        # Récupérer les paramètres
        page = int(request.GET.get('page', 1))
        order_by = request.GET.get('order_by', '-date')
        cat_type = request.GET.get('cat_type', 'all')
        cat_id = request.GET.get('cat_id', '')
        
        # Construire le queryset
        if cat_type == "all":
            try:
                queryset = Product.objects.filter(
                    PRDISDeleted=False, 
                    PRDISactive=True
                ).annotate(
                    like_count=Count('favorites')
                ).order_by(order_by)
            except:
                queryset = Product.objects.filter(
                    PRDISDeleted=False, 
                    PRDISactive=True
                ).order_by(order_by)
        else:
            queryset = self.get_queryset(cat_type, cat_id, order_by)
        
        # Pagination
        paginator = Paginator(queryset, self.PAGE_SIZE)
        page_obj = paginator.get_page(page)
        
        # Préparer les produits avec leurs images
        import json
        products_data = []
        for product in page_obj:
            # Collecter toutes les images avec le préfixe /media/
            product_images = []
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
            
            products_data.append({
                'product': product,
                'product_images': json.dumps(product_images),  # JSON stringifié pour le template
                'like_count': getattr(product, 'like_count', 0),
            })
        
        # Contexte pour le template
        context = {
            'products_data': products_data,
            'page_obj': page_obj,
            'has_next': page_obj.has_next(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'order_by': order_by,
            'cat_type': cat_type,
            'cat_id': cat_id,
            'total_products': queryset.count(),  # Total de produits pour le compteur
        }
        
        # Rendre le template partiel
        return render(request, 'categories/product_list_partial.html', context)
