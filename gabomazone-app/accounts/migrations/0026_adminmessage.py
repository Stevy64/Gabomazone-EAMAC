# Migration: AdminMessage (messages admin → utilisateurs)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0025_peertopeerproduct_additional_image_4'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200, verbose_name='Objet')),
                ('body', models.TextField(verbose_name='Message')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Lu le')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Envoyé le')),
                ('email_sent', models.BooleanField(default=False, help_text='Copie envoyée par email au destinataire', verbose_name='Email envoyé')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admin_messages_received', to=settings.AUTH_USER_MODEL, verbose_name='Destinataire')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admin_messages_sent', to=settings.AUTH_USER_MODEL, verbose_name='Expéditeur (admin)')),
            ],
            options={
                'verbose_name': 'Message admin → utilisateur',
                'verbose_name_plural': 'Messages admin → utilisateurs',
                'ordering': ('-created_at',),
            },
        ),
    ]
