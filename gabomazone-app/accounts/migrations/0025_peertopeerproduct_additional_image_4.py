from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0024_condition_values_no_underscores'),
    ]

    operations = [
        migrations.AddField(
            model_name='peertopeerproduct',
            name='additional_image_4',
            field=models.ImageField(
                blank=True,
                max_length=500,
                null=True,
                upload_to='peer_to_peer/imgs/',
                verbose_name='Image supplémentaire 4',
            ),
        ),
    ]
