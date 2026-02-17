# Generated manually to add escrow fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0011_auto_20251218_0159'),
    ]

    operations = [
        migrations.AddField(
            model_name='singpaytransaction',
            name='escrow_status',
            field=models.CharField(
                choices=[
                    ('none', 'Pas d\'escrow'),
                    ('escrow_pending', 'Fonds en escrow'),
                    ('escrow_released', 'Fonds libérés'),
                    ('escrow_refunded', 'Fonds remboursés')
                ],
                default='none',
                help_text='Statut des fonds en escrow (séquestre)',
                max_length=20,
                verbose_name='Statut escrow'
            ),
        ),
        migrations.AddField(
            model_name='singpaytransaction',
            name='escrow_released_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Date de libération escrow'
            ),
        ),
        migrations.AddField(
            model_name='singpaytransaction',
            name='disbursement_id',
            field=models.CharField(
                blank=True,
                help_text='ID du virement SingPay pour la libération des fonds',
                max_length=100,
                null=True,
                verbose_name='ID Disbursement'
            ),
        ),
    ]

