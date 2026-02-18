# Migration: Payment.service_fee_amount + B2CDeliveryVerification

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0038_merge_20260205_2257'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='service_fee_amount',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12, null=True,
                verbose_name='Frais de service (paiement à la livraison)'),
        ),
        migrations.CreateModel(
            name='B2CDeliveryVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seller_code', models.CharField(max_length=6, unique=True, verbose_name='Code vendeur (V-CODE)')),
                ('buyer_code', models.CharField(max_length=6, unique=True, verbose_name='Code client (A-CODE)')),
                ('seller_code_verified', models.BooleanField(default=False, verbose_name='Code vendeur vérifié')),
                ('buyer_code_verified', models.BooleanField(default=False, verbose_name='Code client vérifié')),
                ('seller_code_verified_at', models.DateTimeField(blank=True, null=True, verbose_name='Date vérification code vendeur')),
                ('buyer_code_verified_at', models.DateTimeField(blank=True, null=True, verbose_name='Date vérification code client')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'En attente'),
                        ('seller_code_verified', 'Code vendeur/livreur vérifié'),
                        ('buyer_code_verified', 'Code client vérifié'),
                        ('completed', 'Terminé'),
                        ('disputed', 'Litige'),
                    ],
                    default='pending',
                    max_length=30,
                    verbose_name='Statut',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Date de finalisation')),
                ('order', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='b2c_delivery_verification',
                    to='orders.order',
                    verbose_name='Commande B2C',
                )),
            ],
            options={
                'verbose_name': 'Vérification livraison B2C',
                'verbose_name_plural': 'Vérifications livraison B2C',
                'ordering': ('-created_at',),
            },
        ),
    ]
