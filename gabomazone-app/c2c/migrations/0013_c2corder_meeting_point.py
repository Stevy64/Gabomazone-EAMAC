from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('c2c', '0012_alter_disputecase_id_alter_safezone_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='c2corder',
            name='meeting_type',
            field=models.CharField(
                blank=True, null=True, max_length=20,
                choices=[('safe_zone', 'Zone Gabomazone'), ('custom', 'Point personnalisé')],
                verbose_name='Type de point de rencontre'),
        ),
        migrations.AddField(
            model_name='c2corder',
            name='meeting_safe_zone',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='meetings',
                to='c2c.safezone',
                verbose_name='Zone Gabomazone sélectionnée'),
        ),
        migrations.AddField(
            model_name='c2corder',
            name='meeting_address',
            field=models.CharField(
                blank=True, null=True, max_length=300,
                verbose_name='Adresse du point de rencontre personnalisé'),
        ),
        migrations.AddField(
            model_name='c2corder',
            name='meeting_notes',
            field=models.CharField(
                blank=True, null=True, max_length=200,
                verbose_name='Précisions sur le point de rencontre'),
        ),
        migrations.AddField(
            model_name='c2corder',
            name='meeting_proposed_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='proposed_meetings',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Proposé par'),
        ),
        migrations.AddField(
            model_name='c2corder',
            name='meeting_confirmed_by_buyer',
            field=models.BooleanField(default=False, verbose_name="Confirmé par l'acheteur"),
        ),
        migrations.AddField(
            model_name='c2corder',
            name='meeting_confirmed_by_seller',
            field=models.BooleanField(default=False, verbose_name='Confirmé par le vendeur'),
        ),
    ]
