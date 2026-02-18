# Generated manually for C2C payment events (traçabilité escrow)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0013_alter_vendorpayments_method'),
        ('c2c', '0005_auto_20251218_0246'),
    ]

    operations = [
        migrations.CreateModel(
            name='C2CPaymentEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('created', 'Commande créée'), ('paid_escrow', 'Paiement reçu (fonds en escrow)'), ('seller_code_verified', 'Code vendeur vérifié'), ('buyer_code_verified', 'Code acheteur vérifié'), ('released', 'Fonds libérés au vendeur'), ('cancelled_refund', 'Annulation / Remboursement (frais gardés)')], max_length=30, verbose_name='Étape')),
                ('amount_refunded', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Montant remboursé')),
                ('commission_retained', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Frais de service gardés')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Métadonnées')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
                ('c2c_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_events', to='c2c.c2corder', verbose_name='Commande C2C')),
                ('transaction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='c2c_payment_events', to='payments.singpaytransaction', verbose_name='Transaction SingPay')),
            ],
            options={
                'verbose_name': 'Événement paiement C2C',
                'verbose_name_plural': 'Événements paiement C2C',
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddIndex(
            model_name='c2cpaymentevent',
            index=models.Index(fields=['c2c_order', 'event_type'], name='c2c_c2cpaym_c2c_ord_6b2e8a_idx'),
        ),
        migrations.AddIndex(
            model_name='c2cpaymentevent',
            index=models.Index(fields=['created_at'], name='c2c_c2cpaym_created_8a1f0d_idx'),
        ),
    ]
