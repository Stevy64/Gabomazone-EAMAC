# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0019_auto_20251212_0626'),
        ('c2c', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SellerReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveIntegerField(help_text='Note de 1 à 5 étoiles', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Note')),
                ('comment', models.TextField(blank=True, help_text='Commentaire optionnel sur la transaction', null=True, verbose_name='Commentaire')),
                ('is_visible', models.BooleanField(default=True, help_text='Si False, l\'avis est masqué (modération)', verbose_name='Visible')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='review', to='c2c.c2corder', verbose_name='Commande')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='accounts.peertopeerproduct', verbose_name='Article')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews_given', to=settings.AUTH_USER_MODEL, verbose_name='Auteur de l\'avis')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_reviews', to=settings.AUTH_USER_MODEL, verbose_name='Vendeur')),
            ],
            options={
                'verbose_name': 'Avis vendeur',
                'verbose_name_plural': 'Avis vendeurs',
                'ordering': ('-created_at',),
                'unique_together': {('order', 'reviewer')},
            },
        ),
        migrations.AddIndex(
            model_name='sellerreview',
            index=models.Index(fields=['seller', 'is_visible'], name='c2c_sellerr_seller__idx'),
        ),
        migrations.AddIndex(
            model_name='sellerreview',
            index=models.Index(fields=['rating'], name='c2c_sellerr_rating_idx'),
        ),
    ]


