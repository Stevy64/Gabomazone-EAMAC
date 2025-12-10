# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_add_view_count_and_favorites'),
        ('orders', '0036_auto_20251203_0304'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Rendre product nullable
        migrations.AlterField(
            model_name='orderdetails',
            name='product',
            field=models.ForeignKey(
                'products.Product',
                on_delete=models.CASCADE,
                blank=True,
                null=True
            ),
        ),
        # Ajouter peer_product
        migrations.AddField(
            model_name='orderdetails',
            name='peer_product',
            field=models.ForeignKey(
                'accounts.PeerToPeerProduct',
                on_delete=models.CASCADE,
                blank=True,
                null=True,
                verbose_name='Article entre particuliers'
            ),
        ),
    ]

