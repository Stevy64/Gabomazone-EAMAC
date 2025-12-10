# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0071_recreate_productfavorite'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='view_count',
            field=models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Nombre de vues'),
        ),
    ]




