# Configuration SingPay pour Gabomazone

Ce document explique comment configurer et utiliser l'intégration SingPay dans Gabomazone.

## 📚 Documentation officielle

La documentation complète de l'API SingPay est disponible à :
**https://client.singpay.ga/doc/reference/index.html**

## ⚙️ Configuration

### 1. Obtenir les credentials SingPay

1. Créez un compte sur [SingPay](https://client.singpay.ga)
2. Connectez-vous à votre espace client
3. Récupérez vos identifiants :
   - **API Key** : Clé d'API publique
   - **API Secret** : Secret d'API (à garder confidentiel)
   - **Merchant ID** : Identifiant de votre compte marchand

### 2. Configuration dans Django Settings

Ajoutez les paramètres suivants dans `project/settings.py` :

```python
## SingPay account ##
SINGPAY_API_KEY = 'votre_api_key'  # Remplacez par votre clé API
SINGPAY_API_SECRET = 'votre_api_secret'  # Remplacez par votre secret API
SINGPAY_MERCHANT_ID = 'votre_merchant_id'  # Remplacez par votre ID marchand
SINGPAY_ENVIRONMENT = 'sandbox'  # 'sandbox' pour les tests, 'production' pour la production
SINGPAY_BYPASS_API = False  # Mettre à False en production pour utiliser l'API réelle
```

### 3. Configuration des URLs de callback

Les URLs de callback doivent être accessibles publiquement. Configurez-les dans votre compte SingPay :

- **Callback URL** : `https://votre-domaine.com/payments/singpay/callback/`
- **Return URL** : `https://votre-domaine.com/orders/order/success/`

## 🔄 Flux de paiement

### 1. Initialisation du paiement

Lorsqu'un client choisit SingPay comme méthode de paiement :

1. Le client remplit le formulaire de facturation
2. Le client sélectionne "Mobile Money via SingPay"
3. Le client clique sur "Passer la commande"
4. Le système initialise le paiement via `SingPayService.init_payment()`
5. Le client est redirigé vers l'URL de paiement SingPay

### 2. Traitement du paiement

1. Le client effectue le paiement sur la plateforme SingPay
2. SingPay envoie une notification webhook à `/payments/singpay/callback/`
3. Le système vérifie la signature et met à jour le statut de la transaction
4. La commande est automatiquement confirmée si le paiement réussit

### 3. Retour après paiement

Après le paiement, le client est redirigé vers :
- **Succès** : `/orders/order/success/`
- **Échec** : Page de paiement avec message d'erreur

## 🧪 Mode Test / Sandbox

Pour tester l'intégration sans utiliser l'API réelle :

1. Activez le mode bypass dans `settings.py` :
   ```python
   SINGPAY_BYPASS_API = True
   ```

2. Les paiements seront simulés et redirigés vers `/payments/singpay/test-payment/{transaction_id}/`

3. Vous pouvez simuler un paiement réussi depuis cette page de test

## 📝 Structure des données

### Initialisation d'un paiement

```python
from payments.services.singpay import singpay_service

success, response = singpay_service.init_payment(
    amount=10000.00,  # Montant en FCFA
    currency='XOF',
    order_id='ORDER-123',
    customer_email='client@example.com',
    customer_phone='+24101234567',  # Format international
    customer_name='Jean Dupont',
    description='Paiement commande #123',
    callback_url='https://votre-domaine.com/payments/singpay/callback/',
    return_url='https://votre-domaine.com/orders/order/success/',
    metadata={'order_id': '123', 'user_id': '456'}
)
```

### Réponse de l'API

```python
{
    'payment_url': 'https://client.singpay.ga/pay/...',
    'transaction_id': 'TXN-123456789',
    'reference': 'REF-ORDER-123',
    'expires_at': '2024-01-01T12:00:00Z'
}
```

## 🔐 Sécurité

### Vérification des signatures

Tous les webhooks SingPay sont signés avec HMAC-SHA256. Le système vérifie automatiquement la signature avant de traiter la notification.

### Headers requis

Les requêtes vers l'API SingPay incluent automatiquement :
- `X-API-Key` : Votre clé API
- `X-Merchant-ID` : Votre ID marchand
- `X-Timestamp` : Timestamp de la requête
- `X-Signature` : Signature HMAC-SHA256

## 🐛 Dépannage

### Le paiement ne s'initialise pas

1. Vérifiez que les credentials sont corrects dans `settings.py`
2. Vérifiez les logs Django pour les erreurs
3. Assurez-vous que `SINGPAY_BYPASS_API` est à `False` en production

### Les webhooks ne sont pas reçus

1. Vérifiez que l'URL de callback est accessible publiquement
2. Vérifiez la configuration dans votre compte SingPay
3. Consultez les logs dans `SingPayWebhookLog` dans l'admin Django

### Erreur de signature

1. Vérifiez que `SINGPAY_API_SECRET` est correct
2. Assurez-vous que le timestamp est synchronisé
3. Vérifiez que la structure des données correspond à la documentation

## 📞 Support

Pour toute question ou problème :
- Documentation : https://client.singpay.ga/doc/reference/index.html
- Support SingPay : Contactez le support via votre espace client

## 🔄 Migration vers la production

Avant de passer en production :

1. ✅ Configurez les credentials de production
2. ✅ Mettez `SINGPAY_ENVIRONMENT = 'production'`
3. ✅ Mettez `SINGPAY_BYPASS_API = False`
4. ✅ Testez avec un petit montant
5. ✅ Vérifiez que les webhooks fonctionnent
6. ✅ Configurez les URLs de callback en production



