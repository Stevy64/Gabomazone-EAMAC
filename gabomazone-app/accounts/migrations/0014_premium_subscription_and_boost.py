# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0072_product_view_count'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0013_peertopeerproduct_deliverycode'),
    ]

    operations = [
        migrations.CreateModel(
            name='PremiumSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('ACTIVE', 'Actif'), ('EXPIRED', 'Expiré'), ('CANCELLED', 'Annulé'), ('PENDING', 'En attente')], default='PENDING', max_length=13, verbose_name='Statut')),
                ('start_date', models.DateTimeField(verbose_name='Date de début')),
                ('end_date', models.DateTimeField(verbose_name='Date de fin')),
                ('price', models.FloatField(default=0.0, verbose_name='Prix')),
                ('payment_status', models.BooleanField(default=False, verbose_name='Paiement effectué')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_date', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('vendor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='premium_subscription', to='accounts.profile', verbose_name='Vendeur')),
            ],
            options={
                'verbose_name': 'Abonnement Premium',
                'verbose_name_plural': 'Abonnements Premium',
                'ordering': ('-created_date',),
            },
        ),
        migrations.CreateModel(
            name='ProductBoostRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'En attente'), ('APPROVED', 'Approuvé'), ('REJECTED', 'Rejeté'), ('ACTIVE', 'Actif'), ('EXPIRED', 'Expiré')], default='PENDING', max_length=13, verbose_name='Statut')),
                ('duration_days', models.PositiveIntegerField(default=7, verbose_name='Durée (jours)')),
                ('boost_percentage', models.FloatField(default=10.0, verbose_name='Pourcentage de boost')),
                ('price', models.FloatField(default=0.0, verbose_name='Prix')),
                ('payment_status', models.BooleanField(default=False, verbose_name='Paiement effectué')),
                ('start_date', models.DateTimeField(blank=True, null=True, verbose_name='Date de début')),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name='Date de fin')),
                ('admin_notes', models.TextField(blank=True, null=True, verbose_name='Notes administrateur')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_date', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('approved_date', models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boost_requests', to='products.product', verbose_name='Produit')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boost_requests', to='accounts.profile', verbose_name='Vendeur')),
            ],
            options={
                'verbose_name': 'Demande de Boost Produit',
                'verbose_name_plural': 'Demandes de Boost Produit',
                'ordering': ('-created_date',),
            },
        ),
    ]




