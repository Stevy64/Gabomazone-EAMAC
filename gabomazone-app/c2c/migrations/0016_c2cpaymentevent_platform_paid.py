# Generated migration for adding PLATFORM_PAID event type

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('c2c', '0015_platformsettings_popular_meeting_min_uses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='c2cpaymentevent',
            name='event_type',
            field=models.CharField(
                choices=[
                    ('created', 'Commande créée'),
                    ('paid_escrow', 'Paiement reçu (fonds en escrow)'),
                    ('seller_code_verified', 'Code vendeur vérifié'),
                    ('buyer_code_verified', 'Code acheteur vérifié'),
                    ('released', 'Fonds libérés au vendeur'),
                    ('platform_paid', 'Commission plateforme versée'),
                    ('cancelled_refund', 'Annulation / Remboursement (frais gardés)'),
                ],
                max_length=30,
                verbose_name='Étape',
            ),
        ),
    ]
