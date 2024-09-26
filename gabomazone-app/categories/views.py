from urllib import request
from django.shortcuts import render
from .models import SubCategory, MainCategory, SuperCategory, MiniCategory
from django.views.generic import View, TemplateView
from products.models import Product
from django.http import JsonResponse
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
    supercategory = SuperCategory.objects.all()
    maincategory = MainCategory.objects.all()
    subcategory = SubCategory.objects.all()
    minicategory = MiniCategory.objects.all()
    context = {
        'supercategory': supercategory,
        'maincategory': maincategory,
        'subcategory': subcategory,
        'minicategory': minicategory,
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
            products = list(
                Product.objects.all().filter(PRDISDeleted = False , PRDISactive = True ).values().order_by(orderd_by)[lower:upper])
            products_size = len(Product.objects.all().filter(PRDISDeleted = False , PRDISactive = True ))
            max_size = True if upper >= products_size else False
            return JsonResponse({"data": products,  "max": max_size, "products_size": products_size, }, safe=False)

        else:      # 3
            lower = upper - 10
            # print(lower, upper)
            if CAT_type == "super":

                products = list(
                    Product.objects.all().filter(product_supercategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).values().order_by(orderd_by)[lower:upper])
                products_size = len(
                    Product.objects.all().filter(product_supercategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ))
            elif CAT_type == "main":
                products = list(
                    Product.objects.all().filter(product_maincategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).values().order_by(orderd_by)[lower:upper])
                products_size = len(
                    Product.objects.all().filter(product_maincategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ))
            elif CAT_type == "sub":
                products = list(
                    Product.objects.all().filter(product_subcategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).values().order_by(orderd_by)[lower:upper])
                products_size = len(
                    Product.objects.all().filter(product_subcategory=int(CAT_id), PRDISDeleted = False , PRDISactive = True ))

            else:
                products = list(
                    Product.objects.all().filter(product_minicategor=int(CAT_id), PRDISDeleted = False , PRDISactive = True ).values().order_by(orderd_by)[lower:upper])
                products_size = len(
                    Product.objects.all().filter(product_minicategor=int(CAT_id), PRDISDeleted = False , PRDISactive = True ))

            max_size = True if upper >= products_size else False
            return JsonResponse({"data": products, "max": max_size, "products_size": products_size, }, safe=False)
