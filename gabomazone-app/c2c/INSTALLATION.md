# Guide d'installation du module C2C

## 📋 Prérequis

- Django 3.2+
- Application `accounts` avec le modèle `PeerToPeerProduct`
- Application `payments` avec le modèle `SingPayTransaction`

## 🚀 Installation

### 1. Vérifier que l'application est dans INSTALLED_APPS

Dans `project/settings.py`, vérifiez que `c2c` est dans `INSTALLED_APPS` :

```python
INSTALLED_APPS = [
    # ...
    'c2c',
]
```

### 2. Créer les migrations

```bash
cd gabomazone-app
python manage.py makemigrations c2c
python manage.py migrate c2c
```

### 3. Créer les paramètres par défaut de la plateforme

```bash
python manage.py shell
```

```python
from c2c.models import PlatformSettings

# Créer les paramètres par défaut
settings = PlatformSettings.objects.create(
    c2c_buyer_commission_rate=5.90,
    c2c_seller_commission_rate=9.90,
    b2c_buyer_commission_rate=0.00,
    b2c_seller_commission_rate=10.00,
    is_active=True
)
print("Paramètres créés avec succès !")
```

### 4. Vérifier les URLs

Dans `project/urls.py`, vérifiez que les URLs C2C sont incluses :

```python
urlpatterns = [
    # ...
    path('c2c/', include('c2c.urls', namespace='c2c')),
]
```

### 5. Créer un superutilisateur (si nécessaire)

```bash
python manage.py createsuperuser
```

### 6. Accéder à l'admin

1. Aller sur `http://localhost:8000/admin/`
2. Se connecter avec le superutilisateur
3. Vérifier que les modèles C2C sont visibles :
   - Platform Settings
   - Purchase Intents
   - Negotiations
   - C2C Orders
   - Delivery Verifications
   - Product Boosts
   - Seller Badges

## ✅ Vérification

### Tester la création d'une intention d'achat

1. Aller sur une page de produit peer-to-peer
2. Cliquer sur "Proposer une offre"
3. Vous devriez être redirigé vers `/c2c/purchase-intent/{product_id}/`
4. Cliquer sur "Créer une intention d'achat"
5. Une conversation devrait s'ouvrir dans la messagerie

### Tester l'admin

1. Aller sur `/admin/c2c/platformsettings/`
2. Modifier les commissions si nécessaire
3. Vérifier que les changements sont sauvegardés

## 🔧 Configuration

### Modifier les commissions

1. Aller dans l'admin Django
2. Ouvrir "Platform Settings"
3. Modifier les taux de commission
4. Sauvegarder

### Configurer SingPay

Les clés API SingPay doivent être configurées dans les settings Django (à ajouter) :

```python
# Dans project/settings.py
SINGPAY_API_KEY = 'your_api_key'
SINGPAY_API_SECRET = 'your_api_secret'
SINGPAY_SANDBOX = True  # Mode sandbox pour les tests
```

## 📝 Notes importantes

- Le module C2C est totalement séparé du système B2C
- Les commissions sont calculées automatiquement lors de la création d'une commande
- Le système de double code est automatiquement créé pour chaque commande
- Les badges vendeurs sont attribués automatiquement selon les performances

## 🐛 Dépannage

### Erreur : "no such table: c2c_platformsettings"

Solution : Exécutez les migrations :
```bash
python manage.py migrate c2c
```

### Erreur : "ModuleNotFoundError: No module named 'c2c'"

Solution : Vérifiez que `c2c` est dans `INSTALLED_APPS` dans `settings.py`

### Les templates ne s'affichent pas

Solution : Vérifiez que le dossier `c2c/templates/` existe et contient les fichiers HTML

## 📞 Support

Pour toute question, consultez le README.md du module C2C.



