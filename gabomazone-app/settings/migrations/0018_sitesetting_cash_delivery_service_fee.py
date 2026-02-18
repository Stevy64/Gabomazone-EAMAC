# Migration: SiteSetting.cash_delivery_service_fee

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0017_auto_20220814_0432'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='cash_delivery_service_fee',
            field=models.DecimalField(
                blank=True, decimal_places=2, default=500, max_digits=12, null=True,
                verbose_name='Frais de service paiement à la livraison (FCFA)'),
        ),
    ]
