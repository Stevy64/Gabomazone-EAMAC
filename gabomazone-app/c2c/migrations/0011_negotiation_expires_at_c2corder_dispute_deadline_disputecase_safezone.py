from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('c2c', '0010_remove_buyer_commission_rate'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Negotiation.expires_at
        migrations.AddField(
            model_name='negotiation',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Expire le'),
        ),
        # 2. C2COrder.dispute_deadline
        migrations.AddField(
            model_name='c2corder',
            name='dispute_deadline',
            field=models.DateTimeField(
                blank=True, null=True,
                verbose_name='Délai de litige',
                help_text='48h après finalisation — au-delà de ce délai, plus de litige possible',
            ),
        ),
        # 3. DisputeCase
        migrations.CreateModel(
            name='DisputeCase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(
                    choices=[
                        ('not_received', 'Article non recu'),
                        ('not_as_described', "Non conforme a l'annonce"),
                        ('damaged', 'Article endommage'),
                        ('fraud', 'Arnaque suspectee'),
                        ('other', 'Autre motif'),
                    ],
                    max_length=30,
                    verbose_name='Motif',
                )),
                ('description', models.TextField(verbose_name='Description detaillee')),
                ('resolution_notes', models.TextField(blank=True, verbose_name='Notes de resolution')),
                ('status', models.CharField(
                    choices=[
                        ('open', 'Ouvert'),
                        ('under_review', "En cours d'examen"),
                        ('resolved_refund', 'Resolu - Remboursement'),
                        ('resolved_seller', 'Resolu - En faveur du vendeur'),
                        ('closed', 'Cloture'),
                    ],
                    default='open',
                    max_length=20,
                    verbose_name='Statut',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('order', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dispute',
                    to='c2c.c2corder',
                    verbose_name='Commande C2C',
                )),
                ('claimant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='c2c_disputes_filed',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Plaignant',
                )),
                ('mediator', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='c2c_disputes_mediated',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Mediateur',
                )),
            ],
            options={
                'verbose_name': 'Litige C2C',
                'verbose_name_plural': 'Litiges C2C',
                'ordering': ('-created_at',),
            },
        ),
        # 4. SafeZone
        migrations.CreateModel(
            name='SafeZone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nom du point')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('address', models.CharField(max_length=500, verbose_name='Adresse')),
                ('city', models.CharField(default='Libreville', max_length=100, verbose_name='Ville')),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='Latitude')),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='Longitude')),
                ('landmark', models.CharField(blank=True, help_text="Ex: 'En face du Total Leon MBA'", max_length=200, verbose_name='Repere')),
                ('opening_hours', models.CharField(blank=True, default='Lun-Sam 8h-20h', max_length=200, verbose_name='Horaires')),
                ('status', models.CharField(
                    choices=[('active', 'Actif'), ('inactive', 'Inactif')],
                    default='active',
                    max_length=10,
                    verbose_name='Statut',
                )),
                ('is_featured', models.BooleanField(default=False, verbose_name='Mis en avant')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': "Zone d'echange securisee",
                'verbose_name_plural': "Zones d'echange securisees",
                'ordering': ('-is_featured', 'city', 'name'),
            },
        ),
    ]
