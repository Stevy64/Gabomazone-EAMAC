from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0032_alter_adminnotification_notification_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_identity_verified',
            field=models.BooleanField(
                default=False,
                help_text='Badge de vérification d\'identité accordé par l\'administrateur',
                verbose_name='Identité vérifiée',
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='identity_verified_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Date de vérification d\'identité',
            ),
        ),
    ]
