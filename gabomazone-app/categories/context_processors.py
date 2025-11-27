
from .models import SubCategory, MainCategory, SuperCategory, MiniCategory


def category_obj(request):
    supercategory = SuperCategory.objects.all()
    maincategory = MainCategory.objects.all()
    subcategory = SubCategory.objects.all()
    minicategory = MiniCategory.objects.all()
    return {
        'supercategory': supercategory,
        'maincategory': maincategory,
        'subcategory': subcategory,
        'minicategory': minicategory, }
