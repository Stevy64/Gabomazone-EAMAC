from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0022_remove_paypal_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='peertopeerproduct',
            name='condition',
            field=models.CharField(
                blank=True,
                choices=[
                    ('NEUF', 'Neuf'),
                    ('COMME_NEUF', 'Comme neuf'),
                    ('BON_ETAT', 'Bon état'),
                    ('UTILISABLE', 'Utilisable'),
                ],
                default='BON_ETAT',
                max_length=20,
                verbose_name="État de l'article",
            ),
        ),
    ]
