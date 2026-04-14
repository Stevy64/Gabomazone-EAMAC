"""
Correctif 1 — Commission uniquement côté vendeur.

- Supprime le champ c2c_buyer_commission_rate de PlatformSettings
- Met à 0 tous les buyer_commission existants sur C2COrder
- Met buyer_total = final_price pour tous les C2COrder existants
- Agrandit seller_code/buyer_code à max_length=9 (format GM-XXXXXX)
"""
from django.db import migrations, models
from decimal import Decimal


def reset_buyer_commissions(apps, schema_editor):
    C2COrder = apps.get_model('c2c', 'C2COrder')
    from django.db.models import F
    C2COrder.objects.update(
        buyer_commission=Decimal('0'),
        buyer_total=F('final_price'),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('c2c', '0009_purchaseintent_availability'),
    ]

    operations = [
        # 1. Supprimer c2c_buyer_commission_rate de PlatformSettings
        migrations.RemoveField(
            model_name='platformsettings',
            name='c2c_buyer_commission_rate',
        ),
        # 2. Remettre à zéro buyer_commission et aligner buyer_total sur final_price
        migrations.RunPython(reset_buyer_commissions, migrations.RunPython.noop),
        # 3. Agrandir les champs codes de vérification (max_length 6 → 9)
        migrations.AlterField(
            model_name='deliveryverification',
            name='seller_code',
            field=models.CharField(max_length=9, unique=True, verbose_name='Code vendeur'),
        ),
        migrations.AlterField(
            model_name='deliveryverification',
            name='buyer_code',
            field=models.CharField(max_length=9, unique=True, verbose_name='Code acheteur'),
        ),
    ]
