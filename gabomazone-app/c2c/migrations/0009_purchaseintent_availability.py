from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('c2c', '0008_deliveryverification_handover_confirm'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseintent',
            name='availability_confirmed_at',
            field=models.DateTimeField(
                blank=True, null=True,
                verbose_name="Disponibilité confirmée par le vendeur",
            ),
        ),
        migrations.AlterField(
            model_name='purchaseintent',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'En attente'),
                    ('awaiting_availability', 'En attente de disponibilité'),
                    ('negotiating', 'En négociation'),
                    ('agreed', 'Accord trouvé'),
                    ('rejected', 'Refusé'),
                    ('cancelled', 'Annulé'),
                    ('expired', 'Expiré'),
                ],
                default='pending',
                max_length=25,
                verbose_name='Statut',
            ),
        ),
    ]
