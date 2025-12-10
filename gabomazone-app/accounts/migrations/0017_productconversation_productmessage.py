# Generated manually for ProductConversation and ProductMessage models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0016_peertopeerordernotification'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductConversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('last_message_at', models.DateTimeField(auto_now_add=True, verbose_name='Dernier message')),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_conversations', to=settings.AUTH_USER_MODEL, verbose_name='Acheteur')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to='accounts.peertopeerproduct', verbose_name='Article')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_conversations', to=settings.AUTH_USER_MODEL, verbose_name='Vendeur')),
            ],
            options={
                'verbose_name': 'Conversation',
                'verbose_name_plural': 'Conversations',
                'ordering': ('-last_message_at',),
                'unique_together': {('product', 'buyer')},
            },
        ),
        migrations.CreateModel(
            name='ProductMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(verbose_name='Message')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('is_read', models.BooleanField(default=False, verbose_name='Lu')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Date de lecture')),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='accounts.productconversation', verbose_name='Conversation')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL, verbose_name='Expéditeur')),
            ],
            options={
                'verbose_name': 'Message',
                'verbose_name_plural': 'Messages',
                'ordering': ('created_at',),
            },
        ),
    ]

