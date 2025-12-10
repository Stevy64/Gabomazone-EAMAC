# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_premium_subscription_and_boost'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Ajouter view_count à PeerToPeerProduct
        migrations.AddField(
            model_name='peertopeerproduct',
            name='view_count',
            field=models.PositiveIntegerField(default=0, verbose_name='Nombre de vues'),
        ),
        # Créer PeerToPeerProductFavorite
        migrations.CreateModel(
            name='PeerToPeerProductFavorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, help_text='Pour les utilisateurs non authentifiés', max_length=40, null=True, verbose_name='Session Key')),
                ('date', models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to='accounts.peertopeerproduct', verbose_name='Article entre particuliers')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='peer_to_peer_product_favorites', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Favori Article entre particuliers',
                'verbose_name_plural': 'Favoris Articles entre particuliers',
                'unique_together': {('product', 'user'), ('product', 'session_key')},
            },
        ),
    ]




