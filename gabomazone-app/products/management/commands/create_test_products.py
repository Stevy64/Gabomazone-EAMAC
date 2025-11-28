from django.core.management.base import BaseCommand
from products.models import Product
from categories.models import SuperCategory
from django.utils.text import slugify
from django.core.files.base import ContentFile
from PIL import Image
import io


class Command(BaseCommand):
    help = 'Crée 4 produits de test pour le rendu'

    def handle(self, *args, **options):
        # Récupérer ou créer une supercatégorie de test
        super_category = SuperCategory.objects.first()
        if not super_category:
            self.stdout.write(self.style.ERROR('Aucune supercatégorie trouvée. Veuillez d\'abord créer une catégorie.'))
            return

        # Créer une image de test simple (carré coloré)
        def create_test_image(color_name, color_rgb):
            img = Image.new('RGB', (400, 400), color_rgb)
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG', quality=85)
            img_io.seek(0)
            return ContentFile(img_io.read(), name=f'{color_name}_test.jpg')

        # Produits de test
        test_products = [
            {
                'product_name': 'Stylo Bic Bleu Premium',
                'product_description': 'Stylo à bille de qualité supérieure, encre bleue fluide. Parfait pour l\'écriture quotidienne et les prises de notes professionnelles.',
                'PRDPrice': 500.0,
                'PRDDiscountPrice': 0,
                'color': ('blue', (70, 130, 180)),
            },
            {
                'product_name': 'Cahier A4 96 Pages',
                'product_description': 'Cahier à spirale avec 96 pages lignées, format A4. Couverture rigide et pages détachables. Idéal pour les étudiants et professionnels.',
                'PRDPrice': 2500.0,
                'PRDDiscountPrice': 2000.0,
                'color': ('green', (144, 238, 144)),
            },
            {
                'product_name': 'Calculatrice Scientifique',
                'product_description': 'Calculatrice scientifique avec écran LCD, fonctions avancées pour les mathématiques et les sciences. Alimentée par pile solaire.',
                'PRDPrice': 8000.0,
                'PRDDiscountPrice': 0,
                'color': ('orange', (255, 165, 0)),
            },
            {
                'product_name': 'Trousse Scolaire Multicolore',
                'product_description': 'Trousse scolaire spacieuse avec plusieurs compartiments. Design moderne et coloré, parfaite pour ranger tous vos accessoires d\'écriture.',
                'PRDPrice': 3500.0,
                'PRDDiscountPrice': 3000.0,
                'color': ('purple', (186, 85, 211)),
            },
        ]

        created_count = 0
        for product_data in test_products:
            # Vérifier si le produit existe déjà
            slug = slugify(product_data['product_name'], allow_unicode=True)
            if Product.objects.filter(PRDSlug=slug).exists():
                self.stdout.write(self.style.WARNING(f'Le produit "{product_data["product_name"]}" existe déjà. Ignoré.'))
                continue

            # Créer l'image de test
            test_image = create_test_image(product_data['color'][0], product_data['color'][1])

            # Créer le produit
            product = Product.objects.create(
                product_name=product_data['product_name'],
                product_description=product_data['product_description'],
                product_image=test_image,
                product_supercategory=super_category,
                PRDPrice=product_data['PRDPrice'],
                PRDDiscountPrice=product_data['PRDDiscountPrice'],
                PRDISactive=True,
                PRDISDeleted=False,
                available=50,
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'✓ Produit créé: {product.product_name} (Slug: {product.PRDSlug})'))

        self.stdout.write(self.style.SUCCESS(f'\n{created_count} produit(s) de test créé(s) avec succès!'))

