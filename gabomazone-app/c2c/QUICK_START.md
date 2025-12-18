# 🚀 Démarrage rapide - Module C2C

## ⚠️ Erreur : "no such table: c2c_purchaseintent"

Cette erreur signifie que les migrations n'ont pas été appliquées.

## ✅ Solution rapide

### 1. Appliquer les migrations

```bash
cd gabomazone-app
python manage.py migrate c2c
```

### 2. Vérifier que les migrations sont appliquées

```bash
python manage.py showmigrations c2c
```

Vous devriez voir :
```
c2c
 [X] 0001_initial
```

### 3. Créer les paramètres par défaut

```bash
python manage.py shell
```

```python
from c2c.models import PlatformSettings

# Vérifier si les paramètres existent déjà
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

### 4. Redémarrer le serveur

```bash
python manage.py runserver
```

## 🔍 Vérification

1. Aller sur `/admin/c2c/`
2. Vérifier que les modèles C2C sont visibles
3. Tester la création d'une intention d'achat

## 🐛 Si les migrations échouent

### Erreur de dépendance

Si vous voyez une erreur comme :
```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

Solution :
```bash
# Vérifier l'état des migrations
python manage.py showmigrations accounts
python manage.py showmigrations payments

# Appliquer toutes les migrations
python manage.py migrate
```

### Erreur de table manquante

Si une table de dépendance manque :
```bash
# Appliquer toutes les migrations
python manage.py migrate
```

## 📝 Commandes utiles

```bash
# Voir l'état des migrations
python manage.py showmigrations

# Créer les migrations (si modèles modifiés)
python manage.py makemigrations c2c

# Appliquer les migrations
python manage.py migrate c2c

# Appliquer toutes les migrations
python manage.py migrate
```

## ✅ Checklist

- [ ] Migrations créées : `python manage.py makemigrations c2c`
- [ ] Migrations appliquées : `python manage.py migrate c2c`
- [ ] Paramètres créés : Via le shell Django
- [ ] Serveur redémarré
- [ ] Test de création d'intention d'achat réussi

Une fois ces étapes complétées, l'erreur devrait disparaître ! 🎉


