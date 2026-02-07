from django.db import migrations, models


def condition_underscore_to_space(apps, schema_editor):
    PeerToPeerProduct = apps.get_model('accounts', 'PeerToPeerProduct')
    mapping = {
        'BON_ETAT': 'BON ETAT',
        'COMME_NEUF': 'COMME NEUF',
    }
    for old, new in mapping.items():
        PeerToPeerProduct.objects.filter(condition=old).update(condition=new)


def condition_space_to_underscore(apps, schema_editor):
    PeerToPeerProduct = apps.get_model('accounts', 'PeerToPeerProduct')
    mapping = {
        'BON ETAT': 'BON_ETAT',
        'COMME NEUF': 'COMME_NEUF',
    }
    for new, old in mapping.items():
        PeerToPeerProduct.objects.filter(condition=new).update(condition=old)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0023_peertopeerproduct_condition'),
    ]

    operations = [
        migrations.RunPython(condition_underscore_to_space, condition_space_to_underscore),
        migrations.AlterField(
            model_name='peertopeerproduct',
            name='condition',
            field=models.CharField(
                blank=True,
                choices=[
                    ('NEUF', 'Neuf'),
                    ('COMME NEUF', 'Comme neuf'),
                    ('BON ETAT', 'Bon état'),
                    ('UTILISABLE', 'Utilisable'),
                ],
                default='BON ETAT',
                max_length=20,
                verbose_name="État de l'article",
            ),
        ),
    ]
