# 📋 Instructions pour appliquer les migrations C2C

## ⚠️ Erreur actuelle

```
OperationalError: no such table: c2c_purchaseintent
```

**Cause** : Les migrations ont été créées mais pas encore appliquées à la base de données.

## ✅ Solution en 3 étapes

### Étape 1 : Appliquer les migrations

Dans votre terminal, exécutez :

```bash
cd gabomazone-app
python manage.py migrate c2c
```

Vous devriez voir :
```
Operations to perform:
  Apply all migrations: c2c
Running migrations:
  Applying c2c.0001_initial... OK
```

### Étape 2 : Créer les paramètres par défaut

```bash
python manage.py shell
```

Puis dans le shell Python :

```python
from c2c.models import PlatformSettings

# Créer les paramètres par défaut
if not PlatformSettings.objects.exists():
    settings = PlatformSettings.objects.create(
        c2c_buyer_commission_rate=5.90,
        c2c_seller_commission_rate=9.90,
        b2c_buyer_commission_rate=0.00,
        b2c_seller_commission_rate=10.00,
        is_active=True
    )
    print("✅ Paramètres créés avec succès !")
else:
    print("✅ Paramètres déjà existants")
```

### Étape 3 : Redémarrer le serveur

```bash
# Arrêter le serveur (Ctrl+C)
# Puis redémarrer
python manage.py runserver
```

## 🔍 Vérification

1. Aller sur `/admin/c2c/`
2. Vérifier que les modèles suivants sont visibles :
   - Platform Settings
   - Purchase Intents
   - Negotiations
   - C2C Orders
   - Delivery Verifications
   - Product Boosts
   - Seller Badges

3. Tester la création d'une intention d'achat :
   - Aller sur un produit peer-to-peer
   - Cliquer sur "Proposer une offre"
   - Vérifier que la page s'affiche sans erreur

## 🐛 Problèmes possibles

### Erreur : "django.db.migrations.exceptions.InconsistentMigrationHistory"

**Solution** :
```bash
# Appliquer toutes les migrations
python manage.py migrate
```

### Erreur : "no such module named 'c2c'"

**Solution** : Vérifiez que `c2c` est dans `INSTALLED_APPS` dans `project/settings.py`

### Les tables ne sont pas créées

**Solution** :
```bash
# Vérifier l'état des migrations
python manage.py showmigrations c2c

# Si [ ] 0001_initial (pas de X), appliquer :
python manage.py migrate c2c
```

## ✅ Une fois les migrations appliquées

Le module C2C sera opérationnel et vous pourrez :
- ✅ Créer des intentions d'achat
- ✅ Négocier des prix
- ✅ Créer des commandes C2C
- ✅ Utiliser le système de double code
- ✅ Gérer les commissions depuis l'admin

## 📞 Support

Si vous rencontrez d'autres problèmes, consultez :
- `INSTALLATION.md` : Guide d'installation complet
- `TESTING.md` : Guide de test
- `README.md` : Documentation complète

