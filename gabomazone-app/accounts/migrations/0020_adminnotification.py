# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0019_auto_20251212_0626'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('BOOST_REQUEST', 'Demande de boost'), ('PREMIUM_SUBSCRIPTION', 'Abonnement premium'), ('CONTACT_MESSAGE', 'Message de contact'), ('PRODUCT_APPROVAL', 'Approbation de produit')], max_length=50, verbose_name='Type de notification')),
                ('title', models.CharField(max_length=200, verbose_name='Titre')),
                ('message', models.TextField(verbose_name='Message')),
                ('related_object_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='ID de l\'objet')),
                ('related_object_type', models.CharField(blank=True, max_length=100, null=True, verbose_name='Type d\'objet')),
                ('related_url', models.CharField(blank=True, max_length=500, null=True, verbose_name='URL de l\'objet')),
                ('is_read', models.BooleanField(default=False, verbose_name='Lu')),
                ('is_resolved', models.BooleanField(default=False, verbose_name='Résolu')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Date de lecture')),
                ('resolved_at', models.DateTimeField(blank=True, null=True, verbose_name='Date de résolution')),
            ],
            options={
                'verbose_name': 'Notification administrateur',
                'verbose_name_plural': 'Notifications administrateur',
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddIndex(
            model_name='adminnotification',
            index=models.Index(fields=['is_read', 'is_resolved', 'created_at'], name='accounts_ad_is_read_8a3f2a_idx'),
        ),
    ]

