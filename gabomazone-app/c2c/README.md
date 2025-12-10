# Module C2C - Vente entre particuliers

## 📋 Vue d'ensemble

Le module C2C (Consumer-to-Consumer) est un système complet de vente entre particuliers pour Gabomazone, totalement séparé du système B2C (Business-to-Consumer) pour une meilleure maintenance.

## 🎯 Fonctionnalités principales

### 1. Négociation obligatoire avant paiement
- ✅ Création d'intention d'achat lors du clic sur "Voir" ou "Négocier"
- ✅ Messagerie privée sécurisée par annonce
- ✅ Système de propositions de prix
- ✅ Accord final sur le prix avant paiement

### 2. Commissions configurables
- ✅ Commission acheteur C2C (5.9% par défaut)
- ✅ Commission vendeur C2C (9.9% par défaut)
- ✅ Commission acheteur B2C (0% par défaut)
- ✅ Commission vendeur B2C (10% par défaut)
- ✅ Configuration depuis l'admin Django

### 3. Paiement SingPay intégré
- ✅ Initialisation de paiement pour commandes C2C
- ✅ Gestion des webhooks
- ✅ Mise à jour automatique du statut
- ✅ Ventilation automatique des commissions

### 4. Sécurisation par double code
- ✅ Code vendeur (V-CODE) : confirme la remise de l'article
- ✅ Code acheteur (A-CODE) : confirme la réception et satisfaction
- ✅ Finalisation automatique lorsque les deux codes sont validés
- ✅ Système de litige vers l'admin

### 5. Options payantes
- ✅ Boost d'annonce (24h, 72h, 7 jours)
- ✅ Badges vendeur automatiques ou manuels
- ✅ Mise en avant dans les résultats de recherche

### 6. Interface Admin complète
- ✅ Gestion des commissions C2C & B2C
- ✅ Gestion des badges
- ✅ Gestion des boosts
- ✅ Liste des transactions
- ✅ Outil de résolution des litiges
- ✅ Statistiques C2C

## 📁 Structure du module

```
c2c/
├── __init__.py
├── apps.py              # Configuration de l'application
├── models.py            # Modèles de données
├── services.py          # Services métier (calculs, SingPay, etc.)
├── signals.py           # Signaux Django
├── admin.py             # Interface d'administration
├── views.py             # Vues Django
├── urls.py              # Routes URL
├── migrations/          # Migrations de base de données
└── templates/           # Templates HTML (à créer)
    └── c2c/
```

## 🗄️ Modèles de données

### PlatformSettings
Paramètres configurables de la plateforme (commissions C2C et B2C).

### PurchaseIntent
Intention d'achat créée lorsqu'un acheteur souhaite négocier.

### Negotiation
Proposition de prix dans le cadre d'une négociation.

### C2COrder
Commande C2C créée après accord sur le prix final.

### DeliveryVerification
Système de double code pour sécuriser la transaction.

### ProductBoost
Boost payant pour mettre en avant un article.

### SellerBadge
Badge attribué à un vendeur selon ses performances.

## 🔧 Installation

### 1. Ajouter l'application aux settings

L'application est déjà ajoutée dans `INSTALLED_APPS` :
```python
INSTALLED_APPS = [
    # ...
    'c2c',
]
```

### 2. Créer les migrations

```bash
python manage.py makemigrations c2c
python manage.py migrate c2c
```

### 3. Créer les paramètres par défaut

```bash
python manage.py shell
```

```python
from c2c.models import PlatformSettings
PlatformSettings.objects.create()
```

### 4. Configurer les URLs

Les URLs sont déjà configurées dans `project/urls.py` :
```python
path('c2c/', include('c2c.urls', namespace='c2c')),
```

## 🔌 Intégration SingPay

### Configuration

1. Ajouter les clés API SingPay dans les settings :
```python
SINGPAY_API_KEY = 'your_api_key'
SINGPAY_API_SECRET = 'your_api_secret'
SINGPAY_SANDBOX = True  # Mode sandbox pour les tests
```

2. Configurer les URLs de callback :
- Callback URL : `/payments/singpay/callback/`
- Return URL : `/c2c/order/{order_id}/`

### Utilisation

Le service `SingPayService` gère automatiquement :
- L'initialisation des paiements
- La gestion des webhooks
- La mise à jour des statuts
- La ventilation des commissions

## 💰 Calcul des commissions

Les commissions sont calculées automatiquement lors de la création d'une commande C2C :

```python
from c2c.services import CommissionCalculator

calculator = CommissionCalculator()
commissions = calculator.calculate_c2c_commissions(price=100000)

# Résultat :
# {
#     'buyer_commission': 5900,      # 5.9% de 100000
#     'seller_commission': 9900,      # 9.9% de 100000
#     'platform_commission': 15800,   # Total commission plateforme
#     'seller_net': 90100,            # Net versé au vendeur
#     'buyer_total': 105900,           # Total à payer par l'acheteur
#     'original_price': 100000
# }
```

## 🔐 Système de double code

### Workflow

1. **Création de la commande** : Deux codes sont générés automatiquement
   - Code vendeur (V-CODE) : 6 chiffres
   - Code acheteur (A-CODE) : 6 chiffres

2. **Vérification code vendeur** :
   - Le vendeur saisit le code acheteur (A-CODE)
   - Confirme qu'il a remis l'article

3. **Vérification code acheteur** :
   - L'acheteur saisit le code vendeur (V-CODE)
   - Confirme qu'il a reçu l'article et qu'il est satisfait

4. **Finalisation** :
   - Lorsque les deux codes sont validés, la transaction est complétée
   - Les statistiques du vendeur sont mises à jour

## 🚀 Utilisation

### Créer une intention d'achat

```python
from c2c.services import PurchaseIntentService
from accounts.models import PeerToPeerProduct

product = PeerToPeerProduct.objects.get(id=1)
intent = PurchaseIntentService.create_purchase_intent(
    product=product,
    buyer=request.user,
    initial_price=product.PRDPrice
)
```

### Créer une négociation

```python
negotiation = PurchaseIntentService.create_negotiation(
    intent=intent,
    proposer=request.user,
    proposed_price=90000,
    message="Je propose 90000 FCFA"
)
```

### Accepter un prix final

```python
c2c_order = PurchaseIntentService.accept_final_price(
    intent=intent,
    final_price=95000
)
```

### Vérifier les codes

```python
from c2c.services import DeliveryVerificationService

# Vérifier code vendeur
DeliveryVerificationService.verify_seller_code(c2c_order, "123456")

# Vérifier code acheteur
DeliveryVerificationService.verify_buyer_code(c2c_order, "654321")
```

## 📊 Badges vendeurs

Les badges sont attribués automatiquement selon le nombre de transactions réussies :

- **Nouveau Vendeur** : < 3 transactions
- **Bon Vendeur** : 3-10 transactions
- **Vendeur Sérieux** : 10-50 transactions
- **Meilleur Vendeur** : 50+ transactions

## 🔥 Boosts de produits

Les prix des boosts sont configurables dans `BoostService` :

- **24h** : 5000 FCFA
- **72h** : 12000 FCFA
- **7 jours** : 25000 FCFA

## 🛠️ Développement

### Tests

```bash
python manage.py test c2c
```

### Linting

```bash
flake8 c2c/
pylint c2c/
```

## 📝 Notes importantes

1. **Séparation B2C/C2C** : Le module C2C est totalement indépendant du système B2C
2. **Pas de portefeuille interne** : L'argent n'est jamais stocké dans des portefeuilles internes
3. **Ventilation directe** : SingPay ventile directement les commissions
4. **Mobile-first** : Tous les templates doivent être responsives
5. **HTMX** : Utiliser HTMX pour toutes les interactions utilisateur

## 🔗 Liens utiles

- Documentation SingPay : [À ajouter]
- Documentation Django : https://docs.djangoproject.com/
- Documentation HTMX : https://htmx.org/

## 📞 Support

Pour toute question ou problème, contacter l'équipe de développement.

