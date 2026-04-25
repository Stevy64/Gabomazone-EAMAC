from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0057_auto_20220504_0220'),
        ('accounts', '0033_profile_identity_verification'),
    ]

    operations = [
        migrations.CreateModel(
            name='B2CProductConversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_message_at', models.DateTimeField(auto_now_add=True, verbose_name='Dernier message')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='b2c_customer_conversations', to=settings.AUTH_USER_MODEL, verbose_name='Client')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='b2c_conversations', to='products.product', verbose_name='Produit B2C')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='b2c_vendor_conversations', to=settings.AUTH_USER_MODEL, verbose_name='Vendeur pro')),
            ],
            options={
                'verbose_name': 'Conversation B2C',
                'verbose_name_plural': 'Conversations B2C',
                'ordering': ('-last_message_at',),
                'unique_together': {('product', 'vendor', 'customer')},
            },
        ),
        migrations.CreateModel(
            name='B2CProductMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(verbose_name='Message')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('is_read', models.BooleanField(default=False, verbose_name='Lu')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Date de lecture')),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='accounts.b2cproductconversation', verbose_name='Conversation B2C')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='b2c_sent_messages', to=settings.AUTH_USER_MODEL, verbose_name='Expéditeur')),
            ],
            options={
                'verbose_name': 'Message B2C',
                'verbose_name_plural': 'Messages B2C',
                'ordering': ('created_at',),
            },
        ),
    ]
