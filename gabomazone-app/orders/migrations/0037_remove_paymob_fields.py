from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0036_auto_20251203_0304'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='auth_token_order',
        ),
        migrations.RemoveField(
            model_name='order',
            name='merchant_order_id',
        ),
        migrations.RemoveField(
            model_name='order',
            name='order_id_paymob',
        ),
        migrations.RemoveField(
            model_name='order',
            name='trnx_id',
        ),
    ]

