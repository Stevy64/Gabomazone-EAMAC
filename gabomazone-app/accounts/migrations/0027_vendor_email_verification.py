from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0022_remove_paypal_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='vendor_verification_token',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True, verbose_name='Token de vérification vendeur'),
        ),
        migrations.AddField(
            model_name='profile',
            name='vendor_verification_sent_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name="Date d'envoi du lien de vérification"),
        ),
    ]
