# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0001_initial'),
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0012_auto_20220814_0432'),
    ]

    operations = [
        migrations.CreateModel(
            name='PeerToPeerProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=150, verbose_name='Nom du produit')),
                ('product_description', models.TextField(verbose_name='Description')),
                ('product_image', models.ImageField(default='peer_to_peer/product.jpg', max_length=500, upload_to='peer_to_peer/imgs/', verbose_name='Image du produit')),
                ('PRDPrice', models.FloatField(verbose_name='Prix')),
                ('commission_rate', models.FloatField(default=0.2, verbose_name='Taux de commission (20%)')),
                ('commission_amount', models.FloatField(blank=True, null=True, verbose_name='Montant de la commission')),
                ('seller_amount', models.FloatField(blank=True, null=True, verbose_name='Montant pour le vendeur')),
                ('additional_image_1', models.ImageField(blank=True, max_length=500, null=True, upload_to='peer_to_peer/imgs/', verbose_name='Image supplémentaire 1')),
                ('additional_image_2', models.ImageField(blank=True, max_length=500, null=True, upload_to='peer_to_peer/imgs/', verbose_name='Image supplémentaire 2')),
                ('additional_image_3', models.ImageField(blank=True, max_length=500, null=True, upload_to='peer_to_peer/imgs/', verbose_name='Image supplémentaire 3')),
                ('status', models.CharField(choices=[('PENDING', 'En attente'), ('APPROVED', 'Approuvé'), ('REJECTED', 'Rejeté'), ('SOLD', 'Vendu'), ('CANCELLED', 'Annulé')], default='PENDING', max_length=13, verbose_name='Statut')),
                ('seller_phone', models.CharField(max_length=20, verbose_name='Téléphone du vendeur')),
                ('seller_address', models.TextField(verbose_name='Adresse du vendeur')),
                ('seller_city', models.CharField(max_length=100, verbose_name='Ville')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('date_update', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('approved_date', models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")),
                ('PRDSlug', models.SlugField(allow_unicode=True, blank=True, max_length=150, null=True, unique=True, verbose_name='Slug')),
                ('product_maincategory', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='categories.maincategory', verbose_name='Catégorie principale')),
                ('product_subcategory', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='categories.subcategory', verbose_name='Sous-catégorie')),
                ('product_supercategory', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='categories.supercategory', verbose_name='Super Catégorie')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='peer_to_peer_products', to=settings.AUTH_USER_MODEL, verbose_name='Vendeur')),
            ],
            options={
                'verbose_name': 'Article entre particuliers',
                'verbose_name_plural': 'Articles entre particuliers',
                'ordering': ('-date',),
            },
        ),
        migrations.CreateModel(
            name='DeliveryCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, unique=True, verbose_name='Code de livraison')),
                ('status', models.CharField(choices=[('PENDING', 'En attente'), ('VERIFIED', 'Vérifié'), ('EXPIRED', 'Expiré')], default='PENDING', max_length=13, verbose_name='Statut')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('verified_date', models.DateTimeField(blank=True, null=True, verbose_name='Date de vérification')),
                ('expires_date', models.DateTimeField(blank=True, null=True, verbose_name="Date d'expiration")),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_codes_received', to=settings.AUTH_USER_MODEL, verbose_name='Acheteur')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='delivery_codes', to='orders.order', verbose_name='Commande')),
                ('peer_to_peer_product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_codes', to='accounts.peertopeerproduct', verbose_name='Article')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_codes_sent', to=settings.AUTH_USER_MODEL, verbose_name='Vendeur')),
            ],
            options={
                'verbose_name': 'Code de livraison',
                'verbose_name_plural': 'Codes de livraison',
                'ordering': ('-created_date',),
            },
        ),
    ]





