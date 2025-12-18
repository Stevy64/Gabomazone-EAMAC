# Generated manually for SingPay integration
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orders', '0001_initial'),
        ('products', '0001_initial'),
        ('accounts', '0001_initial'),
        ('payments', '0008_auto_20251205_1354'),
    ]

    operations = [
        migrations.CreateModel(
            name='SingPayTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=100, unique=True, verbose_name='ID Transaction SingPay')),
                ('reference', models.CharField(blank=True, max_length=100, null=True, verbose_name='Référence')),
                ('internal_order_id', models.CharField(help_text='Identifiant interne de la commande/transaction', max_length=100, verbose_name='ID Commande interne')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Montant')),
                ('currency', models.CharField(default='XOF', max_length=3, verbose_name='Devise')),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('success', 'Réussi'), ('failed', 'Échoué'), ('cancelled', 'Annulé'), ('refunded', 'Remboursé')], default='pending', max_length=20, verbose_name='Statut')),
                ('transaction_type', models.CharField(choices=[('order_payment', 'Paiement de commande'), ('boost_payment', 'Paiement boost produit'), ('subscription_payment', 'Paiement abonnement'), ('c2c_payment', 'Paiement entre particuliers'), ('commission_payment', 'Paiement commission')], max_length=30, verbose_name='Type de transaction')),
                ('customer_email', models.EmailField(max_length=254, verbose_name='Email client')),
                ('customer_phone', models.CharField(max_length=20, verbose_name='Téléphone client')),
                ('customer_name', models.CharField(max_length=200, verbose_name='Nom client')),
                ('payment_url', models.URLField(blank=True, null=True, verbose_name='URL de paiement')),
                ('callback_url', models.URLField(verbose_name='URL de callback')),
                ('return_url', models.URLField(verbose_name='URL de retour')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Métadonnées')),
                ('payment_method', models.CharField(blank=True, max_length=50, null=True, verbose_name='Méthode de paiement')),
                ('paid_at', models.DateTimeField(blank=True, null=True, verbose_name='Date de paiement')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Date d\'expiration')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='orders.order', verbose_name='Commande')),
                ('peer_product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.peertopeerproduct', verbose_name='Article entre particuliers')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.product', verbose_name='Produit')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'Transaction SingPay',
                'verbose_name_plural': 'Transactions SingPay',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='SingPayWebhookLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payload', models.JSONField(verbose_name='Payload reçu')),
                ('signature', models.CharField(max_length=200, verbose_name='Signature')),
                ('timestamp', models.CharField(max_length=50, verbose_name='Timestamp')),
                ('is_valid', models.BooleanField(default=False, verbose_name='Signature valide')),
                ('processed', models.BooleanField(default=False, verbose_name='Traité')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name='Message d\'erreur')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de réception')),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhook_logs', to='payments.singpaytransaction', verbose_name='Transaction')),
            ],
            options={
                'verbose_name': 'Log Webhook SingPay',
                'verbose_name_plural': 'Logs Webhooks SingPay',
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddIndex(
            model_name='singpaytransaction',
            index=models.Index(fields=['transaction_id'], name='payments_si_transac_8a1b2d_idx'),
        ),
        migrations.AddIndex(
            model_name='singpaytransaction',
            index=models.Index(fields=['internal_order_id'], name='payments_si_interna_9c2d3e_idx'),
        ),
        migrations.AddIndex(
            model_name='singpaytransaction',
            index=models.Index(fields=['status'], name='payments_si_status_4d5e6f_idx'),
        ),
        migrations.AddIndex(
            model_name='singpaytransaction',
            index=models.Index(fields=['user'], name='payments_si_user_id_7g8h9i_idx'),
        ),
        migrations.AddField(
            model_name='vendorpayments',
            name='singpay_transaction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='payments.singpaytransaction', verbose_name='Transaction SingPay'),
        ),
    ]




