# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0019_auto_20251212_0626'),
        ('c2c', '0003_auto_20251218_0159'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuyerReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveIntegerField(help_text='Note de 1 à 5 étoiles', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Note')),
                ('comment', models.TextField(blank=True, help_text='Commentaire optionnel sur la transaction', null=True, verbose_name='Commentaire')),
                ('is_visible', models.BooleanField(default=True, help_text="Si False, l'avis est masqué (modération)", verbose_name='Visible')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_reviews', to=settings.AUTH_USER_MODEL, verbose_name='Acheteur')),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_review', to='c2c.c2corder', verbose_name='Commande')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_reviews', to='accounts.peertopeerproduct', verbose_name='Article')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_reviews_given', to=settings.AUTH_USER_MODEL, verbose_name="Auteur de l'avis")),
            ],
            options={
                'verbose_name': 'Avis acheteur',
                'verbose_name_plural': 'Avis acheteurs',
                'ordering': ('-created_at',),
                'unique_together': {('order', 'reviewer')},
            },
        ),
        migrations.AddIndex(
            model_name='buyerreview',
            index=models.Index(fields=['buyer', 'is_visible'], name='c2c_buyerre_buyer__idx'),
        ),
        migrations.AddIndex(
            model_name='buyerreview',
            index=models.Index(fields=['rating'], name='c2c_buyerre_rating_idx'),
        ),
    ]


