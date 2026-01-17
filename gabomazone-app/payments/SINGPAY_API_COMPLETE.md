# Documentation complète de l'API SingPay

Cette documentation décrit toutes les fonctionnalités disponibles dans le service SingPay pour Gabomazone.

## 📚 Documentation officielle

Documentation complète de l'API SingPay : [https://client.singpay.ga/doc/reference/index.html](https://client.singpay.ga/doc/reference/index.html)

## 🔧 Utilisation du service

```python
from payments.services.singpay import singpay_service
```

## 💳 Méthodes de paiement

### 1. Paiement via interface externe (`init_payment`)

Initialise un paiement via l'interface externe SingPay. Le client est redirigé vers une page de paiement.

```python
success, response = singpay_service.init_payment(
    amount=10000.00,
    currency='XOF',
    order_id='ORDER-123',
    customer_email='client@example.com',
    customer_phone='+24101234567',
    customer_name='Jean Dupont',
    description='Paiement commande #123',
    callback_url='https://votre-domaine.com/payments/singpay/callback/',
    return_url='https://votre-domaine.com/orders/success/',
    metadata={'logo_url': 'https://...', 'disbursement': ''}
)

if success:
    payment_url = response['payment_url']
    transaction_id = response['transaction_id']
    # Rediriger le client vers payment_url
```

### 2. Paiement direct Airtel Money (`init_airtel_payment`)

Envoie un USSD Push pour le paiement via Airtel Money.

```python
success, response = singpay_service.init_airtel_payment(
    amount=10000.00,
    currency='XOF',
    order_id='ORDER-123',
    customer_phone='+24101234567',
    description='Paiement commande #123',
    callback_url='https://votre-domaine.com/payments/singpay/callback/'
)

if success:
    transaction_id = response['transaction_id']
    # Le client recevra un USSD Push sur son téléphone
```

### 3. Paiement direct Moov Money (`init_moov_payment`)

Envoie un USSD Push pour le paiement via Moov Money.

```python
success, response = singpay_service.init_moov_payment(
    amount=10000.00,
    currency='XOF',
    order_id='ORDER-123',
    customer_phone='+24101234567',
    description='Paiement commande #123',
    callback_url='https://votre-domaine.com/payments/singpay/callback/'
)
```

### 4. Paiement direct Maviance (`init_maviance_payment`)

Initialise un paiement via Maviance Mobile Money.

```python
success, response = singpay_service.init_maviance_payment(
    amount=10000.00,
    currency='XOF',
    order_id='ORDER-123',
    customer_phone='+24101234567',
    description='Paiement commande #123',
    callback_url='https://votre-domaine.com/payments/singpay/callback/'
)
```

## 🔄 Gestion des transactions

### Vérifier le statut d'une transaction (`verify_payment`)

```python
success, response = singpay_service.verify_payment('transaction_id_123')

if success:
    status = response['status']  # pending, success, failed, cancelled
    amount = response['amount']
    payment_method = response['payment_method']
```

### Annuler une transaction (`cancel_payment`)

```python
success, response = singpay_service.cancel_payment(
    transaction_id='transaction_id_123',
    reason='Client a annulé la commande'
)

if success:
    print(f"Transaction annulée: {response['message']}")
```

### Rembourser une transaction (`refund_payment`)

Remboursement total ou partiel.

```python
# Remboursement total
success, response = singpay_service.refund_payment(
    transaction_id='transaction_id_123',
    reason='Produit défectueux'
)

# Remboursement partiel
success, response = singpay_service.refund_payment(
    transaction_id='transaction_id_123',
    amount=5000.00,  # Rembourser seulement 5000 XOF
    reason='Remboursement partiel'
)

if success:
    refund_id = response['refund_id']
    print(f"Remboursement initié: {refund_id}")
```

## 💸 Virements (Disbursements)

### Effectuer un virement (`init_disbursement`)

Virer de l'argent vers un portefeuille mobile money.

```python
success, response = singpay_service.init_disbursement(
    amount=50000.00,
    currency='XOF',
    recipient_phone='+24101234567',
    recipient_name='Jean Dupont',
    description='Paiement commission vendeur',
    reference='DISB-COMM-123',
    callback_url='https://votre-domaine.com/payments/singpay/callback/'
)

if success:
    disbursement_id = response['disbursement_id']
    print(f"Virement initié: {disbursement_id}")
```

## 💰 Commissions

### Payer une commission (`pay_commission`)

Utilise le système de virement pour payer les commissions.

```python
# Payer une commission à un vendeur
success, response = singpay_service.pay_commission(
    amount=5000.00,
    recipient_phone='+24101234567',
    recipient_name='Vendeur ABC',
    order_id='ORDER-123',
    commission_type='seller',
    description='Commission vendeur commande #123',
    callback_url='https://votre-domaine.com/payments/singpay/callback/'
)

# Payer une commission plateforme
success, response = singpay_service.pay_commission(
    amount=1000.00,
    recipient_phone='+24109876543',
    recipient_name='Plateforme',
    order_id='ORDER-123',
    commission_type='platform'
)
```

## 📊 Consultation et historique

### Récupérer l'historique des transactions (`get_transaction_history`)

```python
success, response = singpay_service.get_transaction_history(
    start_date='2024-01-01',
    end_date='2024-01-31',
    status='success',  # Filtrer par statut (optionnel)
    limit=50,
    offset=0
)

if success:
    transactions = response['transactions']
    total = response['total']
    for transaction in transactions:
        print(f"Transaction: {transaction['transaction_id']} - {transaction['amount']} {transaction['currency']}")
```

### Consulter le solde du portefeuille (`get_balance`)

```python
success, response = singpay_service.get_balance()

if success:
    balance = response['balance']
    available_balance = response['available_balance']
    currency = response['currency']
    print(f"Solde disponible: {available_balance} {currency}")
```

## 🔐 Webhooks

### Vérifier la signature d'un webhook (`verify_webhook_signature`)

```python
is_valid = singpay_service.verify_webhook_signature(
    payload=request.body.decode('utf-8'),
    signature=request.headers.get('X-Signature', ''),
    timestamp=request.headers.get('X-Timestamp', '')
)

if is_valid:
    # Traiter le webhook
    pass
```

## 📝 Exemples d'utilisation dans les vues Django

### Exemple : Annuler une transaction depuis une vue

```python
from payments.services.singpay import singpay_service
from payments.models import SingPayTransaction

def cancel_transaction_view(request, transaction_id):
    try:
        transaction = SingPayTransaction.objects.get(transaction_id=transaction_id)
        
        if not transaction.can_be_cancelled():
            messages.error(request, "Cette transaction ne peut pas être annulée")
            return redirect('payments:transactions')
        
        success, response = singpay_service.cancel_payment(
            transaction_id=transaction.transaction_id,
            reason='Annulé par l\'administrateur'
        )
        
        if success:
            transaction.status = SingPayTransaction.CANCELLED
            transaction.save()
            messages.success(request, "Transaction annulée avec succès")
        else:
            messages.error(request, f"Erreur: {response.get('error', 'Erreur inconnue')}")
            
    except SingPayTransaction.DoesNotExist:
        messages.error(request, "Transaction non trouvée")
    
    return redirect('payments:transactions')
```

### Exemple : Rembourser une transaction

```python
def refund_transaction_view(request, transaction_id):
    try:
        transaction = SingPayTransaction.objects.get(transaction_id=transaction_id)
        
        if not transaction.can_be_refunded():
            messages.error(request, "Cette transaction ne peut pas être remboursée")
            return redirect('payments:transactions')
        
        # Remboursement total
        success, response = singpay_service.refund_payment(
            transaction_id=transaction.transaction_id,
            reason='Remboursement demandé par le client'
        )
        
        if success:
            transaction.status = SingPayTransaction.REFUNDED
            transaction.save()
            messages.success(request, f"Remboursement initié: {response.get('refund_id')}")
        else:
            messages.error(request, f"Erreur: {response.get('error', 'Erreur inconnue')}")
            
    except SingPayTransaction.DoesNotExist:
        messages.error(request, "Transaction non trouvée")
    
    return redirect('payments:transactions')
```

### Exemple : Payer une commission après une vente

```python
def pay_seller_commission(order):
    """Payer la commission au vendeur après une vente réussie"""
    from accounts.models import Profile
    
    # Calculer la commission (exemple: 5% du montant)
    commission_amount = float(order.amount) * 0.05
    
    # Récupérer les informations du vendeur
    seller = order.orderdetails_set.first().peer_product.seller
    seller_profile = Profile.objects.get(user=seller)
    
    if seller_profile.phone:
        success, response = singpay_service.pay_commission(
            amount=commission_amount,
            recipient_phone=seller_profile.phone,
            recipient_name=f"{seller.first_name} {seller.last_name}",
            order_id=f"ORDER-{order.id}",
            commission_type='seller',
            description=f"Commission vendeur pour commande #{order.id}"
        )
        
        if success:
            logger.info(f"Commission payée au vendeur {seller.id}: {response.get('disbursement_id')}")
            return True
        else:
            logger.error(f"Erreur paiement commission: {response.get('error')}")
            return False
    
    return False
```

## ⚠️ Gestion des erreurs

Toutes les méthodes retournent un tuple `(success, response)` :

- `success` : `True` si l'opération a réussi, `False` sinon
- `response` : Dictionnaire contenant les données de réponse ou les détails de l'erreur

```python
success, response = singpay_service.init_payment(...)

if not success:
    error = response.get('error', 'Erreur inconnue')
    api_error = response.get('api_error', {})
    
    if api_error:
        error_message = api_error.get('message', error)
    else:
        error_message = error
    
    logger.error(f"Erreur SingPay: {error_message}")
    # Gérer l'erreur
```

## 🧪 Mode Bypass (Test)

En mode bypass, toutes les opérations sont simulées. Pour activer/désactiver :

1. Dans le fichier `.env` :
   ```bash
   SINGPAY_BYPASS_API=True   # Activer le mode test
   # ou ne pas définir la variable pour auto-détection
   ```

2. Le système désactive automatiquement le bypass si les credentials sont présents.

## 📞 Support

Pour toute question ou problème :
- Documentation officielle : [https://client.singpay.ga/doc/reference/index.html](https://client.singpay.ga/doc/reference/index.html)
- Support SingPay : Contactez le support via votre espace client



