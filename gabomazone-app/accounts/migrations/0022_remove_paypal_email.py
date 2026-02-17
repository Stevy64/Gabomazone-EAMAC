from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_auto_20251218_0159'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bankaccount',
            name='paypal_email',
        ),
    ]

