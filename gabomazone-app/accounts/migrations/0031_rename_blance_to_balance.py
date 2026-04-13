from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0030_auto_20260331_2352'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='blance',
            new_name='balance',
        ),
    ]
