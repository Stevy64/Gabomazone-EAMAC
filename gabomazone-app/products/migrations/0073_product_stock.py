from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0072_product_view_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='stock_quantity',
            field=models.PositiveIntegerField(
                default=0,
                help_text='0 = rupture de stock',
                verbose_name='Quantité en stock'
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='is_out_of_stock',
            field=models.BooleanField(default=False, verbose_name='En rupture de stock'),
        ),
    ]
